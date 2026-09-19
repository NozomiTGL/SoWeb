from django import forms
from .models import Proveedor, Producto

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
        fields = ['nombre', 'descripcion', 'categoria', 'stock_actual', 'stock_minimo', 'proveedor', 'costo_unitario']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control bg-light', 'placeholder': 'Ej. Hosting Básico'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control bg-light', 'rows': 2}),
            'categoria': forms.Select(attrs={'class': 'form-select bg-light'}),
            'stock_actual': forms.NumberInput(attrs={'class': 'form-control bg-light'}),
            'stock_minimo': forms.NumberInput(attrs={'class': 'form-control bg-light'}),
            'proveedor': forms.Select(attrs={'class': 'form-select bg-light'}),
            'costo_unitario': forms.NumberInput(attrs={'class': 'form-control bg-light', 'step': '0.01'}),
        }