import os
from PIL import Image
from model_ai import detect_labels_uri

def process_local_image(image_path):
    """
    Process a local image file and detect labels using Google Cloud Vision API
    Args:
        image_path: Path to the local image file
    Returns:
        dict: Processing results with detected labels
    """
    try:
        # Check if file exists
        if not os.path.exists(image_path):
            return {
                "status": "error",
                "message": f"Image file not found: {image_path}"
            }

        # Convert local file path to URI format
        # For local files, we'll use file:// protocol
        image_uri = f"{os.path.abspath(image_path)}"
        
        # Call the detect_labels_uri function
        labels = detect_labels_uri(image_uri)
        
        return {
            "status": "success",
            "message": "Image processed successfully",
            "labels": labels
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error processing image: {str(e)}"
        }

if __name__ == "__main__":
    # Example usage
    image_path = "received_images/banana.jpeg"
    result = process_local_image(image_path)
    print(result) 
