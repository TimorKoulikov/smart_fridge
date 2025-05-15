from fastapi import FastAPI, File, UploadFile, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
from datetime import datetime
import cv2
import numpy as np
from PIL import Image
import io
import socket
import struct
import asyncio

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Create directory for received images if it doesn't exist
os.makedirs("received_images", exist_ok=True)

# Mount the received_images directory
app.mount("/received_images", StaticFiles(directory="received_images"), name="received_images")

# Store the latest image info
latest_image = {
    "filename": None,
    "timestamp": None
}

# Video stream settings
ESP32_IP = "172.20.10.2"
ESP32_PORT = 8080

async def get_video_frame():
    """Generator function to get video frames from ESP32"""
    try:
        # Create socket connection to ESP32
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((ESP32_IP, ESP32_PORT))
        
        while True:
            # Receive frame size
            size_data = client_socket.recv(4)
            if not size_data:
                break
                
            frame_size = struct.unpack('!I', size_data)[0]
            
            # Receive frame data
            frame_data = b''
            while len(frame_data) < frame_size:
                packet = client_socket.recv(frame_size - len(frame_data))
                if not packet:
                    break
                frame_data += packet
            
            # Convert to image
            frame = Image.open(io.BytesIO(frame_data))
            frame_np = np.array(frame)
            
            # Convert to JPEG
            _, buffer = cv2.imencode('.jpg', frame_np)
            frame_bytes = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
    except Exception as e:
        print(f"Error in video stream: {e}")
    finally:
        client_socket.close()

@app.get("/video_feed")
async def video_feed():
    """Endpoint to stream video from ESP32"""
    return StreamingResponse(
        get_video_frame(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@app.get("/", response_class=HTMLResponse)
async def root():
    image_html = ""
    if latest_image["filename"]:
        image_html = f"""
            <div class="image-container">
                <h2>Latest Image</h2>
                <p>Received at: {latest_image['timestamp']}</p>
                <img src="/received_images/{latest_image['filename']}" alt="Latest image" style="max-width: 100%; height: auto;">
            </div>
        """
    
    return f"""
    <!DOCTYPE html>
    <html>
        <head>
            <title>Smart Fridge Server</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 40px;
                    background-color: #f0f0f0;
                }}
                .container {{
                    background-color: white;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 0 10px rgba(0,0,0,0.1);
                }}
                h1 {{
                    color: #333;
                    text-align: center;
                }}
                .status {{
                    color: #4CAF50;
                    font-weight: bold;
                    text-align: center;
                    font-size: 1.2em;
                    margin-top: 20px;
                }}
                .image-container {{
                    margin-top: 20px;
                    text-align: center;
                }}
                .image-container img {{
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    padding: 5px;
                }}
                .video-container {{
                    margin-top: 20px;
                    text-align: center;
                }}
                .video-container img {{
                    max-width: 100%;
                    height: auto;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Smart Fridge Server</h1>
                <div class="status">Server is running!</div>
                <div class="video-container">
                    <h2>Live Video Stream</h2>
                    <img src="/video_feed" alt="Video stream">
                </div>
                {image_html}
            </div>
        </body>
    </html>
    """

@app.post("/send_picture")
async def send_picture(file: UploadFile = File(...)):
    try:
        # Read the image bytes
        contents = await file.read()
        
        # Save the original image
        with open(f"received_images/{file.filename}", "wb") as f:
            f.write(contents)
            
        # Process the image using AI management
        processing_result = ai_manager.process_image(contents, file.filename)
            
        # Update latest image info
        global latest_image
        latest_image["filename"] = file.filename
        latest_image["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        latest_image["processed_filename"] = processing_result.get("processed_filename")
            
        return {
            "message": "Image received and processed successfully",
            "original_filename": file.filename,
            "processing_result": processing_result
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80) 
