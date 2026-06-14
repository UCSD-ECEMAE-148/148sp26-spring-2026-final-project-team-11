import cv2
import depthai as dai
import json
import numpy as np

# 1. Update these to match the files you just downloaded from Roboflow!
# -------------------------------------------------------------------
JSON_PATH = r"vision\models\Ducktrained\best.json"
BLOB_PATH = r"vision\models\Ducktrained\best_openvino_2022.1_6shave.blob"
# -------------------------------------------------------------------

# 2. Extract the specific YOLO math from your Roboflow JSON file
with open(JSON_PATH, 'r') as file:
    config = json.load(file)
nn_config = config.get("nn_config", {})
metadata = nn_config.get("NN_specific_metadata", {})

pipeline = dai.Pipeline()

# 3. Camera Setup (Keeping the massive FOV and ISP scaling!)
cam_rgb = pipeline.create(dai.node.ColorCamera)
cam_rgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_12_MP)
cam_rgb.setIspScale(1, 3) 
cam_rgb.setInterleaved(False)
cam_rgb.setColorOrder(dai.ColorCameraProperties.ColorOrder.BGR) # YOLO requires BGR color

# 4. Neural Network Setup
# We use an ImageManip node to perfectly squish our widescreen 1352x1013 view 
# into the 640x640 square the AI expects, completely preventing the "Zoom" crop!
manip = pipeline.create(dai.node.ImageManip)
manip.initialConfig.setResize(640, 640)
manip.initialConfig.setFrameType(dai.ImgFrame.Type.BGR888p)
cam_rgb.isp.link(manip.inputImage)

manip.setMaxOutputFrameSize(1228800)

# Load the local .blob file into the camera's VPU
detection_nn = pipeline.create(dai.node.YoloDetectionNetwork)
detection_nn.setBlobPath(BLOB_PATH)
detection_nn.setConfidenceThreshold(0.4) # Show detections 40% and above
detection_nn.setNumClasses(metadata.get("classes", 1))
detection_nn.setCoordinateSize(metadata.get("coordinates", 4))
detection_nn.setAnchors(metadata.get("anchors", []))
detection_nn.setAnchorMasks(metadata.get("anchor_masks", {}))
detection_nn.setIouThreshold(metadata.get("iou_threshold", 0.5))

manip.out.link(detection_nn.input)

# Control node for lens focus
controlIn = pipeline.create(dai.node.XLinkIn)
controlIn.setStreamName('control')
controlIn.out.link(cam_rgb.inputControl)

# Output links
xout_rgb = pipeline.create(dai.node.XLinkOut)
xout_rgb.setStreamName("rgb")
cam_rgb.isp.link(xout_rgb.input)

xout_nn = pipeline.create(dai.node.XLinkOut)
xout_nn.setStreamName("nn")
detection_nn.out.link(xout_nn.input)

# 5. Run the System
with dai.Device(pipeline) as device:
    q_rgb = device.getOutputQueue(name="rgb", maxSize=4, blocking=False)
    q_nn = device.getOutputQueue(name="nn", maxSize=4, blocking=False)
    q_control = device.getInputQueue('control') 

    # SET THIS TO THE NUMBER YOU FOUND WORKED BEST FOR YOUR DUCK!
    lens_position = 130 
    
    # Send the initial manual focus command to the camera
    ctrl = dai.CameraControl()
    ctrl.setManualFocus(lens_position)
    device.getInputQueue('control').send(ctrl)

    print("Native YOLO Model Running!")
    print("Press 'q' to quit.")

    while True:
        in_rgb = q_rgb.get()
        in_nn = q_nn.get()
        
        frame = in_rgb.getCvFrame()
        detections = in_nn.detections

        # Draw the bounding boxes natively
        for detection in detections:
            # Roboflow math returns values between 0 and 1, so we multiply by the frame's width/height
            x1 = int(detection.xmin * frame.shape[1])
            y1 = int(detection.ymin * frame.shape[0])
            x2 = int(detection.xmax * frame.shape[1])
            y2 = int(detection.ymax * frame.shape[0])

            # Draw the Green Box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f"Passenger {detection.confidence*100:.0f}%", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # Show the video feed (resized just so it fits on your laptop monitor)
        display_frame = cv2.resize(frame, (960, 720))
        cv2.imshow("Native OAK-D Inference", display_frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

cv2.destroyAllWindows()