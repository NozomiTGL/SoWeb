from django.db import models
from django.contrib.auth.models import User

class PerfilTrabajador(models.Model):
    """
    Extensión del usuario para manejar roles internos avanzados (RBAC).
    """
    ROL_CHOICES = [
        ('admin', 'Administrador'),
        ('vendedor', 'Vendedor'),
        ('logistica', 'Logística'),
    ]
    usuario = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='perfil_trabajador',
        verbose_name="Usuario Asociado"
    )
    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default='vendedor', verbose_name="Rol Operativo")

    def __str__(self):
        return f"{self.usuario.username} - {self.get_rol_display()}"


class Cliente(models.Model):
    """
    Representa a un cliente o prospecto comercial dentro del sistema CRM.
    """
    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
    ]
    
    ETAPA_CHOICES = [
        ('prospecto', 'Prospecto'),
        ('activo', 'Activo'),
        ('frecuente', 'Frecuente'),
        ('inactivo', 'Inactivo'),
    ]

    # Vinculación con el usuario del sistema encargado del cliente (Vendedor)
    vendedor = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='clientes',
        verbose_name="Vendedor asignado"
    )

    # Vinculación con la cuenta de acceso del propio CLIENTE
    usuario_login = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='perfil_cliente',
        verbose_name="Cuenta de Acceso (Cliente)"
    )

    nombre = models.CharField(max_length=150, verbose_name="Nombre del contacto")
    correo = models.EmailField(unique=True, verbose_name="Correo electrónico")
    telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono")
    empresa = models.CharField(max_length=150, blank=True, null=True, verbose_name="Empresa / Negocio")
    
    fecha_registro = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de registro")
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='activo', verbose_name="Estado")
    etapa_crm = models.CharField(max_length=15, choices=ETAPA_CHOICES, default='prospecto', verbose_name="Etapa CRM")

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['-fecha_registro']

    def __str__(self):
        return f"{self.nombre} | {self.empresa or 'Sin empresa'}"


class Interaccion(models.Model):
    """
    Registra el historial de seguimiento y contactos.
    """
    TIPO_CHOICES = [
        ('llamada', 'Llamada'),
        ('correo', 'Correo'),
        ('reunion', 'Reunión'),
    ]

    cliente = models.ForeignKey(
        Cliente, 
        on_delete=models.CASCADE, 
        related_name='interacciones', 
        verbose_name="Cliente"
    )
    usuario = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        verbose_name="Usuario responsable"
    )
    
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, verbose_name="Tipo de interacción")
    descripcion = models.TextField(verbose_name="Descripción / Minuta")
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de interacción")

    class Meta:
        verbose_name = "Interacción"
        verbose_name_plural = "Interacciones"
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.tipo.upper()} con {self.cliente.nombre} | {self.fecha.strftime('%d/%m/%Y')}"

class TicketSoporte(models.Model):
    ASUNTO_CHOICES = (
        ('Duda sobre mi pedido', 'Duda sobre mi pedido'),
        ('Cambio de producto', 'Cambio de producto'),
        ('Facturación', 'Facturación'),
        ('Soporte Técnico', 'Soporte Técnico'),
        ('Otro', 'Otro asunto'),
    )

    ESTADO_CHOICES = (
        ('En proceso', 'En proceso'),
        ('Respondido', 'Respondido'),
        ('Cerrado', 'Cerrado'),
    )

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tickets')
    asunto = models.CharField(max_length=50, choices=ASUNTO_CHOICES, default='Duda sobre mi pedido')
    mensaje = models.TextField()
    respuesta = models.TextField(blank=True, null=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='En proceso')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"T-{self.id:03d} | {self.asunto} - {self.usuario.username}"