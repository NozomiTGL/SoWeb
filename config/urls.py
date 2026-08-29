from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # URLs de Autenticación nativas de Django (login, logout, etc.)
    path('accounts/', include('django.contrib.auth.urls')),
    # URLs de nuestro CRM
    path('', include('crm.urls')),
]