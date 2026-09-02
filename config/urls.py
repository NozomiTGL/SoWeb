from django.contrib import admin
from django.urls import path, include
from crm import views as crm_views  

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),  # Rutas nativas de Login/Logout
    path('accounts/register/', crm_views.registrar_usuario, name='registrar_usuario'),
    path('', include('crm.urls')),  # Rutas internas protegidas del CRM
]