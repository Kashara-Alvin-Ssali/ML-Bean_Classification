from django.shortcuts import render, redirect
from .forms import PredictionForm, UserRegistrationForm, UserLoginForm, ProfileUpdateForm, ContactForm
from .inference import mobilenet_v2, resnet, vit
from .utils.preprocess import preprocess_image, preprocess_tf_image
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login as auth_login, authenticate, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages

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
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'bean_app/signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            # Handle 'Remember me'
            if not form.cleaned_data.get('remember_me'):
                request.session.set_expiry(0)  # Session expires on browser close
            else:
                request.session.set_expiry(1209600)  # 2 weeks
            return redirect('classify_bean')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = UserLoginForm()
    return render(request, 'bean_app/login.html', {'form': form})

@login_required
def profile_update(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, user=request.user, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile_update')
    else:
        form = ProfileUpdateForm(user=request.user, instance=request.user)
    return render(request, 'bean_app/profile_update.html', {'form': form})

def about(request):
    return render(request, 'bean_app/about.html')

def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your message has been sent!')
            form = ContactForm()  # Clear the form
    else:
        form = ContactForm()
    return render(request, 'bean_app/contact.html', {'form': form})
