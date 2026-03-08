from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static

def home(request):
    return redirect('/accounts/login/')

urlpatterns = [
    path('', home),
    path('admin/', admin.site.urls),

    path('accounts/', include('accounts.urls')),
    path('attendance/', include('attendance.urls')),

    path('', include('courses.urls')),
    path('', include('batches.urls')),
    path('', include('enrollments.urls')),
    path('', include('materials.urls')),
    path('', include('assessments.urls')),
    path('', include('recommendations.urls')),
    path('', include('certifications.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)