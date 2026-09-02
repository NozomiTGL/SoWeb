from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('clientes/', views.lista_clientes, name='lista_clientes'),
    path('clientes/crear/', views.crear_cliente, name='crear_cliente'),
    path('clientes/<int:pk>/editar/', views.editar_cliente, name='editar_cliente'),
    path('clientes/<int:pk>/eliminar/', views.eliminar_cliente, name='eliminar_cliente'),
    path('clientes/<int:pk>/historial/', views.historial_cliente, name='historial_cliente'),
    path('clientes/<int:pk>/', views.detalle_cliente, name='detalle_cliente'),
    path('mi-actividad/', views.mi_actividad, name='mi_actividad'),
    path('reportes/', views.reportes_metricas, name='reportes_metricas'),
    path('clientes/exportar-csv/', views.exportar_clientes_csv, name='exportar_clientes_csv'),
    path('usuarios/', views.lista_usuarios, name='lista_usuarios'),
    path('usuarios/crear/', views.crear_usuario, name='crear_usuario'),
    path('usuarios/<int:pk>/editar/', views.editar_usuario, name='editar_usuario'),
]