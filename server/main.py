from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <!DOCTYPE html>
    <html>
        <head>
            <title>Smart Fridge Server</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 40px;
                    background-color: #f0f0f0;
                }
                .container {
                    background-color: white;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 0 10px rgba(0,0,0,0.1);
                }
                h1 {
                    color: #333;
                    text-align: center;
                }
                .status {
                    color: #4CAF50;
                    font-weight: bold;
                    text-align: center;
                    font-size: 1.2em;
                    margin-top: 20px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Smart Fridge Server</h1>
                <div class="status">Server is running!</div>
            </div>
        </body>
    </html>
    """

@app.post("/send_picture")
async def send_picture(file: UploadFile = File(...)):
    try:
        # Read the image bytes
        contents = await file.read()
        
        # Print the received bytes
        print("Received image bytes:ssss", contents)
        
        # Save the image
        with open(f"received_images/{file.filename}", "wb") as f:
            f.write(contents)
            
        return {"message": "Image received successfully", "filename": file.filename}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import os
    # Create directory for received images if it doesn't exist
    os.makedirs("received_images", exist_ok=True)
    uvicorn.run(app, host="0.0.0.0", port=8000) 