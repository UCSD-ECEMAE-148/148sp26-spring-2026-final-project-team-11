import cv2
import depthai as dai
import json

JSON_PATH = r"vision\models\SignTrained\best.json"
BLOB_PATH = r"vision\models\SignTrained\best_openvino_2022.1_6shave.blob"

with open(JSON_PATH, 'r') as file:
    config = json.load(file)
nn_config = config.get("nn_config", {})
metadata = nn_config.get("NN_specific_metadata", {})

pipeline = dai.Pipeline()

# 1. Switch to 1080p (Natively resolves the multiple-of-16 rule!)
cam_rgb = pipeline.create(dai.node.ColorCamera)
cam_rgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
cam_rgb.setInterleaved(False)
cam_rgb.setColorOrder(dai.ColorCameraProperties.ColorOrder.BGR)
cam_rgb.setFps(20) # Caps frame rate to keep processing cool and lag-free

# 2. Stereo Cameras Setup
monoLeft = pipeline.create(dai.node.MonoCamera)
monoRight = pipeline.create(dai.node.MonoCamera)
stereo = pipeline.create(dai.node.StereoDepth)

monoLeft.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
monoLeft.setCamera("left")
monoRight.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
monoRight.setCamera("right")

# Native 1:1 alignment to the 1080p frame (No custom output size needed!)
stereo.setDefaultProfilePreset(dai.node.StereoDepth.PresetMode.HIGH_DENSITY)
stereo.setDepthAlign(dai.CameraBoardSocket.CAM_A)

monoLeft.out.link(stereo.left)
monoRight.out.link(stereo.right)

# 3. Image Manipulator (Squishing to 640x640)
manip = pipeline.create(dai.node.ImageManip)
manip.initialConfig.setResize(640, 640)
manip.initialConfig.setFrameType(dai.ImgFrame.Type.BGR888p)
manip.setMaxOutputFrameSize(1228800) 
cam_rgb.isp.link(manip.inputImage)

# 4. Spatial Neural Network
spatial_nn = pipeline.create(dai.node.YoloSpatialDetectionNetwork)
spatial_nn.setBlobPath(BLOB_PATH)
spatial_nn.setConfidenceThreshold(0.4) 
spatial_nn.setNumClasses(metadata.get("classes", 1))
spatial_nn.setCoordinateSize(metadata.get("coordinates", 4))
spatial_nn.setAnchors(metadata.get("anchors", []))
spatial_nn.setAnchorMasks(metadata.get("anchor_masks", {}))
spatial_nn.setIouThreshold(metadata.get("iou_threshold", 0.5))

manip.out.link(spatial_nn.input)
stereo.depth.link(spatial_nn.inputDepth)

# Output Links
xout_rgb = pipeline.create(dai.node.XLinkOut)
xout_rgb.setStreamName("rgb")
cam_rgb.isp.link(xout_rgb.input)

xout_nn = pipeline.create(dai.node.XLinkOut)
xout_nn.setStreamName("nn")
spatial_nn.out.link(xout_nn.input)

# Run System
with dai.Device(pipeline) as device:
    q_rgb = device.getOutputQueue(name="rgb", maxSize=4, blocking=False)
    q_nn = device.getOutputQueue(name="nn", maxSize=4, blocking=False)

    print("Optimized 1080p Spatial Model Running!")

    while True:
        in_rgb = q_rgb.get()
        in_nn = q_nn.get()
        
        frame = in_rgb.getCvFrame()
        detections = in_nn.detections

        for detection in detections:
            x1 = int(detection.xmin * frame.shape[1])
            y1 = int(detection.ymin * frame.shape[0])
            x2 = int(detection.xmax * frame.shape[1])
            y2 = int(detection.ymax * frame.shape[0])

            # Read depth value smoothly
            distance_mm = int(detection.spatialCoordinates.z)
            distance_meters = distance_mm / 1000.0

            # Ignore 0mm error/glitch values completely
            if distance_meters > 0.1:
                
                # --- DYNAMIC COLOR LOGIC ---
                # Default to Red for tracking from a distance
                box_color = (0, 0, 255) 
                label_text = f"Sign: {distance_meters:.2f}m"

                # If within 0.5m, snap to Green!
                if distance_meters < 0.5:
                    box_color = (0, 255, 0) 
                    label_text = f"AT STATION: {distance_meters:.2f}m"
                    print(f"🛑 TRIGGER STOP: Sign detected at {distance_meters:.2f}m!")

                # Draw the box and text using our dynamic variables
                cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)
                cv2.putText(frame, label_text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, box_color, 2)

        display_frame = cv2.resize(frame, (960, 540))
        cv2.imshow("Spatial AI Distance Test", display_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cv2.destroyAllWindows()