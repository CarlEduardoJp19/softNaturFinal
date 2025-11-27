from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse

from ..models import Producto, CarritoItem, Lote

# ---------------------- CARRITO ----------------------
def agregarAlCarrito(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    carrito = request.session.get("carrito", {})
    producto_id_str = str(producto.id)

    # Buscar el lote más cercano a vencer
    lote = Lote.objects.filter(
        producto=producto,
        cantidad__gt=0
    ).order_by('fecha_caducidad').first()

    # 🔍 DEBUG DETALLADO
    print("=" * 50)
    print(f"PRODUCTO: {producto.id} - {producto.nombProduc}")
    print(f"LOTE ENCONTRADO: {lote}")
    if lote:
        print(f"  → codigo_lote: {lote.codigo_lote}")
        print(f"  → cantidad: {lote.cantidad}")
        print(f"  → producto_id del lote: {lote.producto_id}")
    else:
        print("  → ❌ NO SE ENCONTRÓ NINGÚN LOTE")
        
        # Ver qué lotes existen para este producto
        todos_lotes = Lote.objects.filter(producto=producto)
        print(f"  → Lotes totales para este producto: {todos_lotes.count()}")
        for l in todos_lotes:
            print(f"     - {l.codigo_lote}, cantidad: {l.cantidad}")
    print("=" * 50)

    lote_codigo = lote.codigo_lote if lote else None

    if producto_id_str in carrito:
        carrito[producto_id_str]["cantidad"] += 1
        if not carrito[producto_id_str].get("lote"):
            carrito[producto_id_str]["lote"] = lote_codigo
    else:
        carrito[producto_id_str] = {
            "cantidad": 1,
            "precio": float(producto.precio),
            "nombProduc": producto.nombProduc,
            "imgProduc": producto.imgProduc.url,
            "lote": lote_codigo
        }

    request.session["carrito"] = carrito
    request.session.modified = True

    return redirect(f"{reverse('productos:producto')}?carrito=1")

def eliminar(request, producto_id):
    carrito = request.session.get('carrito', {})
    producto_id_str = str(producto_id)

    # --- SESIÓN ---
    if producto_id_str in carrito:
        del carrito[producto_id_str]

    request.session['carrito'] = carrito
    request.session.modified = True

    # --- BASE DE DATOS ---
    if request.user.is_authenticated:
        CarritoItem.objects.filter(usuario=request.user, producto_id=producto_id).delete()

    return redirect("productos:producto")

def restar_producto(request, producto_id):
    carrito = request.session.get('carrito', {})
    producto_id_str = str(producto_id)

    # --- SESIÓN ---
    if producto_id_str in carrito:
        if carrito[producto_id_str]["cantidad"] > 1:
            carrito[producto_id_str]["cantidad"] -= 1
        else:
            del carrito[producto_id_str]

    request.session['carrito'] = carrito
    request.session.modified = True

    # --- BASE DE DATOS ---
    if request.user.is_authenticated:
        try:
            item = CarritoItem.objects.get(usuario=request.user, producto_id=producto_id)
            if item.cantidad > 1:
                item.cantidad -= 1
                item.save()
            else:
                item.delete()
        except CarritoItem.DoesNotExist:
            pass

    return redirect(f"{reverse('productos:producto')}?carrito=1")

def limpiar(request):
    # --- SESIÓN ---
    request.session['carrito'] = {}
    request.session.modified = True

    # --- BASE DE DATOS ---
    if request.user.is_authenticated:
        CarritoItem.objects.filter(usuario=request.user).delete()

    return redirect("productos:producto")

# ---------------------- CRUD PRODUCTOS ----------------------

def cargar_carrito_usuario(request, usuario):
    carrito_items = CarritoItem.objects.filter(usuario=usuario)
    carrito = {}

    for item in carrito_items:
        carrito[str(item.producto.id)] = {
            "cantidad": item.cantidad,
            "precio": float(item.producto.precio),
            "nombProduc": item.producto.nombProduc,
        }

    request.session["carrito"] = carrito
    request.session.modified = True