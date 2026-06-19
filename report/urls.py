from django.urls import path
from . import views

urlpatterns = [
    path('', views.report_view, name='report'),

    # Form API endpoints
    path('api/update-correction/', views.update_correction, name='update_correction'),
    path('api/save-confirmation/', views.save_confirmation, name='save_confirmation'),

    # Admin dashboard (no login)
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/print/<int:submission_id>/', views.print_report, name='print_report'),
    path('admin/delete/<int:submission_id>/', views.delete_submission, name='delete_submission'),
]
