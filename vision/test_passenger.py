from roboflowoak import RoboflowOak
import cv2

# 1. Initialize the AI Model
# Paste your specific Roboflow details here!
rf = RoboflowOak(
    model="duck-lqboz", 
    confidence=0.1,             # Only show detections if the AI is 60%+ sure
    overlap=0.5,
    version="1", 
    api_key="i1kDNRD6KYGaul4po6wR", 
    rgb=True, 
    depth=False                 # Set to False because we don't need depth for the passenger seat
)

print("Downloading model and pushing to OAK-D-Lite...")
print("This may take 10-20 seconds the very first time you run it.")

while True:
    # 2. Run the camera frame through the AI chip
    result, frame, raw_frame, depth = rf.detect()
    predictions = result["predictions"]

    # 3. Draw bounding boxes for every duck found
    for p in predictions:
        # Roboflow returns the center X/Y coordinates and the width/height
        x_center = p.json()['x']
        y_center = p.json()['y']
        width = p.json()['width']
        height = p.json()['height']
        class_name = p.json()['class']
        confidence = p.json()['confidence']
        
        # Calculate the top-left and bottom-right corners for the rectangle
        x_min = int(x_center - (width / 2))
        y_min = int(y_center - (height / 2))
        x_max = int(x_center + (width / 2))
        y_max = int(y_center + (height / 2))

        # Draw the box (Green color, 2 pixels thick)
        cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
        
        # Create the text label (e.g., "duck 0.85")
        label = f"{class_name} {confidence:.2f}"
        cv2.putText(frame, label, (x_min, y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    # 4. Display the video feed on your screen
    cv2.imshow("Passenger Verification Test", frame)

    # Press 'q' to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()