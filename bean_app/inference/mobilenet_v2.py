import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import numpy as np

DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# Class names (update if needed)
class_names = ['angular_leaf_spot', 'bean_rust', 'healthy']
NUM_CLASSES = len(class_names)

# Define the model architecture
model = models.mobilenet_v2(pretrained=False)
model.classifier[1] = nn.Linear(model.last_channel, NUM_CLASSES)
model.load_state_dict(torch.load('bean_app/models/best_model.pt', map_location=DEVICE))
model.eval()
model.to(DEVICE)

def preprocess_image(image_file):
    preprocess = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
    ])
    img = Image.open(image_file).convert('RGB')
    return preprocess(img).unsqueeze(0)

def predict(image_file):
    image_tensor = preprocess_image(image_file).to(DEVICE)
    with torch.no_grad():
        outputs = model(image_tensor)
        probs = torch.softmax(outputs, dim=1).cpu().numpy()[0]
        class_id = np.argmax(probs)
        confidence = probs[class_id] * 100
        return f"{class_names[class_id]} ({confidence:.2f}%)" 