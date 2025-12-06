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
    
    lote_codigo = lote.codigo_lote if lote else None
    stock_disponible = producto.stock_total
    
    # ⭐ SI NO HAY STOCK, redirigir con parámetro
    if stock_disponible <= 0:
        return redirect(f"{reverse('productos:producto')}?sin_stock={producto_id}&nombre={producto.nombProduc}")
    
    if producto_id_str in carrito:
        cantidad_actual = carrito[producto_id_str]["cantidad"]
        
        # ⭐ VERIFICAR STOCK antes de agregar
        if cantidad_actual < stock_disponible:
            carrito[producto_id_str]["cantidad"] += 1
            carrito[producto_id_str]["stock"] = stock_disponible
        else:
            return redirect(f"{reverse('productos:producto')}?stock_maximo={producto_id}&nombre={producto.nombProduc}&carrito=1")
        
        if not carrito[producto_id_str].get("lote"):
            carrito[producto_id_str]["lote"] = lote_codigo
    else:
        carrito[producto_id_str] = {
            "cantidad": 1,
            "precio": float(producto.precio),
            "nombProduc": producto.nombProduc,
            "imgProduc": producto.imgProduc.url,
            "lote": lote_codigo,
            "stock": stock_disponible
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

def actualizar_stock_carrito(request):
    """Actualiza el stock de todos los productos en el carrito"""
    carrito = request.session.get("carrito", {})
    
    for producto_id_str, item in carrito.items():
        try:
            producto = Producto.objects.get(id=int(producto_id_str))
            stock_disponible = producto.stock_total
            
            # ⭐ Agregar o actualizar el campo stock
            carrito[producto_id_str]["stock"] = stock_disponible
            
            print(f"✅ Actualizado stock para {producto.nombProduc}: {stock_disponible}")
        except Producto.DoesNotExist:
            print(f"⚠️ Producto {producto_id_str} no existe, se eliminará del carrito")
            del carrito[producto_id_str]
    
    request.session["carrito"] = carrito
    request.session.modified = True
    return carrito