
from django import forms

MODEL_CHOICES = [
    ('mobilenet', 'MobileNet'),
    ('resnet', 'ResNet'),
    ('vit', 'Vision Transformer'),
]

class PredictionForm(forms.Form):
    image = forms.ImageField()
    model_choice = forms.ChoiceField(choices=MODEL_CHOICES)
