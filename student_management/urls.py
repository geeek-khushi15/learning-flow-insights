from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('', include('courses.urls')),
    path('', include('batches.urls')),
    path('', include('enrollments.urls')),
    path('', include('materials.urls')),
    path('', include('assessments.urls')),
    path('', include('recommendations.urls')),
    path('', include('certifications.urls')),
    path('', include('accounts.urls')),  # Base maps to accounts for simplicity
]

from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
