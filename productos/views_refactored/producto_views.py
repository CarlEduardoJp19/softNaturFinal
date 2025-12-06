from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.utils import timezone
from ..models import Producto, Category, Calificacion
from usuarios.decorators import login_required


# ---------------------- VISTAS DE PRODUCTOS ----------------------

def productos(request):
    products = Producto.objects.all()
    return render(request, 'productos/producto.html', {'products': products})


def productos_view(request, categoria_id=None):
    buscar = request.GET.get('buscar', '')
    
    if categoria_id:
        try:
            categoria = Category.objects.get(id=categoria_id)
            productos = Producto.objects.filter(
                Categoria=categoria,  # ⭐ Nota: es "Categoria" con mayúscula en tu modelo
                estado=True
            ).prefetch_related('lotes')  # ⭐ CAMBIADO: usar prefetch en lugar de annotate
        except Category.DoesNotExist:
            productos = Producto.objects.filter(
                estado=True
            ).prefetch_related('lotes')
            categoria = None
    else:
        productos = Producto.objects.filter(
            estado=True
        ).prefetch_related('lotes')  # ⭐ CAMBIADO: usar prefetch en lugar de annotate
        categoria = None
    
    if buscar:
        productos = productos.filter(
            Q(nombProduc__icontains=buscar) |
            Q(descripcion__icontains=buscar)
        )
    
    # ⭐ ACTUALIZAR STOCK EN CARRITO
    carrito = request.session.get('carrito', {})
    for producto_id_str in list(carrito.keys()):
        try:
            producto = Producto.objects.get(id=int(producto_id_str))
            carrito[producto_id_str]["stock"] = producto.stock_total
        except Producto.DoesNotExist:
            del carrito[producto_id_str]
    
    request.session['carrito'] = carrito
    request.session.modified = True
    
    # ------------------ Carrito en sesión ------------------
    items = []
    subtotal = 0
    total_cantidad = 0
    
    for key, value in carrito.items():
        if not isinstance(value, dict):
            continue
        
        cantidad = int(value.get("cantidad", 0))
        precio = float(value.get("precio", 0))
        nombre = value.get("nombProduc", "Sin nombre")
        precio_total = cantidad * precio
        
        subtotal += precio_total
        total_cantidad += cantidad
        
        items.append({
            "producto_id": key,
            "producto": nombre,
            "cantidad": cantidad,
            "precio_unitario": precio,
            "precio_total": precio_total
        })
    
    iva = subtotal * 0.19
    total = subtotal + iva
    
    categorias = Category.objects.all()
    
    return render(request, 'productos/producto.html', {
        'products': productos,
        'carrito': items,
        'subtotal': round(subtotal, 2),
        'iva': round(iva, 2),
        'total': round(total, 2),
        'total_cantidad': total_cantidad,
        'categorias': categorias,
        'categoria_actual': categoria,
        'buscar': buscar,
    })

def productos_por_categoria(request, categoria_id):
    try:
        categoria = Category.objects.get(id=categoria_id)
        productos = Producto.objects.filter(Categoria=categoria, estado=True)
    except Category.DoesNotExist:
        productos = Producto.objects.filter(estado=True)
        categoria = None

    usuario_id = request.session.get('usuario_id')
    carrito = request.session.get('carrito', {})
    items = []
    total = 0

    for key, value in carrito.items():
        if not isinstance(value, dict):
            continue

        cantidad = int(value.get("cantidad", 0))
        precio = float(value.get("precio", 0))
        nombre = value.get("nombProduc", "Sin nombre")

        subtotal = precio * cantidad
        items.append({
            "producto": nombre,
            "cantidad": cantidad,
            "precio": precio,
            "subtotal": subtotal
        })
        total += subtotal

    categorias = Category.objects.all()

    return render(request, 'productos/producto.html', {
        'products': productos,
        'usuario_id': usuario_id,
        'carrito': items,
        'total': total,
        'categorias': categorias,
        'categoria_actual': categoria,
    })


def detalle_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    return render(request, "productos/detalle.html", {"producto": producto})


def lote_activo(request, producto_id):
    product = get_object_or_404(Producto, id=producto_id)

    # Obtener el lote más próximo a vencer (sin vencer)
    lote_act = product.lotes.filter(
        fecha_caducidad__gte=timezone.now().date()
    ).order_by('fecha_caducidad').first()

    return render(request, 'productos/detalle.html', {
        'product': product,
        'lote_activo': lote_act,
    })