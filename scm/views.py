from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Proveedor, Producto, MovimientoInventario, Pedido
from .forms import ProveedorForm, ProductoForm, MovimientoInventarioForm, PedidoForm
from django.db.models import F

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


# ==========================================
# MOVIMIENTOS DE INVENTARIO (Fase 2)
# ==========================================
@login_required
def lista_movimientos(request):
    """Muestra el historial de entradas y salidas con filtros de búsqueda."""
    movimientos = MovimientoInventario.objects.all().select_related('producto', 'usuario')
    productos = Producto.objects.all().order_by('nombre') # Necesario para llenar el desplegable de filtros
    
    # 1. Capturar los parámetros que vienen de la URL (ej. ?tipo=ENTRADA&producto=2)
    filtro_tipo = request.GET.get('tipo')
    filtro_producto = request.GET.get('producto')

    # 2. Aplicar los filtros si el usuario seleccionó alguno
    if filtro_tipo:
        movimientos = movimientos.filter(tipo=filtro_tipo)
    if filtro_producto:
        movimientos = movimientos.filter(producto_id=filtro_producto)
        
    context = {
        'movimientos': movimientos,
        'productos': productos,
        'filtro_tipo': filtro_tipo,
        'filtro_producto': filtro_producto,
    }
    
    return render(request, 'scm/lista_movimientos.html', context)

@login_required
def registrar_movimiento(request):
    """Registra una entrada o salida y actualiza el stock automáticamente."""
    if request.method == 'POST':
        form = MovimientoInventarioForm(request.POST)
        if form.is_valid():
            # commit=False nos permite modificar el objeto antes de guardarlo en la BD
            movimiento = form.save(commit=False)
            movimiento.usuario = request.user 
            
            # Candado de seguridad: No permitir salidas mayores al stock disponible
            if movimiento.tipo == 'SALIDA' and movimiento.cantidad > movimiento.producto.stock_actual:
                messages.error(request, f'Error: No hay suficiente capacidad. Stock actual de {movimiento.producto.nombre}: {movimiento.producto.stock_actual}')
            else:
                movimiento.save() # Al hacer .save(), se ejecuta la resta/suma matemática que pusimos en models.py
                messages.success(request, 'Movimiento registrado. El stock del servicio ha sido actualizado.')
                return redirect('lista_movimientos')
    else:
        form = MovimientoInventarioForm()
    
    return render(request, 'scm/form_movimiento.html', {'form': form, 'titulo': 'Registrar Movimiento'})

@login_required
def vista_inventario(request):
    """Pantalla 6: Consulta de existencias y estado de stock."""
    productos = Producto.objects.all().order_by('nombre')
    return render(request, 'scm/inventario.html', {'productos': productos})

# ==========================================
# MÓDULO DE PEDIDOS (Fase 2)
# ==========================================
@login_required
def lista_pedidos(request):
    """Pantalla 11: Gestión de pedidos de reposición o suministro."""
    pedidos = Pedido.objects.all().select_related('producto', 'proveedor')
    
    # Filtros de búsqueda (Estado y Tipo)
    filtro_estado = request.GET.get('estado')
    filtro_tipo = request.GET.get('tipo')
    
    if filtro_estado:
        pedidos = pedidos.filter(estado=filtro_estado)
    if filtro_tipo:
        pedidos = pedidos.filter(tipo=filtro_tipo)
        
    return render(request, 'scm/lista_pedidos.html', {
        'pedidos': pedidos,
        'filtro_estado': filtro_estado,
        'filtro_tipo': filtro_tipo,
    })

@login_required
def crear_pedido(request):
    """Pantalla 12: Registro de un nuevo pedido."""
    if request.method == 'POST':
        form = PedidoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Pedido registrado con éxito.')
            return redirect('lista_pedidos')
    else:
        form = PedidoForm()
    
    return render(request, 'scm/form_pedido.html', {'form': form, 'titulo': 'Nuevo Pedido'})

@login_required
def editar_pedido(request, id):
    pedido = get_object_or_404(Pedido, id=id)
    if request.method == 'POST':
        form = PedidoForm(request.POST, instance=pedido)
        if form.is_valid():
            # Aquí ocurre la magia: Si cambias el estado a "Surtido", 
            # el models.py detectará el cambio y sumará el stock al inventario.
            form.save()
            messages.success(request, 'Pedido actualizado con éxito.')
            return redirect('lista_pedidos')
    else:
        form = PedidoForm(instance=pedido)
    
    return render(request, 'scm/form_pedido.html', {'form': form, 'titulo': 'Editar Pedido'})

@login_required
def eliminar_pedido(request, id):
    pedido = get_object_or_404(Pedido, id=id)
    if request.method == 'POST':
        pedido.delete()
        messages.success(request, 'Pedido eliminado con éxito.')
        return redirect('lista_pedidos')
    
    # Reutilizamos tu plantilla de confirmación genérica
    return render(request, 'scm/confirmar_eliminacion.html', {
        'objeto': f"Pedido {pedido.folio}", 'tipo': 'Pedido', 'url_cancelar': 'lista_pedidos'
    })

@login_required
def estrategia_logistica(request):
    """Pantalla 10: Comparativa Push vs Pull."""
    productos_push = Producto.objects.filter(estrategia='PUSH').order_by('nombre')
    productos_pull = Producto.objects.filter(estrategia='PULL').order_by('nombre')
    
    context = {
        'productos_push': productos_push,
        'productos_pull': productos_pull,
        'total_push': productos_push.count(),
        'total_pull': productos_pull.count(),
    }
    return render(request, 'scm/estrategia_logistica.html', context)

# ==========================================
# DASHBOARD / REPORTES (Fase 2)
# ==========================================
@login_required
def dashboard_scm(request):
    """Pantalla 14: Reportes SCM (Dashboard visual)."""
    # 1. Métricas Globales (KPIs)
    total_productos = Producto.objects.count()
    total_proveedores = Proveedor.objects.count()
    pedidos_proceso = Pedido.objects.filter(estado__in=['Pendiente', 'En proceso']).count()
    
    # 2. Inventario Crítico (Stock actual menor o igual al mínimo)
    inventario_critico = Producto.objects.filter(stock_actual__lte=F('stock_minimo')).order_by('stock_actual')
    total_stock_bajo = inventario_critico.count()

    # 3. Datos para la Gráfica de Estrategia
    total_push = Producto.objects.filter(estrategia='PUSH').count()
    total_pull = Producto.objects.filter(estrategia='PULL').count()

    context = {
        'total_productos': total_productos,
        'total_proveedores': total_proveedores,
        'pedidos_proceso': pedidos_proceso,
        'total_stock_bajo': total_stock_bajo,
        'inventario_critico': inventario_critico,
        'total_push': total_push,
        'total_pull': total_pull,
    }
    return render(request, 'scm/dashboard.html', context)