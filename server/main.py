from fastapi import FastAPI, File, UploadFile, Form, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
import re
from datetime import datetime
import cv2
import numpy as np
from PIL import Image
import io
import socket
import struct
import asyncio
import requests
from frame_capture import capture_frame
from model_ai import detect_labels_uri, localize_objects
from logo_ai import detect_logos
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
    "timestamp": None,
    "processed_filename": None
}

# Video stream settings
ESP32_IP = "172.20.10.2"
ESP32_PORT = 8080

# Inventory dictionary and minimums
inventory = {}

minimum_required = {
}

# Normalize product name
def normalize_product_name(name: str) -> str:
    name = name.strip().lower()
    name = re.sub(r"\s+", " ", name)
    if name.endswith("s") and len(name) > 1:
        name = name[:-1]
    return name

@app.get("/", response_class=HTMLResponse)
async def root():
    # Always show the latest frame
    image_html = """
        <div class="image-container">
            <h2>Latest Camera Image</h2>
            <img id="latestFrame" src="/received_images/latest_frame.jpg?t={}" alt="Latest camera image" style="max-width: 100%; height: auto;">
            <p>Last updated: {}</p>
            <div style="margin: 10px 0;">
                <button onclick="captureFrame()" style="background-color: #2196F3;">Capture New Frame</button>
                <button onclick="detectLabels()" style="background-color: #FF9800;">Detect Labels</button>
                <button onclick="detectLogos()" style="background-color: #4CAF50;">Detect Logos</button>
                <button onclick="detectObjects()" style="background-color: #9C27B0;">Detect Objects</button>
            </div>
            <div id="labelsResult" style="margin-top: 10px; text-align: left; max-width: 640px; margin: 10px auto;">
                <h3>Detected Labels:</h3>
                <ul id="labelsList"></ul>
            </div>
            <div id="logosResult" style="margin-top: 10px; text-align: left; max-width: 640px; margin: 10px auto;">
                <h3>Detected Logos:</h3>
                <ul id="logosList"></ul>
            </div>
            <div id="objectsResult" style="margin-top: 10px; text-align: left; max-width: 640px; margin: 10px auto;">
                <h3>Detected Objects:</h3>
                <ul id="objectsList"></ul>
            </div>
        </div>
    """.format(datetime.now().timestamp(), datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    inventory_html = ""
    alert_html = ""

    for product, quantity in inventory.items():
        min_qty = minimum_required.get(product, 0)

        inventory_html += f"""
        <li>
            {product.capitalize()}: {quantity} (Min: {min_qty})
            <form style="display:inline;" method="post" action="/update_quantity">
                <input type="hidden" name="product_name" value="{product}">
                <input type="hidden" name="change" value="1">
                <button type="submit">+</button>
            </form>
            <form style="display:inline;" method="post" action="/update_quantity">
                <input type="hidden" name="product_name" value="{product}">
                <input type="hidden" name="change" value="-1">
                <button type="submit">−</button>
            </form>
        </li>
        """

        if quantity < min_qty:
            alert_html += f"<li style='color: red;'>⚠️ {product.capitalize()} is below minimum required ({quantity} / {min_qty})</li>"

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
                    border-top: 2px solid #eee;
                    padding-top: 20px;
                }}
                .image-container img {{
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    padding: 5px;
                    max-width: 640px;
                    width: 100%;
                }}
                button {{
                    padding: 10px 20px;
                    font-size: 16px;
                    margin: 10px;
                    cursor: pointer;
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 4px;
                }}
                button:hover {{
                    background-color: #45a049;
                }}
                #labelsList, #logosList, #objectsList {{
                    list-style-type: none;
                    padding: 0;
                }}
                #labelsList li, #logosList li, #objectsList li {{
                    padding: 5px 10px;
                    margin: 5px 0;
                    background-color: #f8f9fa;
                    border-radius: 4px;
                }}
                .section-header {{
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }}
                .section-header button {{
                    margin: 0;
                    padding: 5px 10px;
                    font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Smart Fridge Server</h1>
                <div class="status">Server is running!</div>
                
                <div class="section-header">
                    <h3>Inventory</h3>
                    <button onclick="getProducts()" style="background-color: #2196F3;">Get Products</button>
                </div>
                <ul>{inventory_html}</ul>

                {f'<h3 style="color:red;">Alerts</h3><ul>{alert_html}</ul>' if alert_html else ''}

                <form method="post" action="/add_product">
                    <h3>Add Products</h3>
                    <input type="text" name="product_name" placeholder="Product name" required>
                    <input type="number" name="quantity" placeholder="Quantity" min="1" required>
                    <button type="submit">Add to Inventory</button>
                </form>

                <form method="post" action="/set_minimum">
                    <h3>Set Minimum Required</h3>
                    <input type="text" name="product_name" placeholder="Product name" required>
                    <input type="number" name="minimum_quantity" placeholder="Minimum quantity" min="0" required>
                    <button type="submit">Set Minimum</button>
                </form>

                {image_html}
            </div>
            <script>
                // Function to capture a new frame
                async function captureFrame() {{
                    try {{
                        const response = await fetch('/capture_frame');
                        if (response.ok) {{
                            // Update the image with a new timestamp to prevent caching
                            const img = document.getElementById('latestFrame');
                            img.src = '/received_images/latest_frame.jpg?t=' + new Date().getTime();
                            
                            // Update the last updated timestamp
                            const timestamp = document.querySelector('.image-container p');
                            timestamp.textContent = 'Last updated: ' + new Date().toLocaleString();
                        }} else {{
                            alert('Failed to capture frame');
                        }}
                    }} catch (error) {{
                        console.error('Error:', error);
                        alert('Error capturing frame');
                    }}
                }}

                // Function to detect labels
                async function detectLabels() {{
                    try {{
                        const response = await fetch('/detect_labels');
                        if (response.ok) {{
                            const data = await response.json();
                            const labelsList = document.getElementById('labelsList');
                            
                            if (data.error) {{
                                labelsList.innerHTML = `<li style="color: red;">Error: ${{data.error}}</li>`;
                                localStorage.removeItem('detectedLabels');
                            }} else {{
                                // Store labels in localStorage
                                localStorage.setItem('detectedLabels', JSON.stringify(data.labels));
                                displayLabels(data.labels);
                            }}
                        }} else {{
                            alert('Failed to detect labels');
                        }}
                    }} catch (error) {{
                        console.error('Error:', error);
                        alert('Error detecting labels');
                    }}
                }}

                // Function to display labels
                function displayLabels(labels) {{
                    const labelsList = document.getElementById('labelsList');
                    labelsList.innerHTML = '';
                    labels.forEach(label => {{
                        const li = document.createElement('li');
                        li.textContent = `${{label.description}} (Confidence: ${{(label.score * 100).toFixed(1)}}%)`;
                        labelsList.appendChild(li);
                    }});
                }}

                // Function to detect logos
                async function detectLogos() {{
                    try {{
                        const response = await fetch('/detect_logos');
                        if (response.ok) {{
                            const data = await response.json();
                            const logosList = document.getElementById('logosList');
                            
                            if (data.error) {{
                                logosList.innerHTML = `<li style="color: red;">Error: ${{data.error}}</li>`;
                                localStorage.removeItem('detectedLogos');
                            }} else {{
                                // Store logos in localStorage
                                localStorage.setItem('detectedLogos', JSON.stringify(data.logos));
                                displayLogos(data.logos);
                            }}
                        }} else {{
                            alert('Failed to detect logos');
                        }}
                    }} catch (error) {{
                        console.error('Error:', error);
                        alert('Error detecting logos');
                    }}
                }}

                // Function to display logos
                function displayLogos(logos) {{
                    const logosList = document.getElementById('logosList');
                    logosList.innerHTML = '';
                    logos.forEach(logo => {{
                        const li = document.createElement('li');
                        li.textContent = `${{logo.description}} (Confidence: ${{(logo.score * 100).toFixed(1)}}%)`;
                        logosList.appendChild(li);
                    }});
                }}

                // Function to detect objects
                async function detectObjects() {{
                    try {{
                        const response = await fetch('/detect_objects');
                        if (response.ok) {{
                            const data = await response.json();
                            const objectsList = document.getElementById('objectsList');
                            
                            if (data.error) {{
                                objectsList.innerHTML = `<li style="color: red;">Error: ${{data.error}}</li>`;
                                localStorage.removeItem('detectedObjects');
                            }} else {{
                                // Store objects in localStorage
                                localStorage.setItem('detectedObjects', JSON.stringify(data.objects));
                                displayObjects(data.objects);
                            }}
                        }} else {{
                            alert('Failed to detect objects');
                        }}
                    }} catch (error) {{
                        console.error('Error:', error);
                        alert('Error detecting objects');
                    }}
                }}

                // Function to display objects
                function displayObjects(objects) {{
                    const objectsList = document.getElementById('objectsList');
                    objectsList.innerHTML = '';
                    objects.forEach(obj => {{
                        const li = document.createElement('li');
                        li.textContent = `${{obj.name}} (Confidence: ${{(obj.score * 100).toFixed(1)}}%)`;
                        objectsList.appendChild(li);
                    }});
                }}

                // Load saved data when page loads
                window.onload = function() {{
                    const savedLabels = localStorage.getItem('detectedLabels');
                    if (savedLabels) {{
                        displayLabels(JSON.parse(savedLabels));
                    }}
                    
                    const savedLogos = localStorage.getItem('detectedLogos');
                    if (savedLogos) {{
                        displayLogos(JSON.parse(savedLogos));
                    }}

                    const savedObjects = localStorage.getItem('detectedObjects');
                    if (savedObjects) {{
                        displayObjects(JSON.parse(savedObjects));
                    }}
                }}

                // Function to get products
                async function getProducts() {{
                    try {{
                        const response = await fetch('/get_products');
                        if (response.ok) {{
                            const data = await response.json();
                            if (data.error) {{
                                alert('Error: ' + data.error);
                            }} else {{
                                // Reload the page to show updated inventory
                                location.reload();
                            }}
                        }} else {{
                            alert('Failed to get products');
                        }}
                    }} catch (error) {{
                        console.error('Error:', error);
                        alert('Error getting products');
                    }}
                }}
            </script>
        </body>
    </html>
    """

@app.post("/add_product")
async def add_product(product_name: str = Form(...), quantity: int = Form(...)):
    try:
        normalized_name = normalize_product_name(product_name)
        inventory[normalized_name] = inventory.get(normalized_name, 0) + quantity
        return RedirectResponse("/", status_code=303)
    except Exception as e:
        return {"error": str(e)}

@app.post("/set_minimum")
async def set_minimum(product_name: str = Form(...), minimum_quantity: int = Form(...)):
    try:
        normalized_name = normalize_product_name(product_name)
        minimum_required[normalized_name] = minimum_quantity
        return RedirectResponse("/", status_code=303)
    except Exception as e:
        return {"error": str(e)}

@app.post("/update_quantity")
async def update_quantity(product_name: str = Form(...), change: int = Form(...)):
    try:
        normalized_name = normalize_product_name(product_name)
        if normalized_name in inventory:
            inventory[normalized_name] = max(0, inventory[normalized_name] + change)
        return RedirectResponse("/", status_code=303)
    except Exception as e:
        return {"error": str(e)}

@app.post("/send_picture")
async def send_picture(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        os.makedirs("received_images", exist_ok=True)
        with open(f"received_images/{file.filename}", "wb") as f:
            f.write(contents)
        return {"message": "Image received successfully", "filename": file.filename}
    except Exception as e:
        return {"error": str(e)}

@app.get("/save_frame")
async def save_frame(t: int):
    result = capture_frame()
    if result["status"] == "success":
        global latest_image
        latest_image["filename"] = result["filename"]
        latest_image["timestamp"] = result["timestamp"]
    return result

@app.get("/capture_frame")
async def capture_frame_endpoint():
    result = capture_frame()
    return result

@app.get("/detect_labels")
async def detect_labels_endpoint():
    try:
        # Get the absolute path of the latest frame
        image_path = os.path.abspath("received_images/latest_frame.jpg")
        # Convert to file URI
        image_uri = f"{image_path}"
        
        # Detect labels
        labels = detect_labels_uri(image_uri)
        
        # Convert labels to list of dictionaries with description and score
        labels_list = []
        for label in labels:
            labels_list.append({
                "description": label["description"],
                "score": label["score"]
            })
        
        return {"labels": labels_list}
    except Exception as e:
        print(f"Error detecting labels: {str(e)}")
        return {"error": str(e)}

@app.get("/detect_logos")
async def detect_logos_endpoint():
    try:
        # Get the absolute path of the latest frame
        image_path = os.path.abspath("received_images/latest_frame.jpg")
        # Convert to file URI
        image_uri = f"{image_path}"
        
        # Detect logos
        logos = detect_logos(image_uri)
        
        # Convert logos to list of dictionaries with description and score
        logos_list = []
        for logo in logos:
            logos_list.append({
                "description": logo["description"],
                "score": logo["score"]
            })
        
        return {"logos": logos_list}
    except Exception as e:
        print(f"Error detecting logos: {str(e)}")
        return {"error": str(e)}

@app.get("/detect_objects")
async def detect_objects_endpoint():
    try:
        # Get the absolute path of the latest frame
        image_path = os.path.abspath("received_images/latest_frame.jpg")
        # Convert to file URI
        image_uri = f"{image_path}"
        
        # Detect objects
        objects = localize_objects(image_uri)
        
        # Convert objects to list of dictionaries with name and score
        objects_list = []
        for obj in objects:
            objects_list.append({
                "name": obj["name"],
                "score": obj["score"]
            })
        
        return {"objects": objects_list}
    except Exception as e:
        print(f"Error detecting objects: {str(e)}")
        return {"error": str(e)}

@app.get("/get_products")
async def get_products():
    try:
        # Clear the inventory before adding new items
        inventory.clear()
        
        # First capture a new frame
        capture_result = capture_frame()
        if capture_result["status"] != "success":
            return {"error": "Failed to capture frame"}

        # Get the absolute path of the latest frame
        image_path = os.path.abspath("received_images/latest_frame.jpg")
        # Convert to file URI
        image_uri = f"{image_path}"
        
        # Detect objects
        objects = localize_objects(image_uri)
        
        # Convert objects to list of dictionaries with name and score
        objects_list = []
        for obj in objects:
            # Add each detected object to inventory with quantity 1
            name = obj.name.lower()
            if name in inventory:
                inventory[name] += 1
            else:
                inventory[name] = 1
            
            objects_list.append({
                "name": obj.name,
                "score": obj.score
            })
        
        return {"objects": objects_list}
    except Exception as e:
        print(f"Error getting products: {str(e)}")
        return {"error": str(e)}

if __name__ == "__main__":
    os.makedirs("received_images", exist_ok=True)
    # Initialize inventory
    inventory = {}
    minimum_required = {}
    uvicorn.run(app, host="0.0.0.0", port=8000)
