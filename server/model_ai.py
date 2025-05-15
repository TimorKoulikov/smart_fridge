import os 

def detect_labels_uri(path):
    """Detects labels in the file located in Google Cloud Storage or on the
    Web."""
    from google.cloud import vision

    client = vision.ImageAnnotatorClient()
    
    with open(path, "rb") as image_file:
        content=image_file.read()

    image = vision.Image(content=content)

    response = client.label_detection(image=image)
    labels = response.label_annotations
    
    # Create a list of label descriptions and scores
    label_results = []
    for label in labels:
        label_results.append({
            "description": label.description,
            "score": label.score
        })

    if response.error.message:
        raise Exception(
            "{}\nFor more info on error messages, check: "
            "https://cloud.google.com/apis/design/errors".format(response.error.message)
        )
    
    return label_results

print
