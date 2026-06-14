import cv2
import depthai as dai
import os  # <-- NEW: Imports the tool to check your Windows files

pipeline = dai.Pipeline()

cam_rgb = pipeline.create(dai.node.ColorCamera)
cam_rgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_12_MP)
cam_rgb.setIspScale(1, 3) 
cam_rgb.setInterleaved(False)
cam_rgb.setColorOrder(dai.ColorCameraProperties.ColorOrder.RGB)

# Control node for lens focus
controlIn = pipeline.create(dai.node.XLinkIn)
controlIn.setStreamName('control')
controlIn.out.link(cam_rgb.inputControl)

xout_rgb = pipeline.create(dai.node.XLinkOut)
xout_rgb.setStreamName("rgb")
cam_rgb.video.link(xout_rgb.input)

with dai.Device(pipeline) as device:
    q_rgb = device.getOutputQueue(name="rgb", maxSize=4, blocking=False)
    q_control = device.getInputQueue('control') 
    
    lens_position = 130 
    
    # --- NEW SMART FILE CHECKER ---
    photo_count = 0
    # This loop checks your folder. If dataset_img_0.jpg exists, it checks 1. 
    # If 1 exists, it checks 2. It keeps going until it finds an empty slot!
    while os.path.exists(f"dataset_img_{photo_count}.jpg"):
        photo_count += 1
    
    print("Camera Ready! MAX FOV + ISP Downscaling active.")
    print(f"-> Resuming from image number: {photo_count} <-") # Tells you where it's starting!
    print("Press ',' to focus CLOSER (Lower number).")
    print("Press '.' to focus FURTHER (Higher number).")
    print("Press 's' to SAVE photo. Press 'q' to QUIT.")
    # ------------------------------

    while True:
        in_rgb = q_rgb.get()
        frame = in_rgb.getCvFrame()
        
        display_frame = cv2.resize(frame, (960, 720))
        cv2.putText(display_frame, f"Focus: {lens_position}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow("Data Collection", display_frame)
        
        key = cv2.waitKey(1) & 0xFF

        if key == ord('s'):
            filename = f"dataset_img_{photo_count}.jpg"
            cv2.imwrite(filename, frame) 
            print(f"Saved: {filename} at focus {lens_position}")
            # Increases the count for the next time you press 's'
            photo_count += 1
            
        elif key == ord(','): 
            lens_position -= 5
            if lens_position < 0: lens_position = 0
            ctrl = dai.CameraControl()
            ctrl.setManualFocus(lens_position)
            q_control.send(ctrl)
            
        elif key == ord('.'): 
            lens_position += 5
            if lens_position > 255: lens_position = 255
            ctrl = dai.CameraControl()
            ctrl.setManualFocus(lens_position)
            q_control.send(ctrl)

        elif key == ord('q'):
            break

cv2.destroyAllWindows()