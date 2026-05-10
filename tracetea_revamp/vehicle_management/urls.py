from django.conf.urls import url
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from vehicle_management import views
app_name = 'vehicle_management'

urlpatterns = [
    path('vehicle/list/', views.vehicle_list, name='vehicle_list'),
    path('vehicle/create/', views.vehicle_create, name='vehicle_create'),
    path('vehicle/edit/<int:id>/', views.vehicle_edit, name='vehicle_edit'),
    path('vehicle/view/<int:id>/', views.vehicle_view, name='vehicle_view'),
    path('vehicle/delete/<int:id>/', views.vehicle_delete, name='vehicle_delete'),
    path('vehicle-management/',views.VehicleManagementAPIView.as_view()),
    path('vehicle-available-status/',views.VehicleAvailabilityAPIView.as_view())
]
