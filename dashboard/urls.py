from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('admin/', views.admin_overview, name='admin_overview'),
    path('worker/', views.worker_summary, name='worker_summary'),
    path('customer/', views.customer_summary, name='customer_summary'),
]


