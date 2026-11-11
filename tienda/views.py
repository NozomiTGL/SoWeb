from django.shortcuts import render
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from scm.models import Producto
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from scm.models import Producto
from .models import Carrito, CarritoDetalle
from erp.models import OrdenEmpresarial
from crm.models import Cliente
from django.db import transaction
from .models import Carrito, CarritoDetalle, Monedero, CodigoRecarga
from .models import Carrito, CarritoDetalle, Monedero, MovimientoMonedero

@login_required
def catalogo_tienda(request):
    """
    Catálogo comercial B2B: Muestra productos activos, permite búsqueda y filtrado[cite: 26].
    """
    # Solo mostramos productos que el admin haya marcado como 'Activos / Visibles'
    productos = Producto.objects.filter(estado=True)
    
    # Lógica de búsqueda por nombre
    query = request.GET.get('q', '')
    if query:
        productos = productos.filter(nombre__icontains=query)
        
    # Lógica de filtrado por categoría
    categoria = request.GET.get('categoria', '')
    if categoria:
        productos = productos.filter(categoria=categoria)

    context = {
        'productos': productos,
        'q': query,
        'categoria_seleccionada': categoria,
        'categorias': Producto.CATEGORIA_CHOICES, # Para pintar los botones de filtro
    }
    return render(request, 'tienda/catalogo.html', context)

@login_required
def agregar_al_carrito(request):
    """
    Añade un producto al carrito único del usuario.
    """
    if request.method == 'POST':
        producto_id = request.POST.get('producto_id')
        producto = get_object_or_404(Producto, id=producto_id)
        
        if producto.stock_actual <= 0:
            messages.error(request, f"Lo sentimos, {producto.nombre} está agotado.")
            return redirect('catalogo_tienda')

        # Obtener o reutilizar el carrito del usuario
        carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
        if carrito.estado != 'Activo':
            carrito.estado = 'Activo'
            carrito.save()
        
        item, item_created = CarritoDetalle.objects.get_or_create(
            carrito=carrito,
            producto=producto,
            defaults={'cantidad': 1}
        )
        
        if not item_created:
            if item.cantidad < producto.stock_actual:
                item.cantidad += 1
                item.save()
                messages.success(request, f"Se agregó otra unidad de {producto.nombre} a tu carrito.")
            else:
                messages.warning(request, f"No puedes agregar más de {producto.stock_actual} unidades de este servicio.")
        else:
            messages.success(request, f"{producto.nombre} agregado al carrito.")
            
    return redirect('catalogo_tienda')


@login_required
def ver_carrito(request):
    """
    Muestra la pantalla del carrito de compras.
    """
    # Obtener el carrito único por usuario
    carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
    if carrito.estado != 'Activo':
        carrito.estado = 'Activo'
        carrito.save()

    detalles = carrito.detalles.all()
    subtotal_carrito = sum(item.subtotal for item in detalles)
    
    context = {
        'carrito': carrito,
        'detalles': detalles,
        'subtotal_carrito': subtotal_carrito,
    }
    return render(request, 'tienda/carrito.html', context)


@login_required
def eliminar_item_carrito(request, item_id):
    """
    Elimina un producto completo del carrito[cite: 19].
    """
    item = get_object_or_404(CarritoDetalle, id=item_id, carrito__usuario=request.user)
    nombre_producto = item.producto.nombre
    item.delete()
    messages.info(request, f"{nombre_producto} eliminado del carrito.")
    return redirect('ver_carrito')


@login_required
def vaciar_carrito(request):
    """
    Vacía completamente el carrito del usuario[cite: 19].
    """
    carrito = get_object_or_404(Carrito, usuario=request.user, estado='Activo')
    carrito.detalles.all().delete()
    messages.success(request, "Tu carrito ha sido vaciado.")
    return redirect('ver_carrito')

@login_required
def ver_monedero(request):
    """
    Muestra el saldo actual del cliente y permite recargarlo por código o tarjeta.
    """
    monedero, _ = Monedero.objects.get_or_create(usuario=request.user)
    return render(request, 'tienda/monedero.html', {'monedero': monedero})


@login_required
def recargar_monedero(request):
    """
    Procesa la recarga de saldo e historial de movimientos.
    """
    if request.method == 'POST':
        codigo = request.POST.get('codigo_promo', '').strip().upper()
        monto_custom = request.POST.get('monto_custom')
        
        monedero, _ = Monedero.objects.get_or_create(usuario=request.user)
        monto_recargado = Decimal('0.00')

        codigos_validos = {
            'SOWEB500': Decimal('500.00'),
            'SOWEB1000': Decimal('1000.00'),
            'RECARGA1000': Decimal('1000.00'),
            'PROMO2026': Decimal('2000.00'),
            'SOWEB100': Decimal('100.00'),
        }

        if codigo in codigos_validos:
            monto_recargado = codigos_validos[codigo]
            descripcion_mov = f"Recarga con código promocional: {codigo}"
        elif monto_custom:
            try:
                monto_recargado = Decimal(monto_custom)
                if monto_recargado <= 0:
                    messages.error(request, "Ingrese un monto mayor a cero.")
                    return redirect('ver_monedero')
                descripcion_mov = "Recarga de saldo con tarjeta/método simulado"
            except Exception:
                messages.error(request, "Monto de recarga no válido.")
                return redirect('ver_monedero')
        else:
            messages.error(request, "Ingresa un código promocional válido o especifica un monto.")
            return redirect('ver_monedero')

        monedero.saldo_actual += monto_recargado
        monedero.save()

        # Registrar movimiento en el historial
        MovimientoMonedero.objects.create(
            monedero=monedero,
            tipo='Recarga',
            monto=monto_recargado,
            descripcion=descripcion_mov
        )

        messages.success(request, f"¡Recarga exitosa! Se han acreditado ${monto_recargado:.2f} a tu monedero.")
        
    return redirect('ver_monedero')


@login_required
def checkout(request):
    """
    Muestra la pantalla de checkout.
    """
    carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
    detalles = carrito.detalles.all()

    if not detalles.exists():
        messages.warning(request, "Tu carrito está vacío.")
        return redirect('catalogo_tienda')

    monedero, _ = Monedero.objects.get_or_create(usuario=request.user)
    subtotal = sum(item.subtotal for item in detalles)

    context = {
        'carrito': carrito,
        'detalles': detalles,
        'subtotal': subtotal,
        'monedero': monedero,
    }
    return render(request, 'tienda/checkout.html', context)


@login_required
@transaction.atomic
def procesar_compra(request):
    """
    Procesa la compra admitiendo múltiples medios de pago (Monedero, Tarjeta, PayPal y Mixto)
    e integra el registro en el historial de movimientos del monedero.
    """
    if request.method != 'POST':
        return redirect('checkout')

    carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
    detalles = carrito.detalles.all()

    if not detalles.exists():
        messages.error(request, "No hay productos para procesar.")
        return redirect('catalogo_tienda')

    metodo_pago = request.POST.get('metodo_pago')
    subtotal = sum(item.subtotal for item in detalles)
    monedero, _ = Monedero.objects.get_or_create(usuario=request.user)

    monto_monedero_usado = Decimal('0.00')
    monto_tarjeta_usado = Decimal('0.00')
    monto_paypal_usado = Decimal('0.00')

    # Validaciones según método de pago elegido
    if metodo_pago == 'monedero':
        if monedero.saldo_actual < subtotal:
            messages.error(request, "Saldo insuficiente en tu monedero virtual. Elige otro método de pago o recarga saldo.")
            return redirect('checkout')
        monto_monedero_usado = subtotal

    elif metodo_pago == 'tarjeta':
        num_tarjeta = request.POST.get('num_tarjeta', '').replace(' ', '')
        if len(num_tarjeta) != 16:
            messages.error(request, "Error de transacción simulada: Ingrese un número de tarjeta válido (16 dígitos).")
            return redirect('checkout')
        monto_tarjeta_usado = subtotal

    elif metodo_pago == 'paypal':
        email_paypal = request.POST.get('email_paypal', '').strip()
        if not email_paypal or '@' not in email_paypal:
            messages.error(request, "Error de transacción simulada: Ingrese un correo electrónico de PayPal válido.")
            return redirect('checkout')
        monto_paypal_usado = subtotal

    elif metodo_pago == 'mixto':
        if monedero.saldo_actual <= 0:
            messages.error(request, "No tienes saldo en el monedero para realizar pago mixto.")
            return redirect('checkout')
        
        monto_monedero_usado = min(monedero.saldo_actual, subtotal)
        monto_tarjeta_usado = subtotal - monto_monedero_usado

        num_tarjeta = request.POST.get('num_tarjeta_mixto', '').replace(' ', '')
        if len(num_tarjeta) != 16:
            messages.error(request, "Ingrese una tarjeta válida para cubrir el saldo restante.")
            return redirect('checkout')
    else:
        messages.error(request, "Seleccione un método de pago válido.")
        return redirect('checkout')

    # Descuento del Monedero si se utilizó + Registro en Historial
    if monto_monedero_usado > 0:
        monedero.saldo_actual -= monto_monedero_usado
        monedero.save()

        # Registro en el historial de movimientos
        MovimientoMonedero.objects.create(
            monedero=monedero,
            tipo='Compra',
            monto=monto_monedero_usado,
            descripcion="Consumo por compra en tienda"
        )

    # Descuento de stock en SCM
    for item in detalles:
        item.producto.stock_actual -= item.cantidad
        item.producto.save()

    # Obtener perfil del cliente (CRM)
    cliente_obj = Cliente.objects.filter(usuario_login=request.user).first()
    if not cliente_obj:
        messages.error(request, "No se encontró un perfil de Cliente asociado a tu cuenta.")
        return redirect('checkout')

    # Registrar Orden en ERP
    orden = OrdenEmpresarial.objects.create(
        cliente=cliente_obj,
        total=subtotal,
        estado='Procesada' if hasattr(OrdenEmpresarial, 'estado') else 'Pendiente'
    )

    # Vaciar los detalles del carrito y restablecer estado
    carrito.detalles.all().delete()
    carrito.estado = 'Activo'
    carrito.save()

    # Formatear métodos usados para el mensaje final
    metodos_usados = []
    if monto_monedero_usado > 0:
        metodos_usados.append(f"Monedero: ${monto_monedero_usado:.2f}")
    if monto_tarjeta_usado > 0:
        metodos_usados.append(f"Tarjeta: ${monto_tarjeta_usado:.2f}")
    if monto_paypal_usado > 0:
        metodos_usados.append(f"PayPal: ${monto_paypal_usado:.2f}")

    resumen_pago = " | ".join(metodos_usados)

    messages.success(
        request, 
        f"¡Compra completada con éxito! Orden #{orden.id} generada. ({resumen_pago})"
    )
    return redirect('catalogo_tienda')


@login_required
def mis_pedidos(request):
    """
    Consulta y muestra el historial de órdenes del cliente autenticado.
    """
    cliente_obj = Cliente.objects.filter(usuario_login=request.user).first()
    
    if cliente_obj:
        ordenes = OrdenEmpresarial.objects.filter(cliente=cliente_obj).order_by('-id')
    else:
        ordenes = []

    context = {
        'ordenes': ordenes
    }
    return render(request, 'tienda/mis_pedidos.html', context)

@login_required
def detalle_orden(request, orden_id):
    """
    Despliega el comprobante detallado de una orden específica.
    """
    cliente_obj = get_object_or_404(Cliente, usuario_login=request.user)
    orden = get_object_or_404(OrdenEmpresarial, id=orden_id, cliente=cliente_obj)

    context = {
        'orden': orden
    }
    return render(request, 'tienda/detalle_orden.html', context)

@login_required
def historial_monedero(request):
    """
    Despliega el historial completo de recargas y consumos del monedero.
    """
    monedero, _ = Monedero.objects.get_or_create(usuario=request.user)
    movimientos = monedero.movimientos.all()

    context = {
        'monedero': monedero,
        'movimientos': movimientos
    }
    return render(request, 'tienda/historial_monedero.html', context)