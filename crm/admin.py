from django.contrib import admin

from django.contrib import admin
from .models import Cliente, Interaccion

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'empresa', 'correo', 'estado', 'etapa_crm', 'fecha_registro')
    list_filter = ('estado', 'etapa_crm')
    search_fields = ('nombre', 'empresa', 'correo')

@admin.register(Interaccion)
class InteraccionAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'tipo', 'usuario', 'fecha')
    list_filter = ('tipo', 'fecha')
    search_fields = ('cliente__nombre', 'descripcion')