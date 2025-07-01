# models.py
from django.db import models
from django.contrib.auth.models import User

# No database models needed for this project (inference-only app)
# You can add prediction logs or history here in the future

class Prediction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image_path = models.CharField(max_length=255)
    model = models.CharField(max_length=32)
    result = models.CharField(max_length=64)
    confidence = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.model} - {self.result} ({self.confidence:.2f}%) @ {self.timestamp}"
