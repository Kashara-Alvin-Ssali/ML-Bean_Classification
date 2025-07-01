from torchvision import transforms
from PIL import Image
import numpy as np
from tensorflow.keras.preprocessing import image as tf_image

def preprocess_image(image_file):
    # Preprocessing for PyTorch ResNet: resize, to tensor, normalize
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    image = Image.open(image_file).convert("RGB")
    return transform(image).unsqueeze(0)

def preprocess_tf_image(image_file):
    img = Image.open(image_file).resize((224, 224)).convert("RGB")
    img_array = tf_image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = img_array / 255.0
    return img_array
