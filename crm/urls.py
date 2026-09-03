"""
Módulo de Enrutamiento (URLs) para la aplicación CRM de SoWeb.

Mapea las peticiones HTTP a sus respectivas vistas en `crm/views.py`,
organizando las rutas por módulos: Dashboard, Directorio de Clientes,
Actividad Personal, Reportes y Administración de Usuarios/Trabajadores.
"""

from django.urls import path
from . import views

urlpatterns = [
    # ---------------------------------------------------------
    # 1. DASHBOARD GENERAL
    # ---------------------------------------------------------
    path('', views.dashboard, name='dashboard'),

    # ---------------------------------------------------------
    # 2. GESTIÓN Y CRUD DE CLIENTES
    # ---------------------------------------------------------
    path('clientes/', views.lista_clientes, name='lista_clientes'),
    path('clientes/crear/', views.crear_cliente, name='crear_cliente'),
    path('clientes/<int:pk>/editar/', views.editar_cliente, name='editar_cliente'),
    path('clientes/<int:pk>/eliminar/', views.eliminar_cliente, name='eliminar_cliente'),
    path('clientes/<int:pk>/historial/', views.historial_cliente, name='historial_cliente'),
    path('clientes/<int:pk>/', views.detalle_cliente, name='detalle_cliente'),
    path('clientes/exportar-csv/', views.exportar_clientes_csv, name='exportar_clientes_csv'),

    # ---------------------------------------------------------
    # 3. ACTIVIDAD PERSONAL Y REPORTES
    # ---------------------------------------------------------
    path('mi-actividad/', views.mi_actividad, name='mi_actividad'),
    path('reportes/', views.reportes_metricas, name='reportes_metricas'),

    # ---------------------------------------------------------
    # 4. GESTIÓN DE TRABAJADORES / USUARIOS (Exclusivo Administradores)
    # ---------------------------------------------------------
    path('usuarios/', views.lista_usuarios, name='lista_usuarios'),
    path('usuarios/crear/', views.crear_usuario, name='crear_usuario'),
    path('usuarios/<int:pk>/editar/', views.editar_usuario, name='editar_usuario'),
]