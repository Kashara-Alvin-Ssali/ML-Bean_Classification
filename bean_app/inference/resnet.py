import torch
import torch.nn.functional as F
from torchvision import models

# Define the model architecture (ResNet18 with 3 output classes)
model = models.resnet18(pretrained=False)
num_ftrs = model.fc.in_features
model.fc = torch.nn.Linear(num_ftrs, 3)

# Load the model state dict directly (not from a checkpoint dict)
model.load_state_dict(torch.load('bean_app/models/resnet_model.pth', map_location='cpu'))
model.eval()

# Class order must match train_dataset.classes from training
class_names = ['angular_leaf_spot', 'bean_rust', 'healthy']

def predict(image_tensor):
    with torch.no_grad():
        output = model(image_tensor)
        probs = F.softmax(output, dim=1)
        class_id = torch.argmax(probs, dim=1).item()
        confidence = probs[0][class_id].item() * 100
        return f"{class_names[class_id]} ({confidence:.2f}%)"
