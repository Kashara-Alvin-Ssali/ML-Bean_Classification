from django.shortcuts import render, redirect
from .forms import PredictionForm
from .inference import mobilenet_v2, resnet, vit
from .utils.preprocess import preprocess_image, preprocess_tf_image
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login as auth_login, authenticate
from django.contrib.auth.decorators import login_required

MODEL_MAP = {
    'mobilenet': (mobilenet_v2.predict, None),
    'resnet': (resnet.predict, preprocess_image),
    'vit': (vit.predict, None),
}

def welcome(request):
    return render(request, 'bean_app/welcome.html')

@login_required
def classify_bean(request):
    prediction = None
    selected_model = None

    if request.method == 'POST':
        form = PredictionForm(request.POST, request.FILES)
        if form.is_valid():
            image = form.cleaned_data['image']
            model_key = form.cleaned_data['model_choice']
            selected_model = dict(form.fields['model_choice'].choices)[model_key]

            predict_fn, preproc_fn = MODEL_MAP[model_key]
            if preproc_fn:
                image_tensor = preproc_fn(image)
                prediction = predict_fn(image_tensor)
            else:
                prediction = predict_fn(image)

    else:
        form = PredictionForm()

    return render(request, 'bean_app/index.html', {
        'form': form,
        'prediction': prediction,
        'selected_model': selected_model
    })

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'bean_app/signup.html', {'form': form})
