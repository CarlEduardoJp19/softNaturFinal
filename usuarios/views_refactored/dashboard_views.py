from django.db.models import Count, Sum, Q
from django.db.models.functions import TruncMonth
from django.shortcuts import render
from django.utils import timezone

from ..decorators import admin_required
from ..models import Pedido, Usuario, Devolucion
from productos.models import Producto

@admin_required
def dashboard(request):
    mes_especifico = request.GET.get("mes_especifico", "")
    anio_especifico = request.GET.get("anio_especifico", "")
    
    hoy = timezone.now()

    # Base: solo datos desde 2025
    pedidos = Pedido.objects.filter(
        pago=True,
        fecha_creacion__year__gte=2025
    )

    # Base para devoluciones con el mismo filtro de fecha
    devoluciones = Devolucion.objects.filter(
        fecha_solicitud__year__gte=2025
    )

    # FILTROS ESPECÍFICOS
    if mes_especifico:
        pedidos = pedidos.filter(fecha_creacion__month=int(mes_especifico))
        devoluciones = devoluciones.filter(fecha_solicitud__month=int(mes_especifico))
    
    if anio_especifico:
        pedidos = pedidos.filter(fecha_creacion__year=int(anio_especifico))
        devoluciones = devoluciones.filter(fecha_solicitud__year=int(anio_especifico))

    # TOTALES FILTRADOS
    total_ventas = pedidos.aggregate(total=Sum("total"))["total"] or 0
    total_pedidos = pedidos.count()

    # Productos filtrados por los pedidos filtrados
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
    
    # Total de productos: si no hay filtros, mostrar todos los productos
    if not mes_especifico and not anio_especifico:
        total_productos = Producto.objects.count()
    else:
        total_productos = prod_info.count()

    # Usuarios con compras en el período filtrado
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
    
    # Total de usuarios: si no hay filtros, mostrar todos los usuarios
    if not mes_especifico and not anio_especifico:
        total_usuarios = Usuario.objects.count()
    else:
        total_usuarios = usuarios_info.count()

    # Ventas por mes (con los pedidos ya filtrados)
    ventas_info = (
        pedidos.annotate(mes=TruncMonth("fecha_creacion"))
        .values("mes")
        .annotate(total=Sum("total"))
        .order_by("mes")
    )
    ventas_info = [
        (v["mes"].strftime("%B"), v["total"]) for v in ventas_info
    ]

    # Estado de pedidos (con los pedidos ya filtrados)
    estado_info = (
        pedidos.values("estado")
        .annotate(total=Count("id"))
        .order_by("estado")
    )
    estado_info = [(e["estado"], e["total"]) for e in estado_info]

    # Últimas 5 devoluciones (con el filtro aplicado)
    ultimas_devoluciones = devoluciones.order_by('-fecha_solicitud')[:5]

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