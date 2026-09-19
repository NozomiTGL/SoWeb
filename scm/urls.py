from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views
from . import api

urlpatterns = [
    # Rutas para Proveedores
    path('proveedores/', views.lista_proveedores, name='lista_proveedores'),
    path('proveedores/nuevo/', views.crear_proveedor, name='crear_proveedor'),
    path('proveedores/editar/<int:id>/', views.editar_proveedor, name='editar_proveedor'),
    path('proveedores/eliminar/<int:id>/', views.eliminar_proveedor, name='eliminar_proveedor'),
    
    # Rutas para Productos/Servicios
    path('productos/', views.lista_productos, name='lista_productos'),
    path('productos/nuevo/', views.crear_producto, name='crear_producto'),
    path('productos/editar/<int:id>/', views.editar_producto, name='editar_producto'),
    path('productos/eliminar/<int:id>/', views.eliminar_producto, name='eliminar_producto'),

    # Rutas para Movimientos de Inventario
    path('movimientos/', views.lista_movimientos, name='lista_movimientos'),
    path('movimientos/nuevo/', views.registrar_movimiento, name='registrar_movimiento'),
    
    # Rutas de Inventario
    path('inventario/', views.vista_inventario, name='vista_inventario'),
    
    # Rutas para Pedidos (Fase 2)
    path('pedidos/', views.lista_pedidos, name='lista_pedidos'),
    path('pedidos/nuevo/', views.crear_pedido, name='crear_pedido'),
    path('pedidos/editar/<int:id>/', views.editar_pedido, name='editar_pedido'),
    path('pedidos/eliminar/<int:id>/', views.eliminar_pedido, name='eliminar_pedido'),
    
    # Ruta para Estrategia Logística (Push vs Pull)
    path('logistica/', views.estrategia_logistica, name='estrategia_logistica'),
    # Ruta para el Dashboard
    path('dashboard/', views.dashboard_scm, name='dashboard_scm'),
]

# ==========================================
# RUTAS DE LA API REST
# ==========================================
router = DefaultRouter()
router.register(r'api/proveedores', api.ProveedorViewSet, basename='api-proveedor')
router.register(r'api/productos', api.ProductoViewSet, basename='api-producto')

# Añadimos las rutas generadas por el router a los urlpatterns
urlpatterns += router.urls