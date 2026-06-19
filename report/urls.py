from django.urls import path
from . import views

urlpatterns = [
    path('', views.report_view, name='report'),

    # Public form API endpoints
    path('api/update-correction/', views.update_correction, name='update_correction'),
    path('api/save-answer/', views.save_answer, name='save_answer'),
    path('api/save-confirmation/', views.save_confirmation, name='save_confirmation'),

    # Admin auth
    path('admin/login/', views.admin_login, name='admin_login'),
    path('admin/logout/', views.admin_logout, name='admin_logout'),

    # Admin dashboard
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/print/<int:submission_id>/', views.print_report, name='print_report'),
    path('admin/delete/<int:submission_id>/', views.delete_submission, name='delete_submission'),

    # Admin: Corrections Manager API
    path('admin/api/corrections/', views.admin_get_corrections, name='admin_get_corrections'),
    path('admin/api/corrections/seed/', views.admin_seed_corrections, name='admin_seed_corrections'),
    path('admin/api/corrections/add/', views.admin_add_correction_item, name='admin_add_correction_item'),
    path('admin/api/corrections/<int:item_id>/update/', views.admin_update_correction_item, name='admin_update_correction_item'),
    path('admin/api/corrections/<int:item_id>/delete/', views.admin_delete_correction_item, name='admin_delete_correction_item'),

    # Admin: Sections API
    path('admin/api/sections/add/', views.admin_add_section, name='admin_add_section'),
    path('admin/api/sections/<str:section_key>/update-title/', views.admin_update_section_title, name='admin_update_section_title'),
    path('admin/api/sections/<str:section_key>/delete/', views.admin_delete_section, name='admin_delete_section'),

    path('thanks/', views.thanks_view, name='thanks'),
]
