from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Cliente, Interaccion
from .serializers import ClienteSerializer, InteraccionSerializer

class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer

    # Endpoint: PUT /api/clientes/{id}/etapa/
    @action(detail=True, methods=['put'])
    def etapa(self, request, pk=None):
        cliente = self.get_object()
        nueva_etapa = request.data.get('etapa_crm')
        if nueva_etapa:
            cliente.etapa_crm = nueva_etapa
            cliente.save()
            return Response({'status': 'Etapa actualizada', 'etapa_crm': nueva_etapa})
        return Response({'error': 'Proporciona el valor etapa_crm'}, status=status.HTTP_400_BAD_REQUEST)

    # Endpoint: GET /api/clientes/{id}/interacciones/
    @action(detail=True, methods=['get'])
    def interacciones(self, request, pk=None):
        cliente = self.get_object()
        interacciones = Interaccion.objects.filter(cliente=cliente)
        serializer = InteraccionSerializer(interacciones, many=True)
        return Response(serializer.data)

class InteraccionViewSet(viewsets.ModelViewSet):
    queryset = Interaccion.objects.all()
    serializer_class = InteraccionSerializer