
from django.conf.urls import url
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from accounts import views
app_name = 'accounts'
urlpatterns = [
	url(r'^login/$', views.admin_login, name="admin_login"),
	url(r"logout/$", auth_views.LogoutView.as_view(), name="logout"),
    # API
    path('login-api/', views.LoginView.as_view(), name='knox_login'),
	path('login/logout_app/', views.LogoutView.as_view(), name='knox_logout'),
	# USER PASSWORD RESET API
	path('request-otp/', views.RequestOTPAPIView.as_view()),
	path('validate-otp/',views.ValidateOTP.as_view()),
	path('password-reset/', views.SetNewPassWordAPIView.as_view()),
	path('password-change/', views.ChangePasswordAPIView.as_view()),
    path('generate-qr/', views.GenerateQRCodeView.as_view(), name='generate-qr'),
	url(r'^change_password/$', views.change_password_view, name="change_password"),
	path('users-change-password/<int:user_id>/', views.profile_change_password, name='users_change_password'),
	
]