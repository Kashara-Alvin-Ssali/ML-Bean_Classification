import torch
import torch.nn.functional as F
from transformers import ViTForImageClassification, ViTImageProcessor
from PIL import Image

# Load the image processor (feature extractor)
processor = ViTImageProcessor.from_pretrained("google/vit-base-patch16-224")

# Define the model architecture (must match training)
model = ViTForImageClassification.from_pretrained(
    "google/vit-base-patch16-224",
    num_labels=3,
    ignore_mismatched_sizes=True
)
model.load_state_dict(torch.load('bean_app/models/vit_model.pt', map_location='cpu'))
model.eval()

class_names = ['angular_leaf_spot', 'bean_rust', 'healthy']

def preprocess_image(image_file):
    image = Image.open(image_file).convert('RGB')
    inputs = processor(images=image, return_tensors="pt")
    return inputs['pixel_values']

def predict(image_file):
    image_tensor = preprocess_image(image_file)
    with torch.no_grad():
        outputs = model(pixel_values=image_tensor)
        probs = F.softmax(outputs.logits, dim=1)
        class_id = torch.argmax(probs, dim=1).item()
        confidence = probs[0][class_id].item() * 100
        return f"{class_names[class_id]} ({confidence:.2f}%)"
