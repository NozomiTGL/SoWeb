from django import forms
from .models import Proveedor, Producto, MovimientoInventario, Pedido

class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ['nombre', 'contacto', 'correo', 'telefono']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control bg-light', 'placeholder': 'Ej. AWS, Hostinger'}),
            'contacto': forms.TextInput(attrs={'class': 'form-control bg-light', 'placeholder': 'Nombre del contacto'}),
            'correo': forms.EmailInput(attrs={'class': 'form-control bg-light', 'placeholder': 'correo@proveedor.com'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control bg-light', 'placeholder': 'Teléfono'}),
        }

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['nombre', 'descripcion', 'categoria', 'stock_actual', 'stock_minimo', 'proveedor', 'costo_unitario', 'estrategia']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control bg-light', 'placeholder': 'Ej. Hosting Básico'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control bg-light', 'rows': 2}),
            'categoria': forms.Select(attrs={'class': 'form-select bg-light'}),
            'stock_actual': forms.NumberInput(attrs={'class': 'form-control bg-light'}),
            'stock_minimo': forms.NumberInput(attrs={'class': 'form-control bg-light'}),
            'proveedor': forms.Select(attrs={'class': 'form-select bg-light'}),
            'costo_unitario': forms.NumberInput(attrs={'class': 'form-control bg-light', 'step': '0.01'}),'estrategia': forms.Select(attrs={'class': 'form-select'}),
        }

class MovimientoInventarioForm(forms.ModelForm):
    class Meta:
        model = MovimientoInventario
        fields = ['producto', 'tipo', 'cantidad', 'motivo']
        widgets = {
            'producto': forms.Select(attrs={'class': 'form-select bg-light'}),
            'tipo': forms.Select(attrs={'class': 'form-select bg-light'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control bg-light', 'min': '1'}),
            'motivo': forms.Select(attrs={'class': 'form-select bg-light'}),
        }

class PedidoForm(forms.ModelForm):
    class Meta:
        model = Pedido
        # No incluimos 'folio' porque se genera automáticamente
        fields = ['producto', 'cantidad', 'tipo', 'proveedor', 'fecha', 'estado', 'notas']
        widgets = {
            'producto': forms.Select(attrs={'class': 'form-select bg-light'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control bg-light', 'min': '1'}),
            'tipo': forms.Select(attrs={'class': 'form-select bg-light'}),
            'proveedor': forms.Select(attrs={'class': 'form-select bg-light'}),
            'fecha': forms.DateInput(attrs={'class': 'form-control bg-light', 'type': 'date'}),
            'estado': forms.Select(attrs={'class': 'form-select bg-light'}),
            'notas': forms.Textarea(attrs={'class': 'form-control bg-light', 'rows': 3, 'placeholder': 'Notas adicionales...'}),
        }