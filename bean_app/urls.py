from django.urls import path
from . import views
from .api_views import predict_api
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.welcome, name='welcome'),
    path('index/', views.classify_bean, name='classify_bean'),
    path('api/predict/', predict_api, name='predict_api'),
    path('login/', auth_views.LoginView.as_view(template_name='bean_app/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('signup/', views.signup, name='signup'),
]
