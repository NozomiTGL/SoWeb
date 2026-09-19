from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Proveedor, Producto
from .forms import ProveedorForm, ProductoForm

# ==========================================
# VISTAS DE PROVEEDORES
# ==========================================
@login_required
def lista_proveedores(request):
    """Muestra el catálogo de proveedores logísticos/tecnológicos."""
    proveedores = Proveedor.objects.all().order_by('nombre')
    return render(request, 'scm/lista_proveedores.html', {'proveedores': proveedores})

@login_required
def crear_proveedor(request):
    """Procesa el formulario para registrar un nuevo proveedor."""
    if request.method == 'POST':
        form = ProveedorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Proveedor registrado con éxito.')
            return redirect('lista_proveedores')
    else:
        form = ProveedorForm()
    
    return render(request, 'scm/form_proveedor.html', {'form': form, 'titulo': 'Nuevo Proveedor'})

# ==========================================
# VISTAS DE PRODUCTOS / SERVICIOS
# ==========================================
@login_required
def lista_productos(request):
    """Muestra el catálogo de productos/servicios y su capacidad disponible."""
    productos = Producto.objects.all().select_related('proveedor').order_by('nombre')
    return render(request, 'scm/lista_productos.html', {'productos': productos})

@login_required
def crear_producto(request):
    """Procesa el formulario para dar de alta un nuevo producto o servicio."""
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Servicio/Producto registrado con éxito.')
            return redirect('lista_productos')
    else:
        form = ProductoForm()
    
    return render(request, 'scm/form_producto.html', {'form': form, 'titulo': 'Nuevo Producto'})