from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum,  Count, F
from django.contrib import messages
from crm.models import Cliente
from scm.models import Producto, MovimientoInventario
from .models import EstadoERP, OrdenEmpresarial, DetalleOrden
import json
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import timedelta

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
    """Paso 2: Agregar o eliminar productos del SCM al carrito."""
    if 'erp_cliente_id' not in request.session:
        return redirect('nueva_orden_paso1')

    productos = Producto.objects.all().order_by('categoria', 'nombre')
    carrito = request.session.get('erp_carrito', {})

    if request.method == 'POST':
        producto_id = request.POST.get('producto_id')
        accion = request.POST.get('accion', 'agregar') # 'agregar' o 'eliminar'
        
        if accion == 'agregar':
            cantidad = int(request.POST.get('cantidad', 1))
            producto_obj = get_object_or_404(Producto, id=producto_id)
            
            if cantidad > producto_obj.stock_actual:
                messages.error(request, f'Stock insuficiente para {producto_obj.nombre}. Solo quedan {producto_obj.stock_actual}.')
            else:
                carrito[producto_id] = cantidad
                request.session['erp_carrito'] = carrito
                messages.success(request, f'{producto_obj.nombre} agregado a la orden.')
                
        elif accion == 'eliminar':
            if str(producto_id) in carrito:
                del carrito[str(producto_id)]
                request.session['erp_carrito'] = carrito
                messages.info(request, 'Servicio removido de la orden.')
                
        return redirect('nueva_orden_paso2')

    # Reconstruir los detalles del carrito para la vista
    items_carrito = []
    total_carrito = 0
    
    for prod_id, cantidad in carrito.items():
        try:
            producto = Producto.objects.get(id=prod_id)
            subtotal = producto.costo_unitario * cantidad
            total_carrito += subtotal
            items_carrito.append({
                'producto': producto,
                'cantidad': cantidad,
                'subtotal': subtotal
            })
        except Producto.DoesNotExist:
            continue

    context = {
        'productos': productos,
        'carrito_items': len(carrito),
        'items_carrito': items_carrito,
        'total_carrito': total_carrito
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
    Dashboard Empresarial (Pantalla 9): 
    Genera las métricas reales y las inyecta en las gráficas.
    """
    # 1. TARJETAS SUPERIORES (KPIs)
    ventas_totales = OrdenEmpresarial.objects.filter(estado='Completada').aggregate(Sum('total'))['total__sum'] or 0
    ordenes_procesadas = OrdenEmpresarial.objects.filter(estado='Completada').count()
    clientes_activos = Cliente.objects.filter(estado='activo').count()
    productos_vendidos = DetalleOrden.objects.filter(orden__estado='Completada').aggregate(Sum('cantidad'))['cantidad__sum'] or 0

    # 2. GRÁFICA 1: Ventas por mes 
    seis_meses_atras = timezone.now() - timedelta(days=180)
    ventas_mes = OrdenEmpresarial.objects.filter(
        estado='Completada', fecha__gte=seis_meses_atras
    ).annotate(mes=TruncMonth('fecha')).values('mes').annotate(total=Sum('total')).order_by('mes')

    meses_labels = [v['mes'].strftime('%b') for v in ventas_mes]
    meses_data = [float(v['total']) for v in ventas_mes]

    # 3. GRÁFICA 2: Productos más vendidos
    top_productos = Producto.objects.annotate(
        vendidos=Sum('detalleorden__cantidad')
    ).exclude(vendidos=None).order_by('-vendidos')[:5]

    prod_labels = [p.nombre for p in top_productos]
    prod_data = [p.vendidos for p in top_productos]

    # ========================================================
    # 4. GRÁFICA 3: ESTADO DEL INVENTARIO (CÁLCULO 100% REAL)
    # ========================================================
    total_productos = Producto.objects.count()
    if total_productos > 0:
        # Calculamos cuántos productos están bien, en riesgo o agotados
        stock_sano = Producto.objects.filter(stock_actual__gt=F('stock_minimo')).count()
        stock_critico = Producto.objects.filter(stock_actual__lte=F('stock_minimo'), stock_actual__gt=0).count()
        agotados = Producto.objects.filter(stock_actual=0).count()
        
        # El porcentaje del centro será la proporción de catálogo que tiene buen stock
        porcentaje_salud = int((stock_sano / total_productos) * 100)
    else:
        stock_sano, stock_critico, agotados, porcentaje_salud = 0, 0, 0, 0

    rotacion_labels = ['Stock Saludable', 'Stock Crítico', 'Agotados']
    rotacion_data = [stock_sano, stock_critico, agotados]

    context = {
        'ventas_totales': ventas_totales,
        'ordenes_procesadas': ordenes_procesadas,
        'clientes_activos': clientes_activos,
        'productos_vendidos': productos_vendidos,
        
        # El nuevo porcentaje calculado real
        'porcentaje_salud': porcentaje_salud,
        
        # JSON para Chart.js
        'meses_labels': json.dumps(meses_labels),
        'meses_data': json.dumps(meses_data),
        'prod_labels': json.dumps(prod_labels),
        'prod_data': json.dumps(prod_data),
        'rotacion_labels': json.dumps(rotacion_labels),
        'rotacion_data': json.dumps(rotacion_data),
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

@login_required
def dashboard_general(request):
    """
    Pantalla 1: Inicio ERP (Dashboard general)
    Vista integrada del negocio con KPIs rápidos y resúmenes visuales.
    """
    # 1. KPIs Superiores
    clientes_activos = Cliente.objects.filter(estado='activo').count()
    ordenes_clientes = OrdenEmpresarial.objects.filter(estado='Completada').count()
    ventas_totales = OrdenEmpresarial.objects.filter(estado='Completada').aggregate(Sum('total'))['total__sum'] or 0

    # 2. Datos para Gráfica 1: Ventas (Últimos 6 meses)
    seis_meses_atras = timezone.now() - timedelta(days=180)
    ventas_mes = OrdenEmpresarial.objects.filter(
        estado='Completada', fecha__gte=seis_meses_atras
    ).annotate(mes=TruncMonth('fecha')).values('mes').annotate(total=Sum('total')).order_by('mes')

    meses_labels = [v['mes'].strftime('%b') for v in ventas_mes]
    meses_data = [float(v['total']) for v in ventas_mes]

    # Respaldo visual si aún no hay ventas registradas
    if not meses_labels:
        meses_labels = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun']
        meses_data = [8, 14, 32, 12, 34, 42]

    # 3. Datos para Gráfica 2: Productos más vendidos
    top_productos = Producto.objects.annotate(
        vendidos=Sum('detalleorden__cantidad')
    ).exclude(vendidos=None).order_by('-vendidos')[:4]

    prod_labels = [p.nombre for p in top_productos]
    prod_data = [p.vendidos for p in top_productos]

    if not prod_labels:
        prod_labels = ['Vasija de barro', 'Textil bordado', 'Alebrije', 'Collar artesanal']
        prod_data = [45, 38, 25, 18]

    context = {
        'clientes_activos': clientes_activos,
        'ordenes_clientes': ordenes_clientes,
        'ventas_totales': ventas_totales,
        'meses_labels': json.dumps(meses_labels),
        'meses_data': json.dumps(meses_data),
        'prod_labels': json.dumps(prod_labels),
        'prod_data': json.dumps(prod_data),
    }
    return render(request, 'erp/dashboard_general.html', context)