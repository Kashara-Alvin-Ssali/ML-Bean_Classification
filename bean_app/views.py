from django.shortcuts import render, redirect, get_object_or_404
from .forms import PredictionForm, UserRegistrationForm, UserLoginForm, ProfileUpdateForm, ContactForm
from .inference import mobilenet_v2, resnet, vit
from .utils.preprocess import preprocess_image, preprocess_tf_image
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login as auth_login, authenticate, logout as auth_logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Prediction
from django.http import HttpResponse, HttpResponseForbidden, FileResponse
import os
from django.conf import settings
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import io
from collections import Counter
from django.db.models.functions import TruncDate
from django.db.models import Count
from django.contrib.auth import get_user_model

MODEL_MAP = {
    'mobilenet': (mobilenet_v2.predict, None),
    'resnet': (resnet.predict, preprocess_image),
    'vit': (vit.predict, None),
}

def welcome(request):
    return render(request, 'bean_app/welcome.html')

@login_required
def classify_bean(request):
    results = []
    selected_model = None
    error_message = None
    if request.method == 'POST':
        form = PredictionForm(request.POST)
        images = request.FILES.getlist('images')
        if form.is_valid():
            model_key = form.cleaned_data['model_choice']
            selected_model = dict(form.fields['model_choice'].choices)[model_key]
            if not images:
                error_message = 'Please upload at least one image.'
            else:
                predict_fn, preproc_fn = MODEL_MAP[model_key]
                for image in images:
                    if not image.content_type.startswith('image/'):
                        error_message = 'Only image files are allowed.'
                        break
                    if preproc_fn:
                        image_tensor = preproc_fn(image)
                        prediction = predict_fn(image_tensor)
                    else:
                        prediction = predict_fn(image)
                    prediction_obj = Prediction.objects.create(
                        user=request.user,
                        image=image,
                        result=prediction,
                        model_used=selected_model
                    )
                    results.append({
                        'image': prediction_obj.image.url,
                        'result': prediction_obj.result,
                        'model': prediction_obj.model_used,
                        'date': prediction_obj.created_at,
                    })
    else:
        form = PredictionForm()
    return render(request, 'bean_app/index.html', {
        'form': form,
        'results': results,
        'selected_model': selected_model,
        'error_message': error_message,
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
    user = request.user
    profile = user.profile
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, user=user, instance=user)
        if form.is_valid():
            user = form.save()
            if request.POST.get('avatar_remove') == 'true':
                if profile.avatar:
                    profile.avatar.delete(save=False)
                profile.avatar = None
                profile.save()
                messages.success(request, 'Profile picture removed.')
            else:
                avatar = form.cleaned_data.get('avatar')
                if avatar:
                    profile.avatar = avatar
                    profile.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile_update')
    else:
        form = ProfileUpdateForm(user=user, instance=user)
    return render(request, 'bean_app/profile_update.html', {'form': form, 'profile': profile})

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

@login_required
def my_history(request):
    predictions = request.user.predictions.order_by('-created_at')
    return render(request, 'bean_app/my_history.html', {'predictions': predictions})

@login_required
def delete_prediction(request, pk):
    prediction = get_object_or_404(Prediction, pk=pk, user=request.user)
    if request.method == 'POST':
        prediction.image.delete(save=False)
        prediction.delete()
        messages.success(request, 'Prediction deleted.')
    return redirect('my_history')

@login_required
def download_prediction(request, pk):
    prediction = get_object_or_404(Prediction, pk=pk, user=request.user)
    # Serve the image file for download
    response = FileResponse(prediction.image.open('rb'), as_attachment=True, filename=os.path.basename(prediction.image.name))
    return response

@login_required
def download_prediction_txt(request, pk):
    prediction = get_object_or_404(Prediction, pk=pk, user=request.user)
    content = f"Result: {prediction.result}\nModel: {prediction.model_used}\nDate: {prediction.created_at.strftime('%Y-%m-%d %H:%M')}"
    response = HttpResponse(content, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename=prediction_{pk}.txt'
    return response

@login_required
def download_prediction_pdf(request, pk):
    prediction = get_object_or_404(Prediction, pk=pk, user=request.user)
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Branding/Header
    p.setFont("Helvetica-Bold", 18)
    p.setFillColorRGB(0.22, 0.55, 0.24)
    p.drawString(40, height - 50, "Bean Leaf Disease Classifier Report")
    p.setFont("Helvetica", 12)
    p.setFillColorRGB(0, 0, 0)
    p.drawString(40, height - 80, f"User: {request.user.username}")
    p.drawString(40, height - 100, f"Date: {prediction.created_at.strftime('%Y-%m-%d %H:%M')}")
    p.drawString(40, height - 120, f"Model Used: {prediction.model_used}")
    p.drawString(40, height - 140, f"Result: {prediction.result}")

    # Image
    img_y = height - 320
    try:
        img_path = prediction.image.path
        img = ImageReader(img_path)
        p.drawImage(img, 40, img_y, width=180, height=180, preserveAspectRatio=True, mask='auto')
    except Exception as e:
        p.setFont("Helvetica", 10)
        p.setFillColorRGB(1, 0, 0)
        p.drawString(40, img_y + 80, "[Image not available]")

    # Footer/Branding
    p.setFont("Helvetica-Oblique", 10)
    p.setFillColorRGB(0.5, 0.5, 0.5)
    p.drawString(40, 40, "Powered by Bean Classifier & AI")
    p.save()
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename=prediction_{pk}.pdf'
    return response

@login_required
def dashboard(request):
    user = request.user
    predictions = user.predictions.order_by('-created_at')
    total_predictions = predictions.count()
    recent_predictions = predictions[:10]
    # Most common result
    result_counts = Counter(predictions.values_list('result', flat=True))
    most_common_result = result_counts.most_common(1)[0][0] if result_counts else None
    # Data for charts: predictions per day
    per_day = predictions.annotate(day=TruncDate('created_at')).values('day').annotate(count=Count('id')).order_by('day')
    chart_labels = [str(item['day']) for item in per_day]
    chart_data = [item['count'] for item in per_day]
    # Data for class distribution
    class_counts = predictions.values('result').annotate(count=Count('id')).order_by('-count')
    class_labels = [item['result'] for item in class_counts]
    class_data = [item['count'] for item in class_counts]
    # Data for model usage breakdown
    model_counts_qs = predictions.values('model_used').annotate(count=Count('id')).order_by('-count')
    model_labels = [item['model_used'] for item in model_counts_qs]
    model_counts = [item['count'] for item in model_counts_qs]
    model_usage = zip(model_labels, model_counts)
    # Recent activity feed (predictions + stubs for other actions)
    activity_feed = list(predictions.order_by('-created_at')[:10].values('created_at', 'result', 'model_used', 'image'))
    # Example: add stubs for other actions (profile update, password change)
    # In a real app, you would log these actions in a separate model or use signals
    # For now, just show predictions
    # Most recent images (last 5 prediction images)
    recent_images = predictions.order_by('-created_at')[:5].values_list('image', flat=True)
    return render(request, 'bean_app/dashboard.html', {
        'total_predictions': total_predictions,
        'most_common_result': most_common_result,
        'recent_predictions': recent_predictions,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'class_labels': class_labels,
        'class_data': class_data,
        'model_labels': model_labels,
        'model_counts': model_counts,
        'model_usage': model_usage,
        'activity_feed': activity_feed,
        'recent_images': recent_images,
    })

@login_required
def settings_view(request):
    user = request.user
    User = get_user_model()
    message = None
    if request.method == 'POST':
        if 'update_account' in request.POST:
            new_email = request.POST.get('email')
            new_username = request.POST.get('username')
            if new_email and new_email != user.email:
                user.email = new_email
            if new_username and new_username != user.username:
                user.username = new_username
            user.save()
            message = 'Account details updated.'
        elif 'toggle_notifications' in request.POST:
            profile = user.profile
            profile.notifications_enabled = not getattr(profile, 'notifications_enabled', True)
            profile.save()
            message = 'Notification preferences updated.'
        elif 'delete_account' in request.POST:
            user.delete()
            return redirect('welcome')
    return render(request, 'bean_app/settings.html', {
        'message': message,
        'last_login': user.last_login,
        'email': user.email,
        'username': user.username,
        'notifications_enabled': getattr(user.profile, 'notifications_enabled', True),
    })
