from django.urls import path
from . import views
from .api_views import predict_api
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.welcome, name='welcome'),
    path('index/', views.classify_bean, name='classify_bean'),
    path('api/predict/', predict_api, name='predict_api'),
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('signup/', views.signup, name='signup'),
    path('profile/', views.profile_update, name='profile_update'),
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='bean_app/password_reset_form.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='bean_app/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='bean_app/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='bean_app/password_reset_complete.html'), name='password_reset_complete'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('password_change/', auth_views.PasswordChangeView.as_view(template_name='bean_app/password_change_form.html'), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='bean_app/password_change_done.html'), name='password_change_done'),
]
