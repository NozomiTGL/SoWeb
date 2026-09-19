from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Proveedor(models.Model):
    """
    Representa a los proveedores de infraestructura tecnológica, licenciamiento 
    o talento externo (Outsourcing/Freelancers) de SoWeb.
    """
    nombre = models.CharField(max_length=150, verbose_name="Nombre del proveedor (Ej. AWS, Hostinger)")
    contacto = models.CharField(max_length=100, verbose_name="Nombre de contacto")
    correo = models.EmailField(unique=True, verbose_name="Correo electrónico")
    telefono = models.CharField(max_length=20, verbose_name="Teléfono")

    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    """
    Representa los servicios empaquetados, licencias o capacidades de servidor de SoWeb.
    El 'stock' simboliza la capacidad operativa disponible (ranuras de desarrollo, 
    espacios en servidor, horas de soporte).
    """
    # Opciones de categoría adaptadas a una agencia TIC
    CATEGORIA_CHOICES = [
        ('hosting', 'Infraestructura y Hosting'),
        ('desarrollo', 'Desarrollo Web / Apps'),
        ('licencias', 'Licencias de Software'),
        ('soporte', 'Horas de Soporte / Mantenimiento'),
    ]

    # Opciones para Estrategia Logística
    ESTRATEGIA_CHOICES = [
        ('PUSH', 'PUSH (Producción/compra anticipada)'),
        ('PULL', 'PULL (Según demanda real)'),
    ]

    nombre = models.CharField(max_length=150, verbose_name="Nombre del servicio/producto")
    descripcion = models.TextField(verbose_name="Descripción")
    categoria = models.CharField(max_length=50, choices=CATEGORIA_CHOICES, verbose_name="Categoría")
    
    # Control de capacidad operativa (Inventario)
    stock_actual = models.IntegerField(default=0, verbose_name="Stock actual (Capacidad disponible)")
    stock_minimo = models.IntegerField(default=0, verbose_name="Stock mínimo (Punto de reorden)")
    
    # Estrategia Logística
    estrategia = models.CharField(
        max_length=10, 
        choices=ESTRATEGIA_CHOICES, 
        default='PUSH', 
        verbose_name="Estrategia Logística"
    )
    
    # Llave foránea hacia el modelo Proveedor
    proveedor = models.ForeignKey(
        Proveedor, 
        on_delete=models.RESTRICT, 
        related_name='productos',
        verbose_name="Proveedor de infraestructura"
    )
    
    costo_unitario = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Costo unitario")

    class Meta:
        verbose_name = "Producto / Servicio"
        verbose_name_plural = "Productos / Servicios"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} (Stock: {self.stock_actual})"


class MovimientoInventario(models.Model):
    """
    Registra las entradas y salidas de capacidad operativa.
    Automatiza la actualización del stock actual del producto asociado.
    """
    TIPO_CHOICES = [
        ('ENTRADA', 'Entrada'),
        ('SALIDA', 'Salida'),
    ]

    MOTIVO_CHOICES = [
        ('venta', 'Venta de Proyecto / Contratación'),
        ('liberacion', 'Liberación de Recursos / Proyecto Terminado'),
        ('reposicion', 'Reposición / Aumento de Capacidad'),
        ('ajuste', 'Ajuste Manual'),
    ]

    producto = models.ForeignKey(
        Producto, 
        on_delete=models.CASCADE, 
        related_name='movimientos',
        verbose_name="Servicio / Producto"
    )
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, verbose_name="Tipo de movimiento")
    cantidad = models.PositiveIntegerField(verbose_name="Cantidad")
    motivo = models.CharField(max_length=20, choices=MOTIVO_CHOICES, verbose_name="Motivo")
    fecha = models.DateTimeField(default=timezone.now, verbose_name="Fecha del movimiento")
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Usuario responsable")

    class Meta:
        verbose_name = "Movimiento de Inventario"
        verbose_name_plural = "Movimientos de Inventario"
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.tipo} - {self.producto.nombre} ({self.cantidad})"

    def save(self, *args, **kwargs):
        """
        Sobrescribimos el método save para actualizar el stock del producto
        automáticamente al registrar un movimiento nuevo.
        """
        # Solo actualizamos el stock si es un registro nuevo (no una edición)
        is_new = self.pk is None 
        
        super().save(*args, **kwargs) # Guardamos el movimiento primero

        if is_new:
            if self.tipo == 'ENTRADA':
                self.producto.stock_actual += self.cantidad
            elif self.tipo == 'SALIDA':
                self.producto.stock_actual -= self.cantidad
            
            self.producto.save() # Guardamos el nuevo stock en el producto

