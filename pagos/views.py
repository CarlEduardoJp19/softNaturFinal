# pagos/views.py ESTO ES PARA CQUE SALGA EL COSTO DELL ENVIO DEL DOMICILIO 
import hashlib
import time
import json
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from .models import Transaccion
from usuarios.models import Pedido, Direccion, PedidoItem
from productos.models import Producto
from django.views.decorators.csrf import csrf_exempt
import hashlib
import time
from django.shortcuts import render, redirect
from django.conf import settings
from usuarios.models import Pedido, PedidoItem
from django.db import transaction
from .models import Transaccion
from productos.models import Producto, Lote


def checkout(request):
    carrito = request.session.get("carrito", {})
    
    if not carrito:
        return redirect("productos:producto")
    
    productos = []
    subtotal = 0

    for item in carrito.values():
        imagen = item.get('imgProduc', '')
        nombre = item.get('nombProduc', 'Sin nombre')
        cantidad = int(item.get('cantidad', 0))
        precio = float(item.get('precio', 0))
        precio_producto = precio * cantidad
        subtotal += precio_producto

        productos.append({
            'imagen': imagen,
            'nombre': nombre,
            'cantidad': cantidad,
            'precio': precio,
            'subtotal': precio_producto
        })

    # Dirección + envío
    direccion_guardada = None
    costo_envio = 0

    if request.user.is_authenticated:
        try:
            direccion_guardada = Direccion.objects.get(usuario=request.user, es_principal=True)

            ciudad = direccion_guardada.ciudad.lower().strip()

            if 'ibague' in ciudad or 'ibagué' in ciudad:
                costo_envio = 8000
            # Todos los demás municipios del Tolima - $12,000
            elif any(municipio in ciudad for municipio in [
                # Zona norte
                'honda', 'mariquita', 'armero', 'guayabal', 'casabianca', 'palocabildo', 
                'fresno', 'falan', 'herveo', 'lerida', 'lérida', 'ambalema', 'venadillo',
                
                # Zona sur
                'espinal', 'guamo', 'saldaña', 'saldana', 'purificacion', 'purificación', 
                'suarez', 'suárez', 'carmen de apicala', 'apicala', 'melgar', 'icononzo', 
                'cunday', 'villarrica', 'prado', 'dolores', 'alpujarra', 'ataco',
                
                # Zona occidente
                'chaparral', 'rioblanco', 'roncesvalles', 'ortega', 'coyaima', 
                'natagaima', 'san antonio',
                
                # Zona centro
                'cajamarca', 'rovira', 'valle de san juan', 'san juan', 'coello', 
                'flandes', 'alvarado', 'piedras', 'anzoategui', 'anzoátegui', 'santa isabel',
                
                # Zona oriente  
                'libano', 'líbano', 'murillo', 'villahermosa', 'planadas', 'san luis'
            ]):
                costo_envio = 12000

        except Direccion.DoesNotExist:
            pass

    # Calcular totales
    iva = subtotal * 0.19
    total_sin_envio = subtotal + iva
    total_final = total_sin_envio + costo_envio

    # Generar order_id SOLO para Bold
    timestamp = int(time.time())
    order_id = f"ORD-{timestamp}"

    amount = int(total_final)
    currency = "COP"
    cadena = f"{order_id}{amount}{currency}{settings.BOLD_SECRET_KEY}"
    integrity_hash = hashlib.sha256(cadena.encode()).hexdigest()

    redirection_url = request.build_absolute_uri('/pagos/respuesta/')

    context = {
        'productos': productos,
        'subtotal': round(subtotal, 2),
        'iva': round(iva, 2),
        'costo_envio': round(costo_envio, 2),
        'total_sin_envio': round(total_sin_envio, 2),
        'total_final': round(total_final, 2),
        'order_id': order_id,
        'amount': amount,
        'currency': currency,
        'integrity_hash': integrity_hash,
        'redirection_url': redirection_url,
        'bold_api_key': settings.BOLD_API_KEY,
        'direccion_guardada': direccion_guardada,
    }
    

    return render(request, 'pagos/checkout.html', context)

def payment_response(request):
    order_id = request.GET.get('bold-order-id')
    tx_status = request.GET.get('bold-tx-status')

    if not order_id:
        return redirect('productos:producto')

    carrito = request.session.get("carrito", {})
    productos_ids = []

    if tx_status == 'approved':
        subtotal = sum(float(item['precio']) * int(item['cantidad']) for item in carrito.values())
        iva = subtotal * 0.19
        costo_envio = 0

        try:
            direccion = Direccion.objects.get(usuario=request.user, es_principal=True)
            ciudad = direccion.ciudad.lower().strip()

            if 'ibague' in ciudad or 'ibagué' in ciudad:
                costo_envio = 8000
            elif any(municipio in ciudad for municipio in [
                'honda', 'mariquita', 'armero', 'guayabal', 'casabianca', 'palocabildo', 
                'fresno', 'falan', 'herveo', 'lerida', 'lérida', 'ambalema', 'venadillo',
                'espinal', 'guamo', 'saldaña', 'saldana', 'purificacion', 'purificación', 
                'suarez', 'suárez', 'carmen de apicala', 'apicala', 'melgar', 'icononzo', 
                'cunday', 'villarrica', 'prado', 'dolores', 'alpujarra', 'ataco',
                'chaparral', 'rioblanco', 'roncesvalles', 'ortega', 'coyaima', 
                'natagaima', 'san antonio',
                'cajamarca', 'rovira', 'valle de san juan', 'san juan', 'coello', 
                'flandes', 'alvarado', 'piedras', 'anzoategui', 'anzoátegui', 'santa isabel',
                'libano', 'líbano', 'murillo', 'villahermosa', 'planadas', 'san luis'
            ]):
                costo_envio = 12000
        except Direccion.DoesNotExist:
            pass

        total_final = subtotal + iva + costo_envio

        pedido = Pedido.objects.create(
            usuario=request.user,
            order_id=order_id,
            total=total_final,
            estado='Pendiente',
            pago=True
        )

        for producto_id, item in carrito.items():
            producto = Producto.objects.get(id=int(producto_id))
            cantidad = int(item['cantidad'])
            precio_unitario = float(item['precio'])
            
            # ✅ AGREGAR EL ID A LA LISTA
            productos_ids.append(int(producto_id))

            lote_codigo = item.get('lote')
            lote_obj = None
            if lote_codigo:
                try:
                    lote_obj = Lote.objects.get(codigo_lote=lote_codigo, producto=producto)
                except Lote.DoesNotExist:
                    lote_obj = None

            PedidoItem.objects.create(
                pedido=pedido,
                producto=producto,
                cantidad=cantidad,
                precio_unitario=precio_unitario,
                lote=lote_obj,
                codigo_lote=lote_obj.codigo_lote if lote_obj else None
            )

            if lote_obj:
                lote_obj.cantidad -= cantidad
                if lote_obj.cantidad < 0:
                    lote_obj.cantidad = 0
                lote_obj.save()

        Transaccion.objects.create(
            order_id=order_id,
            usuario=request.user,
            pedido=pedido,
            monto=total_final,
            estado='approved'
        )

        request.session['carrito'] = {}
        request.session.modified = True

    context = {
        'order_id': order_id,
        'tx_status': tx_status,
        'producto_id': productos_ids[0] if productos_ids else None,
        'productos_ids': productos_ids,
    }

    return render(request, 'pagos/payment_response.html', context)
    
@csrf_exempt
def webhook_bold(request):
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    try:
        data = json.loads(request.body)
    except:
        return JsonResponse({"error": "JSON inválido"}, status=400)

    print("📩 WEBHOOK DE BOLD RECIBIDO:", data)

    event = data.get("event")
    order_id = data.get("order_id")

    if not order_id:
        return JsonResponse({"error": "order_id faltante"}, status=400)

    # Buscar el pedido
    try:
        pedido = Pedido.objects.get(order_id=order_id)
    except Pedido.DoesNotExist:
        return JsonResponse({"error": "Pedido no encontrado"}, status=404)

    # Actualizar estados según el evento recibido
    if event == "payment_success":
        pedido.estado = "pagado"
        pedido.pago = True
    elif event == "payment_failed":
        pedido.estado = "fallido"
        pedido.pago = False
    elif event == "payment_refunded":
        pedido.estado = "reembolsado"

    pedido.save()

    return JsonResponse({"status": "ok"})