# Imports de biblioteca estándar de Python
import calendar
import json
import random
import csv
from openpyxl import Workbook
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.tokens import default_token_generator
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncMonth
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import urlsafe_base64_decode
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
# Imports de terceros
import openpyxl
from openpyxl.utils import get_column_letter
# Imports de la aplicación productos
from productos.forms import CategoriaForm
from productos.models import Calificacion, CarritoItem, Category, Producto
# Imports de la aplicación actual (usuarios)
from .decorators import admin_required
from .forms import EditarPerfilForm, LoginForm, MensajeForm, UsuarioCreationForm
from .models import Mensaje, Pedido, Usuario, Devolucion, Direccion, HistorialDevolucion
from .utils import enviar_email_activacion
from django.core.mail import send_mail
from django.conf import settings

def register(request):
    return render(request, 'usuarios/register.html')

def nosotros(request):
    return render(request, 'usuarios/nosotros.html')

@admin_required
def dashboard(request):
    tiempo = request.GET.get("tiempo")  # semana, mes, anio, o vacío
    hoy = timezone.now()

    # Base: solo datos desde 2025
    pedidos = Pedido.objects.filter(
        pago=True,
        fecha_creacion__year__gte=2025
    )

    # FILTRO DE TIEMPO
    if tiempo == "semana":
        inicio_semana = hoy - timezone.timedelta(days=hoy.weekday())
        pedidos = pedidos.filter(fecha_creacion__gte=inicio_semana)

    elif tiempo == "mes":
        pedidos = pedidos.filter(
            fecha_creacion__year=hoy.year,
            fecha_creacion__month=hoy.month
        )

    elif tiempo == "anio":
        pedidos = pedidos.filter(
            fecha_creacion__year=hoy.year
        )

    total_ventas = pedidos.aggregate(total=Sum("total"))["total"] or 0

    total_pedidos = pedidos.count()

    prod_info = (
        Producto.objects
        .annotate(
            total_vendidos=Sum(
                "pedidoitem__cantidad",
                filter=Q(pedidoitem__pedido__in=pedidos)
            )
        )
        .filter(total_vendidos__gt=0)
        .order_by("-total_vendidos")
    )

    # Usuarios con más compras
    usuarios_info = (
        Usuario.objects
        .annotate(
            pedidos_pagados=Count(
                "pedido",
                filter=Q(pedido__in=pedidos)
            )
        )
        .filter(pedidos_pagados__gt=0)
        .order_by("-pedidos_pagados")
    )

    ventas_info = (
        pedidos.annotate(mes=TruncMonth("fecha_creacion"))
        .values("mes")
        .annotate(total=Sum("total"))
        .order_by("mes")
    )
    ventas_info = [
        (v["mes"].strftime("%B"), v["total"]) for v in ventas_info
    ]

    estado_info = (
        pedidos.values("estado")
        .annotate(total=Count("id"))
        .order_by("estado")
    )
    estado_info = [(e["estado"], e["total"]) for e in estado_info]

    ultimas_devoluciones = (
        Devolucion.objects.order_by('-fecha_solicitud')[:5]
    )

    # Totales generales (no dependen del filtro)
    total_productos = Producto.objects.count()
    total_usuarios = Usuario.objects.count()

    return render(request, "usuarios/dashboard.html", {
        "prod_info": prod_info,
        "usuarios_info": usuarios_info,
        "total_ventas": total_ventas,
        "total_pedidos": total_pedidos,
        "total_productos": total_productos,
        "total_usuarios": total_usuarios,
        "ventas_info": ventas_info,
        "estado_info": estado_info,
        "ultimas_devoluciones": ultimas_devoluciones,
    })

@admin_required
def gstUsuarios(request):
    usuarios = Usuario.objects.all().order_by('id')  # opcional: ordenados por id
    
    # Paginación
    paginator = Paginator(usuarios, 10)  # 10 usuarios por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, "usuarios/gstUsuarios.html", {
        'page_obj': page_obj,
        'usuarios': page_obj.object_list  # lista de usuarios de la página actual
    })



def exportar_usuarios_excel(request):
    wb = Workbook()
    ws = wb.active
    ws.title = "Usuarios"

    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    from datetime import datetime

    # Encabezado principal de la tienda (NARANJA)
    ws.merge_cells('A1:E1')
    ws['A1'] = 'TIENDA NATURISTA LOS GIRASOLES'
    ws['A1'].font = Font(bold=True, size=16, color='FFFFFF')
    ws['A1'].alignment = Alignment(horizontal='center', vertical='center')
    ws['A1'].fill = PatternFill(start_color='E67E22', end_color='E67E22', fill_type='solid')
    ws.row_dimensions[1].height = 30

    # Subtítulo (NARANJA OSCURO)
    ws.merge_cells('A2:E2')
    ws['A2'] = 'LISTADO DE USUARIOS'
    ws['A2'].font = Font(bold=True, size=12, color='FFFFFF')
    ws['A2'].alignment = Alignment(horizontal='center', vertical='center')
    ws['A2'].fill = PatternFill(start_color='D35400', end_color='D35400', fill_type='solid')
    ws.row_dimensions[2].height = 25

    # Fecha de generación
    ws.merge_cells('A3:E3')
    ws['A3'] = f'Fecha de generación: {datetime.now().strftime("%d/%m/%Y %H:%M")}'
    ws['A3'].font = Font(italic=True, size=10)
    ws['A3'].alignment = Alignment(horizontal='center')
    ws.row_dimensions[3].height = 20

    # Fila vacía
    ws.append([])

    # Encabezados de columnas (fila 5)
    encabezados = ["ID", "Nombre", "Email", "Rol", "Teléfono"]
    ws.append(encabezados)

    # Estilo para encabezados de columnas (AMARILLO)
    header_fill = PatternFill(start_color='F1C40F', end_color='F1C40F', fill_type='solid')
    header_font = Font(bold=True, color='000000')
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    for col in range(1, 6):
        cell = ws.cell(row=5, column=col)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.border = thin_border

    # Datos de usuarios
    row_num = 6
    for u in Usuario.objects.all():
        ws.append([u.id, u.nombre, u.email, u.rol, u.phone_number])
        
        for col in range(1, 6):
            cell = ws.cell(row=row_num, column=col)
            cell.border = thin_border
        
        row_num += 1

    # Ajustar ancho de columnas
    column_widths = [10, 30, 35, 15, 20]
    for i, width in enumerate(column_widths, 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = width

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response['Content-Disposition'] = 'attachment; filename="usuarios.xlsx"'
    wb.save(response)

    return response

def register_view(request):
    if request.method == "POST":
        form = UsuarioCreationForm(request.POST)
        if form.is_valid():
            user = form.save()  # ya se guarda como is_active=False
            enviar_email_activacion(user, request)  # enviamos el correo de activación
            return render(request, "usuarios/confirmacion.html")  # mensaje de revisa tu correo
        else:
            print("❌ Errores del formulario:", form.errors)
    else:
        form = UsuarioCreationForm()
    return render(request, "usuarios/register.html", {"form": form})

def login_view(request):
    mensaje = ""

    if request.GET.get("inactividad") == "1":
        messages.error(request, "Tu sesión fue cerrada por inactividad.")

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            user = authenticate(request, username=email, password=password)
            if user is not None and user.rol == "cliente":
                login(request, user)

                # ✅ sincronizar carrito de sesión con BD
                carrito_sesion = request.session.get("carrito", {})
                for key, value in carrito_sesion.items():
                    producto_id = int(key)
                    cantidad = int(value["cantidad"])
                    producto = Producto.objects.get(id=producto_id)

                    item, creado = CarritoItem.objects.get_or_create(
                        usuario=user, producto=producto,
                        defaults={"cantidad": cantidad}
                    )
                    if not creado:
                        item.cantidad += cantidad
                        item.save()

                # ✅ cargar carrito de BD a la sesión
                carrito_db = CarritoItem.objects.filter(usuario=user)
                carrito_dict = {}
                for item in carrito_db:
                    carrito_dict[str(item.producto.id)] = {
                        "cantidad": item.cantidad,
                        "precio": float(item.producto.precio),
                        "nombProduc": item.producto.nombProduc,
                        "imgProduc": item.producto.imgProduc.url,
                    }
                request.session["carrito"] = carrito_dict
                request.session.modified = True

                return redirect('productos:producto')
            else:
                mensaje = "Correo o contraseña incorrectos o no eres cliente"
    else:
        form = LoginForm()

    return render(request, 'usuarios/login.html', {"form": form, "mensaje": mensaje})

def logout_view(request):
    logout(request)
    request.session.pop("carrito", None)

    if request.GET.get("inactividad") == "1":
        return redirect("/usuarios/login/?inactividad=1")

    return redirect("usuarios:login")

@login_required(login_url='usuarios:login')
def editar_perfil(request):
    user = request.user

    if request.method == 'POST':
        print("🔍 POST recibido")  # Para debug
        print("📦 Datos:", request.POST)  # Para debug
        
        form = EditarPerfilForm(request.POST, instance=user)
        
        if form.is_valid():
            form.save()
            print("✅ Guardado exitoso")  # Para debug
            messages.success(request, "Perfil actualizado correctamente.")
            return redirect('usuarios:editar_perfil')
        else:
            print("❌ Errores:", form.errors)  # Para debug
            messages.error(request, "Hubo errores en el formulario.")
    else:
        form = EditarPerfilForm(instance=user)

    return render(request, 'usuarios/editar_perfil.html', {'form': form})


@login_required(login_url='usuarios:login')
def mis_pedidos(request):
    pedidos = (
        Pedido.objects
        .filter(usuario=request.user, pago=True)  # 👈 Solo los pagados
        .prefetch_related('items__producto')
        .order_by('-fecha_creacion')  # 👈 Los más recientes primero
    )
    return render(request, 'usuarios/mis_pedidos.html', {'pedidos': pedidos})

@admin_required
def cambiar_estado_usuario(request, usuario_id):
    usuario = get_object_or_404(Usuario, id=usuario_id)
    usuario.is_active = not usuario.is_active
    usuario.save()
    return redirect('usuarios:gstUsuarios')  # Cambia si tu ruta tiene otro nombre

@admin_required
def agregar_usuario(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        correo = request.POST.get('email')
        telefono = request.POST.get('phone_number')
        rol = request.POST.get('rol')
        password = request.POST.get('password')  # Asegúrate de tener un input para la contraseña
        # Validar si el email ya existe
        if Usuario.objects.filter(email=correo).exists():
            messages.error(request, 'Ya existe un usuario con ese correo.')
            return render(request, 'usuarios/gstUsuarios.html')
        # Crear usuario usando create_user para manejar contraseña
        Usuario.objects.create_user(
            email=correo,
            nombre=nombre,
            phone_number=telefono,
            rol=rol,
            password=password,
            is_active=True
        )

        messages.success(request, 'Usuario agregado correctamente.')
        return redirect('usuarios:gstUsuarios')

    return render(request, 'usuarios/agregar.html')

@admin_required
def informe_calificaciones(request):
    calificaciones = Calificacion.objects.select_related('usuario', 'producto').all()

    tipo = request.GET.get('tipo')
    desde = request.GET.get('desde')
    hasta = request.GET.get('hasta')

    if tipo:
        calificaciones = calificaciones.filter(servicio__tipo=tipo)
    if desde:
        calificaciones = calificaciones.filter(fecha_creacion__gte=desde)
    if hasta:
        calificaciones = calificaciones.filter(fecha_creacion__lte=hasta)

    # Exportar a Excel
    if request.GET.get('exportar') == 'excel':
        import openpyxl
        from openpyxl import Workbook
        from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
        from datetime import datetime

        wb = Workbook()
        ws = wb.active
        ws.title = "Calificaciones"

        # Encabezado principal de la tienda (NARANJA)
        ws.merge_cells('A1:E1')
        ws['A1'] = 'TIENDA NATURISTA LOS GIRASOLES'
        ws['A1'].font = Font(bold=True, size=16, color='FFFFFF')
        ws['A1'].alignment = Alignment(horizontal='center', vertical='center')
        ws['A1'].fill = PatternFill(start_color='E67E22', end_color='E67E22', fill_type='solid')
        ws.row_dimensions[1].height = 30

        # Subtítulo (NARANJA OSCURO)
        ws.merge_cells('A2:E2')
        ws['A2'] = 'INFORME DE CALIFICACIONES'
        ws['A2'].font = Font(bold=True, size=12, color='FFFFFF')
        ws['A2'].alignment = Alignment(horizontal='center', vertical='center')
        ws['A2'].fill = PatternFill(start_color='D35400', end_color='D35400', fill_type='solid')
        ws.row_dimensions[2].height = 25

        # Fecha de generación
        ws.merge_cells('A3:E3')
        ws['A3'] = f'Fecha de generación: {datetime.now().strftime("%d/%m/%Y %H:%M")}'
        ws['A3'].font = Font(italic=True, size=10)
        ws['A3'].alignment = Alignment(horizontal='center')
        ws.row_dimensions[3].height = 20

        # Fila vacía
        ws.append([])

        # Encabezados de columnas (fila 5)
        encabezados = [
            'Usuario',
            'Puntuación Servicio',
            'Puntuación Producto',
            'Comentario',
            'Fecha'
        ]
        ws.append(encabezados)

        # Estilo para encabezados de columnas (AMARILLO)
        header_fill = PatternFill(start_color='F1C40F', end_color='F1C40F', fill_type='solid')
        header_font = Font(bold=True, color='000000')
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

        for col in range(1, 6):
            cell = ws.cell(row=5, column=col)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.border = thin_border

        # Datos de calificaciones
        row_num = 6
        for c in calificaciones:
            ws.append([
                c.usuario.nombre if c.usuario else 'Anónimo',
                c.puntuacion_servicio,
                c.puntuacion_productos,
                c.comentario,
                c.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            ])

            for col in range(1, 6):
                cell = ws.cell(row=row_num, column=col)
                cell.border = thin_border

            row_num += 1

        # Ajustar ancho de columnas
        column_widths = [25, 20, 20, 40, 20]
        for i, width in enumerate(column_widths, 1):
            ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = width

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="calificaciones.xlsx"'
        wb.save(response)
        return response

    return render(request, 'usuarios/informe_calificaciones.html', {
        'calificaciones': calificaciones
    })

@admin_required
def pedidos_view(request):
    # 🔹 Obtener todos los pedidos pagados (sin filtros excesivos)
    pedidos = (
        Pedido.objects
        .filter(pago=True, total__gt=0)  # ← Añade total > 0 también
        .order_by('-fecha_creacion')
    )

    # 🔹 Paginación
    paginator = Paginator(pedidos, 25)  # 25 pedidos por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # 🔹 Conteos por estado (solo pedidos pagados)
    pedidos_pendientes = Pedido.objects.filter(estado="pendiente", pago=True).count()
    pedidos_enviados = Pedido.objects.filter(estado="enviado", pago=True).count()
    pedidos_entregados = Pedido.objects.filter(estado="entregado", pago=True).count()

    # 🔹 Total pedidos pagados
    total_pedidos = pedidos.count()

    return render(request, "usuarios/gst_pedidos.html", {
        "page_obj": page_obj,
        "pedidos": page_obj.object_list,
        "pedidos_pendientes": pedidos_pendientes,
        "pedidos_enviados": pedidos_enviados,
        "pedidos_entregados": pedidos_entregados,
        "total_pedidos": total_pedidos,
    })


def exportar_pedidos_excel(request):
    import openpyxl
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    from datetime import datetime

    wb = Workbook()
    ws = wb.active
    ws.title = "Pedidos"

    # Encabezado principal (NARANJA)
    ws.merge_cells('A1:F1')
    ws['A1'] = 'TIENDA NATURISTA LOS GIRASOLES'
    ws['A1'].font = Font(bold=True, size=16, color='FFFFFF')
    ws['A1'].alignment = Alignment(horizontal='center', vertical='center')
    ws['A1'].fill = PatternFill(start_color='E67E22', end_color='E67E22', fill_type='solid')
    ws.row_dimensions[1].height = 30

    # Subtítulo (NARANJA OSCURO)
    ws.merge_cells('A2:F2')
    ws['A2'] = 'LISTADO DE PEDIDOS'
    ws['A2'].font = Font(bold=True, size=12, color='FFFFFF')
    ws['A2'].alignment = Alignment(horizontal='center', vertical='center')
    ws['A2'].fill = PatternFill(start_color='D35400', end_color='D35400', fill_type='solid')
    ws.row_dimensions[2].height = 25

    # Fecha de generación
    ws.merge_cells('A3:F3')
    ws['A3'] = f'Fecha de generación: {datetime.now().strftime("%d/%m/%Y %H:%M")}'
    ws['A3'].font = Font(italic=True, size=10)
    ws['A3'].alignment = Alignment(horizontal='center')
    ws.row_dimensions[3].height = 20

    # Fila vacía
    ws.append([])

    # Encabezados de columnas (AMARILLO)
    encabezados = ['ID', 'Cliente', 'Email', 'Fecha', 'Estado', 'Total']
    ws.append(encabezados)

    header_fill = PatternFill(start_color='F1C40F', end_color='F1C40F', fill_type='solid')
    header_font = Font(bold=True, color='000000')
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    for col in range(1, 7):
        cell = ws.cell(row=5, column=col)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.border = thin_border

    # Filtros desde GET
    estado = request.GET.get('estado')
    mes = request.GET.get('mes')
    anio = request.GET.get('anio')

    # Consulta base
    pedidos = Pedido.objects.filter(pago=True).order_by('-fecha_creacion')
    
    if estado:
        pedidos = pedidos.filter(estado=estado)
    if mes:
        pedidos = pedidos.filter(fecha_creacion__month=mes)
    if anio:
        pedidos = pedidos.filter(fecha_creacion__year=anio)

    # Colores por estado
    estado_colors = {
        'pendiente': 'FCF3CF',   # Amarillo claro
        'enviado': 'D6EAF8',     # Azul claro
        'entregado': 'D5F4E6',   # Verde claro
    }

    # Datos
    row_num = 6
    total = 0
    for pedido in pedidos:
        ws.append([
            pedido.id,
            pedido.usuario.nombre if pedido.usuario else 'Sin usuario',
            pedido.usuario.email if pedido.usuario else 'Sin email',
            pedido.fecha_creacion.strftime('%d/%m/%Y %H:%M'),
            pedido.estado.capitalize(),
            float(pedido.total)
        ])
        total += float(pedido.total)

        # Color según estado
        estado_lower = pedido.estado.lower()
        row_fill = PatternFill(
            start_color=estado_colors.get(estado_lower, 'FFFFFF'),
            end_color=estado_colors.get(estado_lower, 'FFFFFF'),
            fill_type='solid'
        )

        for col in range(1, 7):
            cell = ws.cell(row=row_num, column=col)
            cell.border = thin_border
            cell.fill = row_fill
        row_num += 1

    # Fila de total
    ws.append(['', '', '', '', 'TOTAL:', total])
    total_fill = PatternFill(start_color='E67E22', end_color='E67E22', fill_type='solid')
    for col in range(1, 7):
        cell = ws.cell(row=row_num, column=col)
        cell.border = thin_border
        cell.font = Font(bold=True, color='FFFFFF')
        cell.fill = total_fill

    # Ajustar ancho de columnas
    column_widths = [10, 25, 30, 20, 15, 15]
    for i, width in enumerate(column_widths, 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = width

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="pedidos.xlsx"'
    wb.save(response)
    return response

def productos_mas_vendidos_view():
    productos = (
        Producto.objects.annotate(
            total_vendidos=Sum(
                'pedidoitem__cantidad',
                filter=Q(pedidoitem__pedido__pago=True)   # Solo productos de pedidos pagados
            )
        )
        .filter(total_vendidos__gt=0)  # Solo los que realmente se han vendido
        .order_by('-total_vendidos')
    )
    return productos

def usuarios_frecuentes_view(request):
    usuarios = Usuario.objects.annotate(
        num_pedidos=Count('pedido', filter=Q(pedido__pago=True))
    ).order_by('-num_pedidos')

    return render(request, "usuarios/dashboard.html", {
        "usuarios_info": usuarios
    })

def contacto(request):
    # Buscar el usuario específico por email
    try:
        # Buscar por email único de carmen
        usuario_carmen = Usuario.objects.get(email='naturistaoftnatur@gmail.com')
        numero_admin = usuario_carmen.phone_number
    except Usuario.DoesNotExist:
        # Fallback: buscar por username
        try:
            usuario_carmen = Usuario.objects.get(nombre='carmen')
            numero_admin = usuario_carmen.phone_number
        except Usuario.DoesNotExist:
            # Último fallback: cualquier admin
            admin = Usuario.objects.filter(rol="admin").first()
            numero_admin = admin.phone_number if admin else ""
    
    return render(request, "usuarios/contacto.html", {
        "numero_admin": numero_admin
    })

def aprobar_comentario(request, id):
    calificacion = get_object_or_404(Calificacion, id=id)
    calificacion.aprobado = True
    calificacion.save()
    return redirect('usuarios:informe_calificaciones')

def rechazar_comentario(request,id):
    calificacion = get_object_or_404(Calificacion, id=id)
    calificacion.delete()
    return redirect('usuarios:informe_calificaciones')

def informe_ventas(request):
    # 🔹 Tomamos pedidos que ya tengan pago confirmado
    pedidos_list = Pedido.objects.filter(
        pago=True,  # ya fue pagado
        total__gt=0  # que tengan monto
    ).order_by('-fecha_creacion')

    # 🔹 Paginación (25 por página)
    paginator = Paginator(pedidos_list, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # 🔹 Totales
    total_ventas = pedidos_list.aggregate(Sum('total'))['total__sum'] or 0
    total_pedidos = pedidos_list.count()

    # 🔹 Contexto
    context = {
        'page_obj': page_obj,
        'total_ventas': total_ventas,
        'total_pedidos': total_pedidos,
    }

    return render(request, 'usuarios/ventas.html', context)


def exportar_ventas_excel(request):
    import openpyxl
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    from datetime import datetime

    wb = Workbook()
    ws = wb.active
    ws.title = "Ventas"

    # Encabezado principal (NARANJA)
    ws.merge_cells('A1:D1')
    ws['A1'] = 'TIENDA NATURISTA LOS GIRASOLES'
    ws['A1'].font = Font(bold=True, size=16, color='FFFFFF')
    ws['A1'].alignment = Alignment(horizontal='center', vertical='center')
    ws['A1'].fill = PatternFill(start_color='E67E22', end_color='E67E22', fill_type='solid')
    ws.row_dimensions[1].height = 30

    # Subtítulo (NARANJA OSCURO)
    ws.merge_cells('A2:D2')
    ws['A2'] = 'INFORME DE VENTAS'
    ws['A2'].font = Font(bold=True, size=12, color='FFFFFF')
    ws['A2'].alignment = Alignment(horizontal='center', vertical='center')
    ws['A2'].fill = PatternFill(start_color='D35400', end_color='D35400', fill_type='solid')
    ws.row_dimensions[2].height = 25

    # Fecha de generación
    ws.merge_cells('A3:D3')
    ws['A3'] = f'Fecha de generación: {datetime.now().strftime("%d/%m/%Y %H:%M")}'
    ws['A3'].font = Font(italic=True, size=10)
    ws['A3'].alignment = Alignment(horizontal='center')
    ws.row_dimensions[3].height = 20

    # Fila vacía
    ws.append([])

    # Encabezados de columnas (AMARILLO)
    encabezados = ['ID', 'Cliente', 'Fecha', 'Monto']
    ws.append(encabezados)

    header_fill = PatternFill(start_color='F1C40F', end_color='F1C40F', fill_type='solid')
    header_font = Font(bold=True, color='000000')
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    for col in range(1, 5):
        cell = ws.cell(row=5, column=col)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.border = thin_border

    # Filtros desde GET
    mes = request.GET.get('mes')
    anio = request.GET.get('anio')

    # Consulta base
    pedidos = Pedido.objects.filter(pago=True, total__gt=0).order_by('-fecha_creacion')
    
    if mes:
        pedidos = pedidos.filter(fecha_creacion__month=mes)
    if anio:
        pedidos = pedidos.filter(fecha_creacion__year=anio)

    # Datos
    row_num = 6
    total = 0
    for pedido in pedidos:
        ws.append([
            pedido.id,
            pedido.usuario.nombre if pedido.usuario else 'Sin usuario',
            pedido.fecha_creacion.strftime('%d/%m/%Y'),
            float(pedido.total)
        ])
        total += float(pedido.total)

        for col in range(1, 5):
            ws.cell(row=row_num, column=col).border = thin_border
        row_num += 1

    # Fila de total (AMARILLO CLARO)
    ws.append(['', '', 'TOTAL:', total])
    total_fill = PatternFill(start_color='FCF3CF', end_color='FCF3CF', fill_type='solid')
    for col in range(1, 5):
        cell = ws.cell(row=row_num, column=col)
        cell.border = thin_border
        cell.font = Font(bold=True)
        cell.fill = total_fill

    # Ajustar ancho de columnas
    column_widths = [10, 30, 15, 20]
    for i, width in enumerate(column_widths, 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = width

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="informe_ventas.xlsx"'
    wb.save(response)
    return response

User = get_user_model()

def activar_cuenta(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        return render(request, "usuarios/activado.html")
    else:
        return render(request, "usuarios/activacion_invalida.html")
    
def cambiar_estado_pedido(request, pedido_id):
    try:
        data = json.loads(request.body)
        nuevo_estado = data.get('estado')
        
        # Validar estado
        estados_validos = ['pendiente', 'enviado', 'entregado']
        if nuevo_estado not in estados_validos:
            return JsonResponse({'success': False, 'message': 'Estado no válido'})
        
        # Actualizar pedido
        pedido = get_object_or_404(Pedido, id=pedido_id)
        pedido.estado = nuevo_estado
        pedido.save()
        
        return JsonResponse({'success': True, 'message': 'Estado actualizado correctamente'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})
    
def editar_usuario(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)

    if request.method == "POST":
        usuario.nombre = request.POST.get("nombre")
        usuario.email = request.POST.get("email")
        usuario.phone_number = request.POST.get("phone_number")
        usuario.rol = request.POST.get("rol")
        usuario.save()

        messages.success(request, "Usuario actualizado correctamente.")
        return redirect("usuarios:gstUsuarios")  # 👈 ajusta al nombre de tu vista/listado

    messages.error(request, "Método no permitido")
    return redirect("usuarios:gstUsuarios")

User = get_user_model()
@csrf_exempt
def enviar_codigo_verificacion(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            password = data.get('password')
            
            # Verificar credenciales
            user = authenticate(request, username=email, password=password)
            
            if user is None:
                return JsonResponse({
                    'success': False,
                    'mensaje': 'Credenciales incorrectas'
                })
            
            # Generar código de 6 dígitos
            codigo = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            
            # Guardar código en cache por 10 minutos
            cache_key = f'verification_code_{email}'
            cache.set(cache_key, codigo, 600)  # 600 segundos = 10 minutos
            
            # Enviar email con código
            asunto = 'Código de verificación - Unidos pensando en su salud'
            mensaje = f'''
Hola {user.nombre or 'Usuario'},

Tu código de verificación es: {codigo}

Este código expirará en 10 minutos.

Si no solicitaste este código, ignora este mensaje.

Saludos,
Equipo de Unidos pensando en su salud
            '''
            
            send_mail(
                asunto,
                mensaje,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
                html_message=f'''
                <html>
                    <body style="font-family: Arial; color: #333;">
                        <h2 style="color: #0066ff;">Código de verificación</h2>
                        <p>Hola <b>{user.nombre or 'Usuario'}</b>,</p>
                        <p>Tu código de verificación es:</p>
                        <div style="font-size: 22px; font-weight: bold; color: #d93025;">{codigo}</div>
                        <p>Este código expirará en 10 minutos.</p>
                        <p>Si no solicitaste este código, puedes ignorar este correo.</p>
                        <br>
                        <p style="font-size: 14px;">Equipo de <b>Unidos pensando en su salud</b></p>
                    </body>
                </html>
                '''
            )
            
            return JsonResponse({
                'success': True,
                'mensaje': 'Código enviado exitosamente al correo.'
            })
            
        except Exception as e:
            print(f"Error al enviar código: {str(e)}")
            return JsonResponse({
                'success': False,
                'mensaje': f'Error al enviar el código: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'mensaje': 'Método no permitido'})

def verificar_codigo(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            password = data.get('password')
            codigo_ingresado = data.get('codigo_verificacion')

            # Obtener código desde cache
            cache_key = f'verification_code_{email}'
            codigo_cache = cache.get(cache_key)

            # Obtener intentos desde cache
            intentos_key = f'intentos_codigo_{email}'
            intentos = cache.get(intentos_key, 0)

            # ✅ Verificar primero si es correcto
            if codigo_ingresado == codigo_cache:
                user = authenticate(request, username=email, password=password)
                if user:
                    login(request, user)
                    # Limpiar cache
                    cache.delete(cache_key)
                    cache.delete(intentos_key)
                    return JsonResponse({
                        'success': True,
                        'mensaje': 'Código correcto. Redirigiendo...',
                        'redirect_url': '/usuarios/dashboard/'
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'mensaje': 'Usuario o contraseña incorrectos. Vuelve a iniciar sesión.',
                        'redirect': True
                    })

            # Código incorrecto → aumentar intentos
            intentos += 1
            cache.set(intentos_key, intentos, 600)  # Guardar 10 minutos también

            if intentos >= 3:
                cache.delete(cache_key)
                cache.delete(intentos_key)
                return JsonResponse({
                    'success': False,
                    'mensaje': 'Has superado los 3 intentos. Vuelve a iniciar sesión.',
                    'redirect': True
                })

            return JsonResponse({
                'success': False,
                'mensaje': f'Código incorrecto. Intento {intentos} de 3.'
            })

        except Exception as e:
            print(f"Error al verificar código: {str(e)}")
            return JsonResponse({
                'success': False,
                'mensaje': f'Error al verificar el código: {str(e)}'
            })

    return JsonResponse({'success': False, 'mensaje': 'Método no permitido'})

def login_admin(request):
    """
    Login de administrador con verificación por código (2 pasos)
    """
    if request.method == 'POST':
        # Si ya tiene el código ingresado
        if 'codigo_verificacion' in request.POST:
            codigo = request.POST.get('codigo_verificacion')
            email = request.POST.get('email_verified')
            password = request.POST.get('password_verified')

            cache_key = f'verification_code_{email}'
            codigo_guardado = cache.get(cache_key)

            if codigo_guardado is None:
                return render(request, 'usuarios/loginAdm.html', {
                    'mensaje': 'El código ha expirado. Solicita uno nuevo.'
                })

            if codigo != codigo_guardado:
                return render(request, 'usuarios/loginAdm.html', {
                    'mensaje': 'Código de verificación incorrecto.'
                })

            # Autenticar usuario
            user = authenticate(request, username=email, password=password)
            if user is not None and user.rol == 'admin':
                cache.delete(cache_key)
                login(request, user)
                return redirect('usuarios:dashboard')
            else:
                return render(request, 'usuarios/loginAdm.html', {
                    'mensaje': 'Error: usuario no válido o sin permisos.'
                })

        # Si es el primer paso (ingreso de credenciales)
        else:
            email = request.POST.get('email')
            password = request.POST.get('password')

            user = authenticate(request, username=email, password=password)
            if user is not None and user.rol == 'admin':
                # Generar y guardar código temporal
                codigo = ''.join([str(random.randint(0, 9)) for _ in range(6)])
                cache_key = f'verification_code_{email}'
                cache.set(cache_key, codigo, 600)  # 10 minutos

                # Enviar correo
                asunto = 'Código de verificación - Unidos pensando en su salud'
                mensaje = f'Tu código de verificación es: {codigo}'
                send_mail(asunto, mensaje, settings.DEFAULT_FROM_EMAIL, [email])

                return render(request, 'usuarios/loginAdm.html', {
                    'verificacion': True,
                    'email_verified': email,
                    'password_verified': password
                })
            else:
                return render(request, 'usuarios/loginAdm.html', {
                    'mensaje': 'Credenciales incorrectas o no eres administrador.'
                })

    return render(request, 'usuarios/loginAdm.html')

def detalle_pedido(request, pedido_id):
    try:
        pedido = get_object_or_404(Pedido, id=pedido_id)
        usuario = getattr(pedido, 'usuario', None)

        # Obtener los items del pedido
        items = pedido.items.all()
        productos = []

        for item in items:
            producto = item.producto

            # Detectar correctamente el campo del nombre
            nombre_producto = getattr(producto, 'nombProduc', None) or getattr(producto, 'nombre', 'Producto')

            productos.append({
                'nombre': nombre_producto,
                'cantidad': item.cantidad,
                'precio': float(getattr(producto, 'precio', 0)),
                'subtotal': float(item.cantidad * getattr(producto, 'precio', 0))
            })

        # Respuesta JSON
        return JsonResponse({
            'success': True,
            'pedido': {
                'id': pedido.id,
                'usuario': getattr(usuario, 'nombre', 'N/A') if usuario else 'N/A',
                'email': getattr(usuario, 'email', 'N/A') if usuario else 'N/A',
                'telefono': getattr(usuario, 'telefono', 'N/A') if usuario else 'N/A',
                'direccion': getattr(usuario, 'direccion', 'N/A') if usuario else 'N/A',
                'estado': getattr(pedido, 'estado', 'Pendiente'),
                'pago': pedido.pago,
                'pagado': pedido.pago,  # Por si acaso lo usas en otro lugar
                'fecha': pedido.fecha_creacion.strftime('%d/%m/%Y') if hasattr(pedido, 'fecha_creacion') else 'N/A',
                'hora': pedido.fecha_creacion.strftime('%H:%M:%S') if hasattr(pedido, 'fecha_creacion') else '',
                'metodo_pago': getattr(pedido, 'metodo_pago', 'N/A'),
                'total': float(getattr(pedido, 'total', 0)),
                'productos': productos
            }
        })

    except Exception as e:
        import traceback
        print(f"Error completo: {traceback.format_exc()}")
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)

@admin_required
@require_http_methods(["POST"])
def cambiar_estado_pedido(request, pedido_id):
    try:
        # Obtener el pedido
        pedido = get_object_or_404(Pedido, id=pedido_id)
        
        # Obtener el nuevo estado del body
        data = json.loads(request.body)
        nuevo_estado = data.get('estado')
        
        # Validar que el estado sea válido
        estados_validos = ['pendiente', 'enviado', 'entregado']
        if nuevo_estado not in estados_validos:
            return JsonResponse({
                'success': False,
                'message': 'Estado no válido'
            }, status=400)
        
        # Actualizar el estado
        pedido.estado = nuevo_estado
        pedido.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Estado actualizado a {nuevo_estado}',
            'nuevo_estado': nuevo_estado
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Error al procesar los datos'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)
    
# ====================== VISTAS DE DEVOLUCIONES (ADMIN) ======================
@login_required
def gst_devoluciones(request):
    """Vista para que el admin gestione todas las devoluciones"""
    
    # ✅ SOLO VERIFICAR is_staff o is_superuser
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, 'No tienes permisos para acceder aquí')
        return redirect('usuarios:dashboard')
    
    estado = request.GET.get('estado')
    
    if estado:
        # Si hay filtro, traer las devoluciones de ese estado
        devoluciones = Devolucion.objects.select_related(
            'usuario', 'producto', 'pedido'
        ).filter(estado=estado).order_by('-fecha_solicitud')
    else:
        # Por defecto, solo las PENDIENTES
        devoluciones = Devolucion.objects.select_related(
            'usuario', 'producto', 'pedido'
        ).filter(estado='Pendiente').order_by('-fecha_solicitud')
    
    # Preparar datos en JSON para el modal
    devoluciones_data = []
    for dev in devoluciones:
        devoluciones_data.append({
            'id': dev.id,
            'usuario_nombre': dev.usuario.nombre,
            'usuario_email': dev.usuario.email,
            'producto_nombre': dev.producto.nombProduc,
            'pedido_id': dev.pedido.id,
            'item_id': dev.item.id if dev.item else None,
            'unidad': dev.unidad,
            'lote': dev.lote.codigo_lote if dev.lote else None, 
            'fecha': dev.fecha_solicitud.strftime('%d/%m/%Y %H:%M'),
            'motivo': dev.motivo,
            'estado': dev.estado,
            'fotos': dev.get_fotos()
        })
    
    import json
    devoluciones_json = json.dumps(devoluciones_data)
    
    context = {
        'devoluciones': devoluciones,
        'devoluciones_json': devoluciones_json
    }
    
    return render(request, 'usuarios/gst_devoluciones.html', context)

def aprobar_devolucion(request, devolucion_id):
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': "No tienes permisos."}, status=403)
    
    try:
        devolucion = Devolucion.objects.select_related('pedido', 'producto', 'item').get(id=devolucion_id)
        producto = devolucion.producto
        item = devolucion.item
        
        if not item:
            return JsonResponse({'success': False, 'error': "No se encontró el item asociado a la devolución"}, status=400)
        
        # Marcar la devolución como aprobada
        devolucion.estado = "Aprobada"
        devolucion.fecha_respuesta = timezone.now()
        devolucion.save()
        
        # Registrar historial
        comentario_inicial = f"Aprobada. Motivo: {devolucion.motivo}"
        HistorialDevolucion.objects.create(
            devolucion=devolucion,
            estado='Aprobada',
            usuario_admin=request.user,
            comentario=comentario_inicial
        )
        
        # === GESTIÓN DE STOCK DEL PRODUCTO DEVUELTO ===
        lote_original = item.lote
        
        if devolucion.motivo == "Producto equivocado":
            # El producto EQUIVOCADO nunca debió salir del stock (fue error de empaque)
            # El producto CORRECTO ya fue descontado en la compra original
            # Por tanto: NO hay cambios en el stock
            print("\n→ PRODUCTO EQUIVOCADO: Sin cambios en stock")
            print("   - Producto correcto (que pidió) ya fue descontado en compra original")
            print("   - Producto equivocado (que recibió) nunca salió del inventario")
            comentario_stock = "Producto equivocado devuelto. Sin cambios en stock (el correcto ya fue descontado originalmente)"
        
        elif devolucion.motivo in ["Fecha de vencimiento expirado", "Producto dañado"]:
            # El producto vencido/dañado YA FUE DESCONTADO en la compra original
            # El cliente lo tiene en su poder, por tanto NO se descuenta nuevamente
            # Solo se descartará cuando se recoja (pero ya está fuera del inventario)
            print("\n→ PRODUCTO DAÑADO/VENCIDO: Ya fue descontado en compra original")
            print("   - El producto defectuoso está en poder del cliente")
            print("   - NO se descuenta nuevamente (ya salió del inventario)")
            
            if lote_original:
                comentario_stock = f"Producto defectuoso del lote {lote_original.codigo_lote or lote_original.id} (ya descontado en compra)"
            else:
                comentario_stock = "Producto defectuoso (ya descontado en compra)"
        
        else:
            print("\n→ OTRO MOTIVO: Sin cambios en stock")
            comentario_stock = "Sin cambios en el stock"
        
        # Actualizar comentario del historial
        historial = HistorialDevolucion.objects.filter(devolucion=devolucion).last()
        if historial:
            historial.comentario += f" | {comentario_stock}"
            historial.save()
        
        # === GESTIÓN DE REEMPLAZO ===
        mensaje_reemplazo = ""
        lote_reemplazo = None
        
        if devolucion.motivo in ["Fecha de vencimiento expirado", "Producto dañado"]:
            # Buscar un lote disponible para el reemplazo
            lote_reemplazo = producto.lotes.filter(cantidad__gt=0).order_by('fecha_caducidad').first()
            
            if lote_reemplazo:
                # Descontar 1 unidad del lote de reemplazo
                lote_reemplazo.cantidad -= 1
                lote_reemplazo.save()
                print(f"✅ Descontado 1 unidad del lote {lote_reemplazo.codigo_lote or lote_reemplazo.id} (reemplazo)")
                print(f"   Stock lote después: {lote_reemplazo.cantidad}")
                mensaje_reemplazo = f"Se enviará un producto de reemplazo del lote {lote_reemplazo.codigo_lote or lote_reemplazo.id}"
            else:
                print(f"⚠️ ADVERTENCIA: No hay stock disponible para enviar reemplazo")
                mensaje_reemplazo = "⚠️ Sin stock disponible para reemplazo"
                
        elif devolucion.motivo == "Producto equivocado":
            # Buscar un lote disponible del producto CORRECTO
            lote_reemplazo = producto.lotes.filter(cantidad__gt=0).order_by('fecha_caducidad').first()
            
            if lote_reemplazo:
                print(f"✅ Se enviará el producto correcto del lote {lote_reemplazo.codigo_lote or lote_reemplazo.id} (sin descuento adicional)")
                mensaje_reemplazo = f"Se enviará el producto correcto del lote {lote_reemplazo.codigo_lote or lote_reemplazo.id}"
            else:
                print(f"⚠️ ADVERTENCIA: No hay lotes disponibles del producto correcto")
                mensaje_reemplazo = "⚠️ Sin stock disponible del producto correcto"
        else:
            mensaje_reemplazo = "Se gestionará el envío del reemplazo"
        
        # === ENVIAR EMAIL AL CLIENTE ===
        try:
            from django.core.mail import send_mail
            from django.conf import settings
            
            # Obtener nombre del usuario
            nombre_usuario = devolucion.usuario.nombre if devolucion.usuario.nombre else devolucion.usuario.email.split('@')[0]
            
            asunto = f'Devolución #{devolucion.id} aprobada - {producto.nombProduc if hasattr(producto, "nombProduc") else str(producto)}'
            
            mensaje = f"""
Hola {nombre_usuario},

Tu devolución del producto "{producto.nombProduc if hasattr(producto, "nombProduc") else str(producto)}" ha sido APROBADA.

DETALLES DE LA DEVOLUCIÓN:
- Devolución #: {devolucion.id}
- Producto: {producto.nombProduc if hasattr(producto, "nombProduc") else str(producto)}
- Unidad: {devolucion.unidad}
- Motivo: {devolucion.motivo}
- Fecha de aprobación: {devolucion.fecha_respuesta.strftime('%d/%m/%Y %H:%M')}

REEMPLAZO:
{mensaje_reemplazo}

Pronto recibirás tu producto de reemplazo{f' (Lote: {lote_reemplazo.codigo_lote or lote_reemplazo.id}, Vencimiento: {lote_reemplazo.fecha_caducidad.strftime("%d/%m/%Y")})' if lote_reemplazo else ''}.

Gracias por tu confianza.

---
Este es un correo automático.
            """.strip()
            
            # Verificar que el usuario tenga email
            if devolucion.usuario.email:
                send_mail(
                    subject=asunto,
                    message=mensaje,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[devolucion.usuario.email],
                    fail_silently=True
                )
            else:
                print(f"Usuario {devolucion.usuario.nombre} no tiene email configurado")
            
        except Exception as e:
            print(f"Error al enviar email: {str(e)}")
        
        # Respuesta AJAX final
        return JsonResponse({
            'success': True,
            'id': devolucion_id,
            'mensaje': f"Devolución #{devolucion_id} aprobada. {mensaje_reemplazo}"
        })
        
    except Devolucion.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Devolución no encontrada'}, status=404)
    except Exception as e:
        print(f"Error en aprobar_devolucion: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
@login_required
def rechazar_devolucion(request, devolucion_id):
    if not request.user.is_staff and not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': "No tienes permisos."}, status=403)

    try:
        devolucion = Devolucion.objects.get(id=devolucion_id)
        devolucion.estado = 'Rechazada'
        devolucion.fecha_respuesta = timezone.now()
        devolucion.save()

        HistorialDevolucion.objects.create(
            devolucion=devolucion,
            estado='Rechazada',
            usuario_admin=request.user,
            comentario='Rechazada por admin'
        )

        return JsonResponse({
            'success': True,
            'id': devolucion_id,
            'mensaje': f"Devolución #{devolucion_id} rechazada"
        })

    except Devolucion.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Devolución no encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
def historial_devoluciones(request):
    """Vista para mostrar el historial de devoluciones (solo Aprobadas o Rechazadas)."""
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "No tienes permisos para acceder aquí")
        return redirect("usuarios:dashboard")
    
    filtro_tiempo = request.GET.get('tiempo')
    estado = request.GET.get('estado')
    busqueda = request.GET.get('buscar')
    
    ahora = timezone.now()
    
    # Base query - solo Aprobadas o Rechazadas
    devoluciones = Devolucion.objects.filter(
        estado__in=['Aprobada', 'Rechazada']
    ).select_related('usuario', 'producto', 'pedido', 'lote').prefetch_related('historial')
    
    # Filtro por tiempo
    if filtro_tiempo == "semana":
        inicio_semana = ahora - timezone.timedelta(days=ahora.weekday())
        devoluciones = devoluciones.filter(fecha_solicitud__gte=inicio_semana)
    elif filtro_tiempo == "mes":
        devoluciones = devoluciones.filter(
            fecha_solicitud__year=ahora.year,
            fecha_solicitud__month=ahora.month
        )
    elif filtro_tiempo == "año":
        devoluciones = devoluciones.filter(
            fecha_solicitud__year=ahora.year
        )
    
    # Filtro por estado (Aprobada o Rechazada)
    if estado:
        devoluciones = devoluciones.filter(estado=estado)
    
    # Filtro por búsqueda (usuario, producto o lote)
    if busqueda:
        devoluciones = devoluciones.filter(
            Q(usuario__nombre__icontains=busqueda) |
            Q(usuario__email__icontains=busqueda) |
            Q(producto__nombProduc__icontains=busqueda) |
            Q(lote__codigo_lote__icontains=busqueda)
        )
    
    # Orden
    devoluciones = devoluciones.order_by('-fecha_solicitud')
    
    # Conteos para estadísticas
    total_aprobadas = devoluciones.filter(estado='Aprobada').count()
    total_rechazadas = devoluciones.filter(estado='Rechazada').count()
    
    context = {
        'devoluciones': devoluciones,
        'total_aprobadas': total_aprobadas,
        'total_rechazadas': total_rechazadas,
        'filtro_tiempo': filtro_tiempo,
        'estado_filtro': estado,
        'busqueda': busqueda,
    }
    return render(request, 'usuarios/historial_devoluciones.html', context)

def exportar_devoluciones_excel(request):
    import openpyxl
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    from datetime import datetime

    wb = Workbook()
    ws = wb.active
    ws.title = "Devoluciones"

    # Encabezado principal (NARANJA)
    ws.merge_cells('A1:H1')
    ws['A1'] = 'TIENDA NATURISTA LOS GIRASOLES'
    ws['A1'].font = Font(bold=True, size=16, color='FFFFFF')
    ws['A1'].alignment = Alignment(horizontal='center', vertical='center')
    ws['A1'].fill = PatternFill(start_color='E67E22', end_color='E67E22', fill_type='solid')
    ws.row_dimensions[1].height = 30

    # Subtítulo (NARANJA OSCURO)
    ws.merge_cells('A2:H2')
    ws['A2'] = 'HISTORIAL DE DEVOLUCIONES'
    ws['A2'].font = Font(bold=True, size=12, color='FFFFFF')
    ws['A2'].alignment = Alignment(horizontal='center', vertical='center')
    ws['A2'].fill = PatternFill(start_color='D35400', end_color='D35400', fill_type='solid')
    ws.row_dimensions[2].height = 25

    # Fecha de generación
    ws.merge_cells('A3:H3')
    ws['A3'] = f'Fecha de generación: {datetime.now().strftime("%d/%m/%Y %H:%M")}'
    ws['A3'].font = Font(italic=True, size=10)
    ws['A3'].alignment = Alignment(horizontal='center')
    ws.row_dimensions[3].height = 20

    # Fila vacía
    ws.append([])

    # Encabezados de columnas (AMARILLO)
    encabezados = ['ID', 'Cliente', 'Email', 'Producto', 'Lote', 'Motivo', 'Estado', 'Fecha']
    ws.append(encabezados)

    header_fill = PatternFill(start_color='F1C40F', end_color='F1C40F', fill_type='solid')
    header_font = Font(bold=True, color='000000')
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    for col in range(1, 9):
        cell = ws.cell(row=5, column=col)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.border = thin_border

    # Filtro desde GET
    estado = request.GET.get('estado')

    # Consulta base
    devoluciones = Devolucion.objects.filter(
        estado__in=['Aprobada', 'Rechazada']
    ).order_by('-fecha_solicitud')
    
    if estado:
        devoluciones = devoluciones.filter(estado=estado)

    # Colores por estado
    estado_colors = {
        'aprobada': 'D5F4E6',   # Verde claro
        'rechazada': 'FADBD8',  # Rojo claro
    }

    # Datos
    row_num = 6
    for dev in devoluciones:
        ws.append([
            dev.id,
            dev.usuario.nombre if dev.usuario else 'Sin usuario',
            dev.usuario.email if dev.usuario else 'Sin email',
            dev.producto.nombProduc if dev.producto else 'Sin producto',
            dev.lote.codigo_lote if dev.lote else 'Sin lote',
            dev.motivo,
            dev.estado,
            dev.fecha_solicitud.strftime('%d/%m/%Y %H:%M')
        ])

        # Color según estado
        estado_lower = dev.estado.lower()
        row_fill = PatternFill(
            start_color=estado_colors.get(estado_lower, 'FFFFFF'),
            end_color=estado_colors.get(estado_lower, 'FFFFFF'),
            fill_type='solid'
        )

        for col in range(1, 9):
            cell = ws.cell(row=row_num, column=col)
            cell.border = thin_border
            cell.fill = row_fill
        row_num += 1

    # Resumen al final
    total_aprobadas = devoluciones.filter(estado='Aprobada').count()
    total_rechazadas = devoluciones.filter(estado='Rechazada').count()
    
    ws.append([])
    row_num += 1
    
    ws.append(['', '', '', '', '', 'Total Aprobadas:', total_aprobadas, ''])
    for col in range(1, 9):
        cell = ws.cell(row=row_num, column=col)
        cell.font = Font(bold=True)
        if col == 7:
            cell.fill = PatternFill(start_color='D5F4E6', end_color='D5F4E6', fill_type='solid')
    row_num += 1

    ws.append(['', '', '', '', '', 'Total Rechazadas:', total_rechazadas, ''])
    for col in range(1, 9):
        cell = ws.cell(row=row_num, column=col)
        cell.font = Font(bold=True)
        if col == 7:
            cell.fill = PatternFill(start_color='FADBD8', end_color='FADBD8', fill_type='solid')

    # Ajustar ancho de columnas
    column_widths = [10, 25, 30, 25, 15, 35, 15, 20]
    for i, width in enumerate(column_widths, 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = width

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="historial_devoluciones.xlsx"'
    wb.save(response)
    return response

@login_required(login_url='usuarios:login')
def guardar_direccion(request):
    """Guarda la dirección de envío del usuario en la base de datos"""
    if request.method == 'POST':
        try:
            # Crear o actualizar la dirección principal del usuario
            direccion, creada = Direccion.objects.update_or_create(
                usuario=request.user,
                es_principal=True,
                defaults={
                    'nombre_completo': request.POST.get('nombre_completo', ''),
                    'telefono': request.POST.get('telefono', ''),
                    'direccion_completa': request.POST.get('direccion_completa', ''),
                    'ciudad': request.POST.get('ciudad', ''),
                    'codigo_postal': request.POST.get('codigo_postal', ''),
                    'notas_entrega': request.POST.get('notas_entrega', ''),
                }
            )
            
            if creada:
                messages.success(request, 'Dirección guardada correctamente.')
            else:
                messages.success(request, 'Dirección actualizada correctamente.')
                
        except Exception as e:
            messages.error(request, f'Error al guardar la dirección: {str(e)}')
    
    return redirect('pagos:checkout')

@login_required(login_url='usuarios:login')
def editar_direccion(request):
    """Permite al usuario editar su dirección guardada"""
    # 🔥 CORRECCIÓN: Usar reverse con parámetros GET
    from django.urls import reverse
    url = reverse('pagos:checkout')
    return redirect(f"{url}?editar=true")