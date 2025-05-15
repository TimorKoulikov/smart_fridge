import cv2
import os
from datetime import datetime

def capture_frame(url="http://172.20.10.2:81/stream"):
    try:
        print(f"Attempting to capture frame from {url}")
        
        # Open the video stream using cv2
        cap = cv2.VideoCapture(url)
        
        if not cap.isOpened():
            print("Failed to open stream")
            return {"status": "error", "message": "Failed to open stream"}
        
        # Read a frame
        ret, frame = cap.read()
        if not ret:
            print("Failed to read frame")
            cap.release()
            return {"status": "error", "message": "Failed to read frame"}
        
        # Save the frame
        filename = "latest_frame.jpg"
        filepath = os.path.join("received_images", filename)
        cv2.imwrite(filepath, frame)
        
        # Release the capture
        cap.release()
        
        # Return success info
        return {
            "status": "success",
            "message": "Frame saved successfully",
            "filename": filename,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
    except Exception as e:
        print(f"Error capturing frame: {str(e)}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    # Create received_images directory if it doesn't exist
    os.makedirs("received_images", exist_ok=True)
    
    # Capture a frame
    result = capture_frame()
    
    # Print the result
    if result["status"] == "success":
        print(f"✅ {result['message']}")
        print(f"📸 Saved as: {result['filename']}")
        print(f"⏰ Timestamp: {result['timestamp']}")
    else:
        print(f"❌ Error: {result['message']}")


