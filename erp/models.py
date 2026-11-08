from django.db import models
from django.contrib.auth.models import User
from crm.models import Cliente
from scm.models import Producto

class OrdenEmpresarial(models.Model):
    """
    Núcleo del ERP: Centraliza las ventas conectando al Cliente (CRM) 
    con el inventario y logística (SCM)[cite: 14].
    """
    ESTADO_CHOICES = [
        ('Pendiente', 'Pendiente'),
        ('Procesando', 'Procesando'),
        ('Completada', 'Completada'),
        ('Cancelada', 'Cancelada'),
    ]

    folio = models.CharField(max_length=20, unique=True, blank=True, verbose_name="Folio de Orden")
    
    # 🔗 CONEXIÓN CON CRM
    cliente = models.ForeignKey(
        Cliente, 
        on_delete=models.RESTRICT, 
        verbose_name="Cliente (CRM)"
    )
    
    # Datos de la operación[cite: 14]
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='Pendiente')
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="Total de la Orden")
    
    # Usuario que registró la venta
    usuario = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        verbose_name="Ejecutivo Responsable"
    )

    class Meta:
        verbose_name = "Orden Empresarial"
        verbose_name_plural = "Órdenes Empresariales"
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.folio} - {self.cliente.nombre}"

    def save(self, *args, **kwargs):
        # Autogenerar Folio de Orden (ej. OR-001)
        if not self.folio:
            total_ordenes = OrdenEmpresarial.objects.count() + 1
            self.folio = f"OR-{total_ordenes:03d}"
        super().save(*args, **kwargs)


class DetalleOrden(models.Model):
    """
    Desglosa los productos específicos que se incluyeron en una Orden Empresarial.
    """
    orden = models.ForeignKey(
        OrdenEmpresarial, 
        on_delete=models.CASCADE, 
        related_name='detalles'
    )
    
    # 🔗 CONEXIÓN CON SCM[cite: 14]
    producto = models.ForeignKey(
        Producto, 
        on_delete=models.RESTRICT, 
        verbose_name="Servicio / Producto (SCM)"
    )
    
    cantidad = models.PositiveIntegerField(verbose_name="Cantidad")
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio Unitario")
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, blank=True, verbose_name="Subtotal")

    class Meta:
        verbose_name = "Detalle de Orden"
        verbose_name_plural = "Detalles de Órdenes"

    def save(self, *args, **kwargs):
        # Calculamos el subtotal automáticamente antes de guardar
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)


class EstadoERP(models.Model):
    """
    Evalúa el nivel de madurez y adopción de la plataforma ERP en la empresa[cite: 16].
    """
    NIVEL_CHOICES = [
        ('Básico', 'Básico (Módulos aislados)'),
        ('Integrado', 'Integrado (CRM y SCM conectados)'),
        ('Automatizado', 'Automatizado (Procesos en tiempo real)'),
        ('Optimizado', 'Optimizado (Inteligencia y métricas)'),
    ]

    nivel = models.CharField(max_length=20, choices=NIVEL_CHOICES, default='Básico', verbose_name="Nivel de Implementación")
    ultima_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Estado de Madurez ERP"
        verbose_name_plural = "Estados de Madurez ERP"

    def __str__(self):
        return f"Nivel Actual: {self.nivel}"

from django.db import models

class Impuesto(models.Model):
    """
    Configurador de cálculo de impuestos aplicables en el checkout.
    """
    nombre = models.CharField(max_length=50, verbose_name="Nombre del Impuesto (Ej. IVA)")
    porcentaje = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Porcentaje (%)")
    estado = models.BooleanField(default=True, verbose_name="Activo")

    class Meta:
        verbose_name = "Impuesto"
        verbose_name_plural = "Impuestos"

    def __str__(self):
        return f"{self.nombre} ({self.porcentaje}%)"


class Promocion(models.Model):
    """
    Gestión de promociones y descuentos para la estrategia de comercialización.
    """
    TIPO_CHOICES = [
        ('porcentaje', 'Descuento por Porcentaje (%)'),
        ('monto', 'Descuento por Monto Fijo ($)'),
    ]

    nombre = models.CharField(max_length=150, verbose_name="Nombre de la Promoción")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    tipo_descuento = models.CharField(max_length=20, choices=TIPO_CHOICES, verbose_name="Tipo de Descuento")
    valor = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor del Descuento")
    fecha_inicio = models.DateTimeField(verbose_name="Fecha de Inicio")
    fecha_fin = models.DateTimeField(verbose_name="Fecha de Fin")
    estado = models.BooleanField(default=True, verbose_name="Promoción Activa")
    
    # Opcional: Podrías enlazarlo a productos específicos con un ManyToManyField si no aplica a todo el carrito
    # productos_aplicables = models.ManyToManyField('Producto', blank=True, related_name='promociones')

    class Meta:
        verbose_name = "Promoción"
        verbose_name_plural = "Promociones"

    def __str__(self):
        return f"{self.nombre} - {self.get_tipo_descuento_display()} ({self.valor})"