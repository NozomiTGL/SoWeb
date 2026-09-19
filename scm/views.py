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

# ==========================================
# EDICIÓN Y ELIMINACIÓN DE PROVEEDORES
# ==========================================
@login_required
def editar_proveedor(request, id):
    proveedor = get_object_or_404(Proveedor, id=id)
    if request.method == 'POST':
        form = ProveedorForm(request.POST, instance=proveedor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Proveedor actualizado con éxito.')
            return redirect('lista_proveedores')
    else:
        form = ProveedorForm(instance=proveedor)
    
    return render(request, 'scm/form_proveedor.html', {'form': form, 'titulo': 'Editar Proveedor'})

@login_required
def eliminar_proveedor(request, id):
    proveedor = get_object_or_404(Proveedor, id=id)
    if request.method == 'POST':
        if proveedor.productos.exists():
            messages.error(request, 'No puedes eliminar este proveedor porque tiene servicios asociados.')
        else:
            proveedor.delete()
            messages.success(request, 'Proveedor eliminado con éxito.')
        return redirect('lista_proveedores')
    
    return render(request, 'scm/confirmar_eliminacion.html', {
        'objeto': proveedor.nombre, 'tipo': 'Proveedor', 'url_cancelar': 'lista_proveedores'
    })

# ==========================================
# EDICIÓN Y ELIMINACIÓN DE PRODUCTOS/SERVICIOS
# ==========================================
@login_required
def editar_producto(request, id):
    producto = get_object_or_404(Producto, id=id)
    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Servicio actualizado con éxito.')
            return redirect('lista_productos')
    else:
        form = ProductoForm(instance=producto)
    
    return render(request, 'scm/form_producto.html', {'form': form, 'titulo': 'Editar Servicio'})

@login_required
def eliminar_producto(request, id):
    producto = get_object_or_404(Producto, id=id)
    if request.method == 'POST':
        producto.delete()
        messages.success(request, 'Servicio eliminado con éxito.')
        return redirect('lista_productos')
    
    return render(request, 'scm/confirmar_eliminacion.html', {
        'objeto': producto.nombre, 'tipo': 'Servicio', 'url_cancelar': 'lista_productos'
    })