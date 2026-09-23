from django.db.models import F
from .models import Producto

def alertas_stock(request):
    """
    Inyecta automáticamente en todas las plantillas la lista de productos
    que están en nivel crítico (stock_actual <= stock_minimo).
    """
    if request.user.is_authenticated:
        productos_criticos = Producto.objects.filter(
            stock_actual__lte=F('stock_minimo')
        ).order_by('stock_actual')
        
        return {
            'productos_criticos': productos_criticos,
            'total_criticos': productos_criticos.count(),
        }
    return {
        'productos_criticos': [],
        'total_criticos': 0,
    }