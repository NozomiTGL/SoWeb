from django.db import models

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

    nombre = models.CharField(max_length=150, verbose_name="Nombre del servicio/producto")
    descripcion = models.TextField(verbose_name="Descripción")
    categoria = models.CharField(max_length=50, choices=CATEGORIA_CHOICES, verbose_name="Categoría")
    
    # Control de capacidad operativa (Inventario)
    stock_actual = models.IntegerField(default=0, verbose_name="Stock actual (Capacidad disponible)")
    stock_minimo = models.IntegerField(default=0, verbose_name="Stock mínimo (Punto de reorden)")
    
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