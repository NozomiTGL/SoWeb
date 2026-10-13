from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.contrib import messages
from crm.models import Cliente
from scm.models import Producto, MovimientoInventario
from .models import EstadoERP, OrdenEmpresarial, DetalleOrden

@login_required
def lista_ordenes(request):
    """Pantalla principal del ERP: Lista de órdenes procesadas."""
    ordenes = OrdenEmpresarial.objects.all().select_related('cliente')
    return render(request, 'erp/lista_ordenes.html', {'ordenes': ordenes})

@login_required
def nueva_orden_paso1(request):
    """Paso 1: Seleccionar el cliente del CRM."""
    clientes = Cliente.objects.filter(estado='activo').order_by('nombre')
    
    if request.method == 'POST':
        cliente_id = request.POST.get('cliente_id')
        if cliente_id:
            # Guardamos el cliente en la memoria temporal (sesión)
            request.session['erp_cliente_id'] = cliente_id
            request.session['erp_carrito'] = {}  # Inicializamos el carrito vacío
            return redirect('nueva_orden_paso2')
        else:
            messages.error(request, 'Debes seleccionar un cliente para continuar.')
            
    return render(request, 'erp/paso1_cliente.html', {'clientes': clientes})

@login_required
def nueva_orden_paso2(request):
    """Paso 2: Agregar productos del SCM al carrito."""
    # Verificamos que no se hayan saltado el Paso 1
    if 'erp_cliente_id' not in request.session:
        return redirect('nueva_orden_paso1')

    productos = Producto.objects.all().order_by('categoria', 'nombre')
    carrito = request.session.get('erp_carrito', {})

    if request.method == 'POST':
        producto_id = request.POST.get('producto_id')
        cantidad = int(request.POST.get('cantidad', 1))
        
        # Validamos que haya stock suficiente para agregarlo
        producto_obj = get_object_or_404(Producto, id=producto_id)
        if cantidad > producto_obj.stock_actual:
            messages.error(request, f'Stock insuficiente para {producto_obj.nombre}. Solo quedan {producto_obj.stock_actual}.')
        else:
            # Agregamos o actualizamos la cantidad en el carrito
            carrito[producto_id] = cantidad
            request.session['erp_carrito'] = carrito
            messages.success(request, f'{producto_obj.nombre} agregado a la orden.')
            
        return redirect('nueva_orden_paso2')

    context = {
        'productos': productos,
        'carrito_items': len(carrito)
    }
    return render(request, 'erp/paso2_productos.html', context)

@login_required
def nueva_orden_paso3(request):
    """Paso 3: Resumen y confirmación de la orden."""
    cliente_id = request.session.get('erp_cliente_id')
    carrito = request.session.get('erp_carrito', {})

    if not cliente_id or not carrito:
        messages.warning(request, 'Tu orden está incompleta. Agrega productos.')
        return redirect('nueva_orden_paso2')

    cliente = get_object_or_404(Cliente, id=cliente_id)
    
    # Reconstruimos los datos del carrito para mostrarlos
    items_resumen = []
    total_orden = 0
    
    for prod_id, cantidad in carrito.items():
        producto = Producto.objects.get(id=prod_id)
        subtotal = producto.costo_unitario * cantidad
        total_orden += subtotal
        items_resumen.append({
            'producto': producto,
            'cantidad': cantidad,
            'subtotal': subtotal
        })

    context = {
        'cliente': cliente,
        'items': items_resumen,
        'total_orden': total_orden
    }
    return render(request, 'erp/paso3_confirmacion.html', context)

@login_required
def procesar_orden(request):
    """
    Motor de Automatización ERP: 
    Crea la orden, descuenta inventario (SCM) y genera historial.
    """
    if request.method == 'POST':
        cliente_id = request.session.get('erp_cliente_id')
        carrito = request.session.get('erp_carrito', {})

        if not cliente_id or not carrito:
            return redirect('lista_ordenes')

        # 1. Crear la Orden
        cliente = Cliente.objects.get(id=cliente_id)
        orden = OrdenEmpresarial.objects.create(
            cliente=cliente,
            usuario=request.user,
            estado='Completada'
        )

        total_orden = 0
        
        # 2. Generar Detalles y Automatizar Inventario
        for prod_id, cantidad in carrito.items():
            producto = Producto.objects.get(id=prod_id)
            subtotal = producto.costo_unitario * cantidad
            total_orden += subtotal

            # Guardar el detalle
            DetalleOrden.objects.create(
                orden=orden,
                producto=producto,
                cantidad=cantidad,
                precio_unitario=producto.costo_unitario
            )

            # Automatización: Registrar Salida en SCM
            MovimientoInventario.objects.create(
                producto=producto,
                tipo='SALIDA',
                cantidad=cantidad,
                motivo='venta',
                usuario=request.user
            )

        # Actualizar total de la orden
        orden.total = total_orden
        orden.save()

        # 3. Limpiar la sesión (vaciar carrito)
        del request.session['erp_cliente_id']
        del request.session['erp_carrito']

        messages.success(request, f'¡Orden {orden.folio} registrada con éxito! El inventario se ha actualizado automáticamente.')
        return redirect('lista_ordenes')
        
    return redirect('lista_ordenes')

@login_required
def dashboard_erp(request):
    """
    Pantalla 9: Dashboard Empresarial.
    Métricas que unifican ventas (ERP), clientes (CRM) y productos (SCM).
    """
    # 1. Cálculos de ventas y órdenes
    ventas_totales = OrdenEmpresarial.objects.filter(estado='Completada').aggregate(Sum('total'))['total__sum'] or 0
    ordenes_procesadas = OrdenEmpresarial.objects.count()
    
    # 2. Métricas cruzadas con CRM y SCM
    clientes_activos = Cliente.objects.filter(estado='activo').count()
    productos_vendidos = DetalleOrden.objects.aggregate(Sum('cantidad'))['cantidad__sum'] or 0
    
    # 3. Top Productos más vendidos
    top_productos = Producto.objects.annotate(
        vendidos=Sum('detalleorden__cantidad')
    ).exclude(vendidos=None).order_by('-vendidos')[:5]

    # 4. Porcentaje simple de inventario disponible (simulado sobre un tope ideal)
    total_stock = Producto.objects.aggregate(Sum('stock_actual'))['stock_actual__sum'] or 0

    context = {
        'ventas_totales': ventas_totales,
        'ordenes_procesadas': ordenes_procesadas,
        'clientes_activos': clientes_activos,
        'productos_vendidos': productos_vendidos,
        'top_productos': top_productos,
        'total_stock': total_stock
    }
    return render(request, 'erp/dashboard_erp.html', context)


@login_required
def nivel_erp(request):
    """
    Pantalla 8: Evaluación del nivel de implementación ERP.
    """
    # Obtenemos el registro de madurez o lo creamos si no existe
    estado, created = EstadoERP.objects.get_or_create(id=1, defaults={'nivel': 'Básico'})
    
    if request.method == 'POST':
        nuevo_nivel = request.POST.get('nivel')
        if nuevo_nivel:
            estado.nivel = nuevo_nivel
            estado.save()
            messages.success(request, f'Nivel de madurez actualizado a: {estado.get_nivel_display()}')
            return redirect('nivel_erp')

    return render(request, 'erp/nivel_erp.html', {'estado': estado})