from django.db.models import Count, Sum, Q
from django.db.models.functions import TruncMonth
from django.shortcuts import render
from django.utils import timezone

from ..decorators import admin_required
from ..models import Pedido, Usuario, Devolucion
from productos.models import Producto

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