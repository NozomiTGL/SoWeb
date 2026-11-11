from django.urls import path
from . import views

urlpatterns = [
    path('catalogo/', views.catalogo_tienda, name='catalogo_tienda'),

    # Nuevas rutas del carrito
    path('carrito/', views.ver_carrito, name='ver_carrito'),
    path('carrito/agregar/', views.agregar_al_carrito, name='agregar_al_carrito'),
    path('carrito/eliminar/<int:item_id>/', views.eliminar_item_carrito, name='eliminar_item_carrito'),
    path('carrito/vaciar/', views.vaciar_carrito, name='vaciar_carrito'),

    # Rutas de Checkout y Transacción
    path('checkout/', views.checkout, name='checkout'),
    path('checkout/procesar/', views.procesar_compra, name='procesar_compra'),

    # Rutas de Monedero y Checkout
    path('monedero/', views.ver_monedero, name='ver_monedero'),
    path('monedero/recargar/', views.recargar_monedero, name='recargar_monedero'),
    path('checkout/', views.checkout, name='checkout'),
    path('checkout/procesar/', views.procesar_compra, name='procesar_compra'),

    # Nueva ruta: Historial de Pedidos
    path('mis-pedidos/', views.mis_pedidos, name='mis_pedidos'),
    path('mis-pedidos/<int:orden_id>/', views.detalle_orden, name='detalle_orden'),
]