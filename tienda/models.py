from django.db import models
from django.contrib.auth.models import User
from scm.models import Producto

class Monedero(models.Model):
    """
    Controla el saldo a favor del cliente para realizar compras en la plataforma[cite: 36, 37].
    """
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='monedero', verbose_name="Usuario/Cliente")
    saldo_actual = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Saldo Disponible")
    ultima_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Monedero"
        verbose_name_plural = "Monederos"

    def __str__(self):
        return f"Monedero de {self.usuario.username} | Saldo: ${self.saldo_actual}"


class Carrito(models.Model):
    """
    Gestión temporal de productos seleccionados por el cliente antes de la compra[cite: 28].
    """
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='carrito', verbose_name="Cliente")
    estado = models.CharField(max_length=20, default='Activo', verbose_name="Estado del Carrito")
    ultima_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Carrito de Compras"
        verbose_name_plural = "Carritos de Compras"

    def get_total(self):
        # Suma los subtotales de todos los items en el carrito
        return sum(item.subtotal for item in self.detalles.all())

    def __str__(self):
        return f"Carrito de {self.usuario.username}"


class CarritoDetalle(models.Model):
    """
    Asocia un producto específico, su cantidad y precio congelado al Carrito[cite: 28].
    """
    carrito = models.ForeignKey(Carrito, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, verbose_name="Producto (SCM)")
    cantidad = models.PositiveIntegerField(default=1, verbose_name="Cantidad")
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio Unitario (Congelado)")

    class Meta:
        verbose_name = "Item del Carrito"
        verbose_name_plural = "Items del Carrito"

    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario

    def save(self, *args, **kwargs):
        # Al guardar el item en el carrito, congelamos el precio YA CON IVA
        # para que quede fijo en esta transacción.
        if not self.precio_unitario:
            self.precio_unitario = self.producto.precio_con_iva
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre} en Carrito"

class CodigoRecarga(models.Model):
    """
    Códigos o cupones de regalo prepagados para recargar el Monedero Virtual.
    """
    codigo = models.CharField(max_length=30, unique=True, verbose_name="Código de regalo / recarga")
    monto = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Monto ($)")
    usado = models.BooleanField(default=False, verbose_name="¿Ya fue canjeado?")
    usado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='codigos_canjeados')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_canje = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Código de Recarga"
        verbose_name_plural = "Códigos de Recarga"

    def __str__(self):
        estado = "Canjeado" if self.usado else "Disponible"
        return f"{self.codigo} - ${self.monto} ({estado})"

class MovimientoMonedero(models.Model):
    TIPO_CHOICES = (
        ('Recarga', 'Recarga de Saldo'),
        ('Compra', 'Consumo por Compra'),
    )

    monedero = models.ForeignKey(Monedero, on_delete=models.CASCADE, related_name='movimientos')
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    descripcion = models.CharField(max_length=255)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.tipo} - ${self.monto} ({self.monedero.usuario.username})"