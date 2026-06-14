# passenger_cam.py
import cv2
import depthai as dai
import json
import requests
import threading
import time
from flask import Flask, Response

# UPDATE THESE PATHS to your specific files!
JSON_PATH = r"vision\models\Ducktrained\best.json"
BLOB_PATH = r"vision\models\Ducktrained\best_openvino_2022.1_6shave.blob"
FLASK_APP_URL = "http://127.0.0.1:5000/camera_feed_update"

# Global variable to hold the latest image frame for the website
latest_frame = None

# Set up the tiny video server
video_app = Flask(__name__)

def generate_video_stream():
    global latest_frame
    while True:
        if latest_frame is not None:
            # Yield the frame in MJPEG format for the HTML <img> tag
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + latest_frame + b'\r\n')
        time.sleep(0.05)

@video_app.route('/video_feed')
def video_feed():
    return Response(generate_video_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')

def run_camera_ai():
    global latest_frame
    
    with open(JSON_PATH, 'r') as file:
        config = json.load(file)
    metadata = config.get("nn_config", {}).get("NN_specific_metadata", {})

    pipeline = dai.Pipeline()
    
    cam_rgb = pipeline.create(dai.node.ColorCamera)
    cam_rgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_12_MP)
    cam_rgb.setIspScale(1, 3) 
    cam_rgb.setInterleaved(False)
    cam_rgb.setColorOrder(dai.ColorCameraProperties.ColorOrder.BGR)
    cam_rgb.setFps(20)

    manip = pipeline.create(dai.node.ImageManip)
    manip.initialConfig.setResize(640, 640)
    manip.initialConfig.setFrameType(dai.ImgFrame.Type.BGR888p)
    manip.setMaxOutputFrameSize(1228800)
    cam_rgb.isp.link(manip.inputImage)

    nn = pipeline.create(dai.node.YoloDetectionNetwork)
    nn.setBlobPath(BLOB_PATH)
    nn.setConfidenceThreshold(0.4)
    nn.setNumClasses(metadata.get("classes", 1))
    nn.setCoordinateSize(metadata.get("coordinates", 4))
    nn.setAnchors(metadata.get("anchors", []))
    nn.setAnchorMasks(metadata.get("anchor_masks", {}))
    nn.setIouThreshold(metadata.get("iou_threshold", 0.5))
    manip.out.link(nn.input)

    xout_rgb = pipeline.create(dai.node.XLinkOut)
    xout_rgb.setStreamName("rgb")
    cam_rgb.isp.link(xout_rgb.input)

    xout_nn = pipeline.create(dai.node.XLinkOut)
    xout_nn.setStreamName("nn")
    nn.out.link(xout_nn.input)

    with dai.Device(pipeline) as device:
        q_rgb = device.getOutputQueue(name="rgb", maxSize=4, blocking=False)
        q_nn = device.getOutputQueue(name="nn", maxSize=4, blocking=False)
        
        print("📷 Camera Node Active! Streaming video to port 5001...")

        while True:
            in_rgb = q_rgb.get()
            in_nn = q_nn.get()
            
            frame = in_rgb.getCvFrame()
            detections = in_nn.detections
            duck_present = len(detections) > 0
            
            # Send the True/False state to the Main app.py server
            try:
                requests.post(FLASK_APP_URL, json={"duck_detected": duck_present})
            except:
                pass 
                
            # Draw the bounding box for the website video feed
            for det in detections:
                x1, y1 = int(det.xmin * frame.shape[1]), int(det.ymin * frame.shape[0])
                x2, y2 = int(det.xmax * frame.shape[1]), int(det.ymax * frame.shape[0])
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, "PASSENGER", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

            # Compress the image to JPEG so the website can read it fast
            small_frame = cv2.resize(frame, (640, 360))
            _, buffer = cv2.imencode('.jpg', small_frame)
            latest_frame = buffer.tobytes()

# Start the Camera AI loop in the background
threading.Thread(target=run_camera_ai, daemon=True).start()

# Start the video server on port 5001
if __name__ == '__main__':
    video_app.run(host='0.0.0.0', port=5001, debug=False, use_reloader=False)