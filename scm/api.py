from rest_framework import serializers, viewsets
from .models import Proveedor, Producto

# ==========================================
# SERIALIZADORES (Convierten BD a JSON)
# ==========================================
class ProveedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proveedor
        fields = '__all__'

class ProductoSerializer(serializers.ModelSerializer):
    # Agregamos este campo extra para que el JSON muestre el nombre del proveedor
    # y no solo su número de ID, lo cual hace la API mucho más fácil de leer.
    proveedor_nombre = serializers.ReadOnlyField(source='proveedor.nombre')

    class Meta:
        model = Producto
        fields = '__all__'

# ==========================================
# VIEWSETS (Controlan el CRUD de la API)
# ==========================================
class ProveedorViewSet(viewsets.ModelViewSet):
    queryset = Proveedor.objects.all().order_by('nombre')
    serializer_class = ProveedorSerializer

class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all().order_by('nombre')
    serializer_class = ProductoSerializer