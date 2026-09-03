"""
Módulo de Modelos para la aplicación CRM de SoWeb.

Define las entidades principales para la gestión de cartera de clientes,
asignación de vendedores/trabajadores y seguimiento de minutas de interacción.
"""

from django.db import models
from django.contrib.auth.models import User


class Cliente(models.Model):
    """
    Representa a un cliente o prospecto comercial dentro del sistema CRM.
    
    Permite almacenar la información de contacto, la empresa u organización a la que
    pertenece, el estado activo/inactivo de la relación comercial y la etapa
    dentro del embudo de ventas (etapa_crm). Además, soporta la asignación
    de un trabajador/vendedor responsable (RBAC).
    """

    # Opciones de estado operacional del cliente
    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
    ]
    
    # Opciones del ciclo de vida del cliente en el pipeline CRM
    ETAPA_CHOICES = [
        ('prospecto', 'Prospecto'),
        ('activo', 'Activo'),
        ('frecuente', 'Frecuente'),
        ('inactivo', 'Inactivo'),
    ]

    # Vinculación con el usuario del sistema encargado del cliente (Relación 1:N con User)
    vendedor = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='clientes',
        verbose_name="Vendedor asignado"
    )

    # Información básica de contacto y empresa
    nombre = models.CharField(max_length=150, verbose_name="Nombre del contacto")
    correo = models.EmailField(unique=True, verbose_name="Correo electrónico")
    telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono")
    empresa = models.CharField(max_length=150, blank=True, null=True, verbose_name="Empresa / Negocio")
    
    # Atributos de control temporal y segmentación comercial
    fecha_registro = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de registro")
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='activo', verbose_name="Estado")
    etapa_crm = models.CharField(max_length=15, choices=ETAPA_CHOICES, default='prospecto', verbose_name="Etapa CRM")

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['-fecha_registro']  # Orden predeterminado: más recientes primero

    def __str__(self):
        """Devuelve una representación legible del cliente con su empresa asociada."""
        return f"{self.nombre} - {self.empresa or 'Sin empresa'}"


class Interaccion(models.Model):
    """
    Registra el historial de seguimiento, minutas y contactos realizados con un cliente.
    
    Almacena el tipo de comunicación (llamada, correo, reunión), el detalle de la
    conversación y el usuario/trabajador que ejecutó la acción.
    """

    # Vías de comunicación registrables
    TIPO_CHOICES = [
        ('llamada', 'Llamada'),
        ('correo', 'Correo'),
        ('reunion', 'Reunión'),
    ]

    # Claves foráneas: Vinculación con el cliente atendido y el trabajador responsable
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
    
    # Detalle de la interacción realizada
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, verbose_name="Tipo de interacción")
    descripcion = models.TextField(verbose_name="Descripción / Minuta")
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de interacción")

    class Meta:
        verbose_name = "Interacción"
        verbose_name_plural = "Interacciones"
        ordering = ['-fecha']  # Orden predeterminado: interacciones más recientes primero

    def __str__(self):
        """Devuelve una síntesis de la interacción especificando tipo, cliente y fecha."""
        return f"{self.tipo.upper()} con {self.cliente.nombre} - {self.fecha.strftime('%d/%m/%Y')}"