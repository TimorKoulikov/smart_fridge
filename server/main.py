from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
import uvicorn
import os
import re

app = FastAPI()

# CORS middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inventory dictionary and minimums
inventory = {
    "egg": 4,
    "milk": 2,
    "bread": 1
}

minimum_required = {
    "egg": 6,
    "milk": 2,
    "bread": 2
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
            ul {{
                font-size: 1.1em;
            }}
            form {{
                margin-top: 20px;
                text-align: center;
            }}
            input[type=text], input[type=number] {{
                padding: 10px;
                margin: 5px;
                border-radius: 5px;
                border: 1px solid #ccc;
                width: 200px;
            }}
            button {{
                padding: 5px 10px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                margin-left: 3px;
                margin-right: 3px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Smart Fridge Inventory</h1>
            <ul>{inventory_html}</ul>

            <h3 style="color:red;">Alerts</h3>
            <ul>{alert_html if alert_html else "<li>No alerts</li>"}</ul>

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
        </div>
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

if __name__ == "__main__":
    os.makedirs("received_images", exist_ok=True)
    uvicorn.run(app, host="0.0.0.0", port=8000)
