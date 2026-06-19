from django.contrib import admin
from django.urls import path, include

admin.site.site_header = 'CUG System Admin'

urlpatterns = [
    path('system-admin/', admin.site.urls),   # Django built-in admin
    path('', include('report.urls')),          # public report + custom /admin/
]
