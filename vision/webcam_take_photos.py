import cv2

def get_external_camera():
    print("Scanning USB ports for cameras...")
    available_cameras = []
    
    # Scan the first 3 ports (0, 1, 2)
    for i in range(3):
        # We use CAP_MSMF instead of DSHOW for modern Windows compatibility
        cap = cv2.VideoCapture(i, cv2.CAP_MSMF)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                available_cameras.append(i)
        cap.release()
        
    if not available_cameras:
        return None
        
    print(f"Cameras found at index: {available_cameras}")
    # The built-in webcam is usually 0. 
    # By picking the highest number found, it usually grabs the external USB camera.
    best_index = available_cameras[-1] 
    return best_index

# --- Main Script ---
target_index = get_external_camera()

if target_index is None:
    print("ERROR: No cameras found! Make sure the Windows Camera app and Zoom are CLOSED.")
else:
    print(f"Connecting to Camera Index {target_index}...")
    cap = cv2.VideoCapture(target_index, cv2.CAP_MSMF)
    
    # Set resolution to 720p widescreen
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    photo_count = 0
    print("\n--- Webcam Ready! ---")
    print("Press 's' to save a photo. Press 'q' to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Stream interrupted.")
            break

        cv2.imshow("Webcam Dataset Collection", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord('s'):
            filename = f"webcam_img_{photo_count}.jpg"
            cv2.imwrite(filename, frame)
            print(f"Saved: {filename}")
            photo_count += 1
            
        elif key == ord('q'):
            print("Finished collecting data!")
            break

    cap.release()
    cv2.destroyAllWindows()