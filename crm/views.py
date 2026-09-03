"""
Módulo de Vistas para la aplicación CRM de SoWeb.

Contiene la lógica de negocio para el Dashboard, CRUD de Clientes, 
exportación de reportes CSV, historial de interacciones, métricas de rendimiento 
y administración de trabajadores/usuarios con control de acceso basado en roles (RBAC).
"""

import csv
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import HttpResponse
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Cliente, Interaccion


def es_admin(user):
    """
    Función auxiliar para verificar si un usuario posee privilegios administrativos.
    
    Returns:
        bool: True si el usuario es staff o superusuario, False en caso contrario.
    """
    return user.is_staff or user.is_superuser


# ---------------------------------------------------------
# 1. DASHBOARD E INDICADORES (Métricas CRM)
# ---------------------------------------------------------
@login_required
def dashboard(request):
    """
    Despliega el tablero principal con métricas clave del sistema.
    
    Filtra los datos según el rol del usuario autenticado:
    - Administrador: Visualiza métricas globales.
    - Vendedor: Visualiza métricas exclusivas de su cartera asignada.
    """
    # Consulta condicional según el rol
    if request.user.is_staff:
        clientes_qs = Cliente.objects.all()
    else:
        clientes_qs = Cliente.objects.filter(vendedor=request.user)

    total_clientes = clientes_qs.count()
    activos = clientes_qs.filter(estado='activo').count()
    inactivos = clientes_qs.filter(estado='inactivo').count()
    
    porcentaje_activos = round((activos / total_clientes * 100), 1) if total_clientes > 0 else 0
    
    ahora = timezone.now()
    if request.user.is_staff:
        interacciones_qs = Interaccion.objects.all()
    else:
        interacciones_qs = Interaccion.objects.filter(usuario=request.user)

    # Interacciones acumuladas en el mes en curso
    interacciones_mes = interacciones_qs.filter(
        fecha__year=ahora.year, 
        fecha__month=ahora.month
    ).count()

    # Identificación de clientes sin interacciones registradas
    clientes_riesgo = clientes_qs.annotate(
        num_interacciones=Count('interacciones')
    ).filter(num_interacciones=0)

    context = {
        'total_clientes': total_clientes,
        'activos': activos,
        'inactivos': inactivos,
        'porcentaje_activos': porcentaje_activos,
        'interacciones_mes': interacciones_mes,
        'total_sin_interaccion': clientes_riesgo.count(),
        'clientes_riesgo': clientes_riesgo,
    }
    return render(request, 'crm/dashboard.html', context)


# ---------------------------------------------------------
# 2. GESTIÓN DE CLIENTES (Listado, Búsqueda y Filtros)
# ---------------------------------------------------------
@login_required
def lista_clientes(request):
    """
    Muestra el directorio de clientes con soporte para búsqueda textual,
    filtrado por estado/etapa y paginación de 10 registros por página.
    """
    query = request.GET.get('q', '')
    estado_filter = request.GET.get('estado', '')
    etapa_filter = request.GET.get('etapa', '')

    # Filtro base según el rol
    if request.user.is_staff:
        clientes_list = Cliente.objects.all().order_by('-fecha_registro')
    else:
        clientes_list = Cliente.objects.filter(vendedor=request.user).order_by('-fecha_registro')

    # Aplicación de filtros dinámicos
    if query:
        clientes_list = clientes_list.filter(nombre__icontains=query) | clientes_list.filter(empresa__icontains=query)
    if estado_filter:
        clientes_list = clientes_list.filter(estado=estado_filter)
    if etapa_filter:
        clientes_list = clientes_list.filter(etapa_crm=etapa_filter)

    # Paginación
    paginator = Paginator(clientes_list, 10)
    page_number = request.GET.get('page')
    clientes = paginator.get_page(page_number)

    context = {
        'clientes': clientes,
        'query': query,
        'estado_filter': estado_filter,
        'etapa_filter': etapa_filter,
    }
    return render(request, 'crm/lista_clientes.html', context)


@login_required
def exportar_clientes_csv(request):
    """
    Genera y descarga un archivo CSV estructurado con la lista de clientes.
    Incluye caracteres BOM UTF-8 para garantizar compatibilidad con Microsoft Excel.
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="Reporte_Clientes_SoWeb.csv"'
    response.write('\ufeff'.encode('utf8'))  # BOM UTF-8

    writer = csv.writer(response)
    writer.writerow(['ID', 'Vendedor Asignado', 'Nombre', 'Empresa', 'Correo', 'Teléfono', 'Etapa CRM', 'Estado', 'Fecha Registro'])

    if request.user.is_staff:
        clientes = Cliente.objects.all().select_related('vendedor')
    else:
        clientes = Cliente.objects.filter(vendedor=request.user).select_related('vendedor')

    for c in clientes:
        vendedor_nombre = c.vendedor.username if c.vendedor else 'Sin Asignar'
        writer.writerow([c.id, vendedor_nombre, c.nombre, c.empresa, c.correo, c.telefono, c.etapa_crm, c.estado, c.fecha_registro])

    return response


# ---------------------------------------------------------
# 3. ALTA, EDICIÓN Y ELIMINACIÓN DE CLIENTES
# ---------------------------------------------------------
@login_required
def crear_cliente(request):
    """
    Procesa la creación de un nuevo cliente.
    Si el usuario es vendedor, se le asigna automáticamente.
    Si es administrador, permite seleccionar el vendedor responsable.
    """
    vendedores = User.objects.filter(is_active=True) if request.user.is_staff else None

    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        correo = request.POST.get('correo')
        telefono = request.POST.get('telefono')
        empresa = request.POST.get('empresa')
        estado = request.POST.get('estado', 'activo')
        etapa_crm = request.POST.get('etapa_crm', 'prospecto')

        # Determinación de propiedad
        if request.user.is_staff:
            vendedor_id = request.POST.get('vendedor')
            vendedor_obj = User.objects.get(pk=vendedor_id) if vendedor_id else request.user
        else:
            vendedor_obj = request.user

        Cliente.objects.create(
            vendedor=vendedor_obj,
            nombre=nombre,
            correo=correo,
            telefono=telefono,
            empresa=empresa,
            estado=estado,
            etapa_crm=etapa_crm
        )
        messages.success(request, f'El cliente "{nombre}" ha sido registrado con éxito.')
        return redirect('lista_clientes')
    
    return render(request, 'crm/form_cliente.html', {
        'titulo': 'Registrar Cliente',
        'vendedores': vendedores
    })


@login_required
def editar_cliente(request, pk):
    """
    Permite actualizar la información de un cliente existente.
    Garantiza que un vendedor solo pueda modificar clientes de su propia cartera.
    """
    if request.user.is_staff:
        cliente = get_object_or_404(Cliente, pk=pk)
        vendedores = User.objects.filter(is_active=True)
    else:
        cliente = get_object_or_404(Cliente, pk=pk, vendedor=request.user)
        vendedores = None
    
    if request.method == 'POST':
        cliente.nombre = request.POST.get('nombre')
        cliente.correo = request.POST.get('correo')
        cliente.telefono = request.POST.get('telefono')
        cliente.empresa = request.POST.get('empresa')
        cliente.estado = request.POST.get('estado')
        cliente.etapa_crm = request.POST.get('etapa_crm')

        # Reasignación exclusiva para personal Staff
        if request.user.is_staff:
            vendedor_id = request.POST.get('vendedor')
            if vendedor_id:
                cliente.vendedor = User.objects.get(pk=vendedor_id)

        cliente.save()
        messages.success(request, f'La información de "{cliente.nombre}" ha sido actualizada.')
        return redirect('lista_clientes')

    return render(request, 'crm/form_cliente.html', {
        'cliente': cliente,
        'titulo': 'Editar Cliente',
        'vendedores': vendedores
    })


@login_required
def eliminar_cliente(request, pk):
    """
    Elimina un cliente de la base de datos previa validación de permisos sobre el registro.
    """
    if request.user.is_staff:
        cliente = get_object_or_404(Cliente, pk=pk)
    else:
        cliente = get_object_or_404(Cliente, pk=pk, vendedor=request.user)

    if request.method == 'POST':
        nombre = cliente.nombre
        cliente.delete()
        messages.success(request, f'El cliente "{nombre}" ha sido eliminado del sistema.')
        return redirect('lista_clientes')
    
    return redirect('lista_clientes')


# ---------------------------------------------------------
# 4. HISTORIAL DE INTERACCIONES
# ---------------------------------------------------------
@login_required
def historial_cliente(request, pk):
    """
    Muestra la bitácora de minutas/interacciones de un cliente y permite agregar nuevos registros.
    """
    if request.user.is_staff:
        cliente = get_object_or_404(Cliente, pk=pk)
    else:
        cliente = get_object_or_404(Cliente, pk=pk, vendedor=request.user)

    interacciones = cliente.interacciones.all()

    if request.method == 'POST':
        tipo = request.POST.get('tipo')
        descripcion = request.POST.get('descripcion')

        Interaccion.objects.create(
            cliente=cliente,
            usuario=request.user,
            tipo=tipo,
            descripcion=descripcion
        )
        messages.success(request, 'Interacción registrada en el historial.')
        return redirect('historial_cliente', pk=pk)

    context = {
        'cliente': cliente,
        'interacciones': interacciones,
    }
    return render(request, 'crm/historial_cliente.html', context)


# ---------------------------------------------------------
# 5. DETALLE DEL CLIENTE Y CAMBIO RÁPIDO DE ETAPA
# ---------------------------------------------------------
@login_required
def detalle_cliente(request, pk):
    """
    Muestra la vista detallada de un cliente y permite actualizar su etapa en el funnel rápidamente.
    """
    if request.user.is_staff:
        cliente = get_object_or_404(Cliente, pk=pk)
    else:
        cliente = get_object_or_404(Cliente, pk=pk, vendedor=request.user)
    
    if request.method == 'POST':
        nueva_etapa = request.POST.get('etapa_crm')
        if nueva_etapa:
            cliente.etapa_crm = nueva_etapa
            cliente.save()
            messages.success(request, f'Etapa de {cliente.nombre} actualizada a {cliente.get_etapa_crm_display()}.')
            return redirect('detalle_cliente', pk=pk)

    context = {
        'cliente': cliente,
        'total_interacciones': cliente.interacciones.count(),
        'ultima_interaccion': cliente.interacciones.first()
    }
    return render(request, 'crm/detalle_cliente.html', context)


# ---------------------------------------------------------
# 6. MI ACTIVIDAD (Interacciones con filtro de fechas)
# ---------------------------------------------------------
@login_required
def mi_actividad(request):
    """
    Despliega el registro individual de interacciones realizadas por el usuario autenticado,
    con soporte para filtrado por rango de fechas.
    """
    actividades = Interaccion.objects.filter(usuario=request.user).select_related('cliente')
    
    fecha_inicio = request.GET.get('fecha_inicio', '')
    fecha_fin = request.GET.get('fecha_fin', '')

    if fecha_inicio:
        actividades = actividades.filter(fecha__date__gte=fecha_inicio)
    if fecha_fin:
        actividades = actividades.filter(fecha__date__lte=fecha_fin)

    context = {
        'actividades': actividades,
        'total_actividades': actividades.count(),
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    }
    return render(request, 'crm/mi_actividad.html', context)


# ---------------------------------------------------------
# 7. REPORTES Y MÉTRICAS DE RENDIMIENTO (con Tendencias)
# ---------------------------------------------------------
@login_required
def reportes_metricas(request):
    """
    Genera métricas consolidadas, comparativas intermensuales y desgloses
    por tipo de comunicación y etapa CRM para la generación de gráficas.
    """
    if request.user.is_staff:
        clientes_qs = Cliente.objects.all()
        interacciones_qs = Interaccion.objects.all()
    else:
        clientes_qs = Cliente.objects.filter(vendedor=request.user)
        interacciones_qs = Interaccion.objects.filter(usuario=request.user)

    total_clientes = clientes_qs.count()
    activos = clientes_qs.filter(estado='activo').count()
    
    # Cálculo de rangos mensuales
    ahora = timezone.now()
    primer_dia_mes_actual = ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    ultimo_dia_mes_anterior = primer_dia_mes_actual - timedelta(days=1)
    primer_dia_mes_anterior = ultimo_dia_mes_anterior.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Comparativa de interacciones acumuladas
    interacciones_mes = interacciones_qs.filter(fecha__gte=primer_dia_mes_actual).count()
    interacciones_mes_anterior = interacciones_qs.filter(
        fecha__gte=primer_dia_mes_anterior, 
        fecha__lt=primer_dia_mes_actual
    ).count()

    if interacciones_mes_anterior > 0:
        var_interacciones = round(((interacciones_mes - interacciones_mes_anterior) / interacciones_mes_anterior) * 100, 1)
    else:
        var_interacciones = 100.0 if interacciones_mes > 0 else 0.0

    # Comparativa de captación de nuevos clientes
    clientes_mes = clientes_qs.filter(fecha_registro__gte=primer_dia_mes_actual).count()
    clientes_mes_anterior = clientes_qs.filter(
        fecha_registro__gte=primer_dia_mes_anterior, 
        fecha_registro__lt=primer_dia_mes_actual
    ).count()

    if clientes_mes_anterior > 0:
        var_clientes = round(((clientes_mes - clientes_mes_anterior) / clientes_mes_anterior) * 100, 1)
    else:
        var_clientes = 100.0 if clientes_mes > 0 else 0.0

    clientes_riesgo = clientes_qs.annotate(num_interacciones=Count('interacciones')).filter(num_interacciones=0)
    total_sin_interaccion = clientes_riesgo.count()

    # Conteos agrupados para renderizado visual
    llamadas = interacciones_qs.filter(tipo='llamada').count()
    correos = interacciones_qs.filter(tipo='correo').count()
    reuniones = interacciones_qs.filter(tipo='reunion').count()

    prospectos = clientes_qs.filter(etapa_crm='prospecto').count()
    etapa_activos = clientes_qs.filter(etapa_crm='activo').count()
    frecuentes = clientes_qs.filter(etapa_crm='frecuente').count()
    etapa_inactivos = clientes_qs.filter(etapa_crm='inactivo').count()

    context = {
        'total_clientes': total_clientes,
        'activos': activos,
        'interacciones_mes': interacciones_mes,
        'total_sin_interaccion': total_sin_interaccion,
        'clientes_mes': clientes_mes,
        'var_interacciones': var_interacciones,
        'var_clientes': var_clientes,
        'llamadas': llamadas,
        'correos': correos,
        'reuniones': reuniones,
        'prospectos': prospectos,
        'etapa_activos': etapa_activos,
        'frecuentes': frecuentes,
        'etapa_inactivos': etapa_inactivos,
    }
    return render(request, 'crm/reportes.html', context)


# ---------------------------------------------------------
# 8. REGISTRO PÚBLICO DE USUARIOS
# ---------------------------------------------------------
def registrar_usuario(request):
    """
    Permite el autoregistro de usuarios mediante el formulario estándar de Django.
    """
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuario registrado con éxito. Ya puedes iniciar sesión.')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


# ---------------------------------------------------------
# 9. GESTIÓN DE TRABAJADORES / USUARIOS (Exclusivo Administradores)
# ---------------------------------------------------------
@login_required
@user_passes_test(es_admin)
def lista_usuarios(request):
    """
    Muestra la lista de cuentas de usuario/trabajadores del sistema.
    Acceso restringido a Administradores.
    """
    usuarios = User.objects.all().order_by('-date_joined')
    return render(request, 'crm/lista_usuarios.html', {'usuarios': usuarios})


@login_required
@user_passes_test(es_admin)
def crear_usuario(request):
    """
    Permite a un administrador dar de alta un nuevo trabajador con asignar roles (staff).
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        es_staff = request.POST.get('is_staff') == 'on'

        if User.objects.filter(username=username).exists():
            messages.error(request, f'El nombre de usuario "{username}" ya está registrado.')
        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                is_staff=es_staff
            )
            messages.success(request, f'El trabajador "{user.username}" fue creado correctamente.')
            return redirect('lista_usuarios')

    return render(request, 'crm/form_usuario.html', {'titulo': 'Crear Nuevo Trabajador'})


@login_required
@user_passes_test(es_admin)
def editar_usuario(request, pk):
    """
    Permite modificar los datos personales, estado activo/inactivo, rol de staff
    o restablecer la contraseña de un trabajador existente.
    """
    usuario_target = get_object_or_404(User, pk=pk)

    if request.method == 'POST':
        usuario_target.first_name = request.POST.get('first_name')
        usuario_target.last_name = request.POST.get('last_name')
        usuario_target.email = request.POST.get('email')
        usuario_target.is_active = request.POST.get('is_active') == 'on'
        usuario_target.is_staff = request.POST.get('is_staff') == 'on'

        nueva_clave = request.POST.get('password')
        if nueva_clave:
            usuario_target.set_password(nueva_clave)

        usuario_target.save()
        messages.success(request, f'La información del trabajador "{usuario_target.username}" fue actualizada.')
        return redirect('lista_usuarios')

    return render(request, 'crm/form_usuario.html', {'usuario_target': usuario_target, 'titulo': 'Editar Trabajador'})