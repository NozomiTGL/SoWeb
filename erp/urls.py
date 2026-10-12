from django.urls import path
from . import views

urlpatterns = [
    # Listado general de órdenes
    path('ordenes/', views.lista_ordenes, name='lista_ordenes'),
    
    # Flujo de creación de orden (3 pasos)
    path('ordenes/nueva/paso-1/', views.nueva_orden_paso1, name='nueva_orden_paso1'),
    path('ordenes/nueva/paso-2/', views.nueva_orden_paso2, name='nueva_orden_paso2'),
    path('ordenes/nueva/paso-3/', views.nueva_orden_paso3, name='nueva_orden_paso3'),
    
    # Endpoint para procesar y limpiar el carrito
    path('ordenes/procesar/', views.procesar_orden, name='procesar_orden'),
]