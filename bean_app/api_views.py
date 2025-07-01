from rest_framework.decorators import api_view, parser_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework import status

from .inference import mobilenet_v2, resnet, vit
from .utils.preprocess import preprocess_image, preprocess_tf_image

MODEL_MAP = {
    'mobilenet': (mobilenet_v2.predict, None),
    'resnet': (resnet.predict, preprocess_image),
    'vit': (vit.predict, None),
}

@api_view(['POST'])
@parser_classes([MultiPartParser])
def predict_api(request):
    model_name = request.data.get("model")
    image = request.data.get("image")

    if not model_name or not image:
        return Response({"error": "Both 'model' and 'image' are required."},
                        status=status.HTTP_400_BAD_REQUEST)

    if model_name not in MODEL_MAP:
        return Response({"error": "Invalid model name."},
                        status=status.HTTP_400_BAD_REQUEST)

    predict_fn, preprocess_fn = MODEL_MAP[model_name]
    try:
        image_tensor = preprocess_fn(image)
        result = predict_fn(image_tensor)
        return Response({"prediction": result, "model": model_name})
    except Exception as e:
        return Response({"error": str(e)}, status=500)
