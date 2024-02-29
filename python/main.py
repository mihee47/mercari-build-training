import os
import logging
import pathlib
import json
import hashlib

from fastapi import FastAPI, Form, HTTPException, File, UploadFile
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
logger = logging.getLogger("uvicorn")
logger.level = logging.INFO
images = pathlib.Path(__file__).parent.resolve() / "images"
origins = [os.environ.get("FRONT_URL", "http://localhost:3000")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Load existing items
def load_items(filename="./items.json"):
    if not os.path.exists(filename):
        return {"items": []}
    with open(filename, "r") as file:
        return json.load(file)

# Save items to items.json
def save_items(items, filename="./items.json"):
    with open(filename, "w") as file:
        json.dump(items, file, indent=4)

# Hashing the image
def hash_image(filename: UploadFile):
    file_content = filename.file.read()
    return hashlib.sha256(file_content).hexdigest()

@app.get("/")
def root():
    return {"message": "Hello, world!"}

@app.post("/items")
async def add_item(name: str = Form(...), 
             category: str = Form(...), 
             image: UploadFile = File(...)):
        logger.info(f"Received item: {name}, Category: {category}")

        # Read and hash the image
        image_hash = hash_image(image)

        # Save the hashed image file
        image_name = f"{image_hash}.jpg"
        image_path = images / image_name
        with open(image_path, "wb") as file:
            file.write(image.file.read())

        items = load_items()
        items["items"].append({"name": name, "category": category, "image": image_name})
        save_items(items)
        return {"message": f"Item received: {name}"}


@app.get("/items")
def get_items():
    items = load_items()
    return items

@app.get("/items/{item_id}")
def get_item(item_id: int):
    items = load_items()
    if 0 <= item_id < len(items["items"]):
        return items["items"][item_id-1]
    else:
        raise HTTPException(status_code=404, detail="Item not found")


@app.get("/image/{image_name}")
async def get_image(image_name):
    # Create image path
    image = images / image_name

    if not image_name.endswith(".jpg"):
        raise HTTPException(status_code=400, detail="Image path does not end with .jpg")

    if not image.exists():
        log = logger.debug(f"Image not found: {image}")
        image = images / "default.jpg"
        print(log)

    return FileResponse(image)
