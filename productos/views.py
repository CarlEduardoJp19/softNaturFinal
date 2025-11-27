from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from usuarios.decorators import login_required
from usuarios.models import Pedido, Devolucion
from .models import Producto
import json

@login_required
def devoluciones(request):
    """Vista para que el cliente solicite devoluciones por unidad"""
    # Cambiar de 30 días a 10 días
    hace_10_dias = timezone.now() - timedelta(days=10)
    pedidos = Pedido.objects.filter(
        usuario=request.user,
        estado='entregado',
        fecha_creacion__gte=hace_10_dias
    ).prefetch_related('items__producto').order_by('-fecha_creacion')

    # Devoluciones existentes (cualquier estado, no solo Pendiente)
    # Esto evita que se pueda devolver un producto ya devuelto
    devoluciones_existentes = Devolucion.objects.filter(
        usuario=request.user
    ).values_list('producto_id', 'pedido_id', 'unidad')
    devoluciones_existentes = [(int(p), int(d), int(u)) for p, d, u in devoluciones_existentes]

    productos_devolubles = []
    pedidos_agrupados = {}

    for pedido in pedidos:
        # Verificar que el pedido tenga menos de 10 días
        dias_transcurridos = (timezone.now() - pedido.fecha_creacion).days
        if dias_transcurridos > 10:
            continue  # Saltar pedidos con más de 10 días
        
        items = pedido.items.all()
        unidades_disponibles = 0
        
        for item in items:
            cantidad = getattr(item, 'cantidad', 1) or 1
            for unidad_index in range(cantidad):
                unidad_num = unidad_index + 1
                key = (getattr(item.producto, 'id', None), pedido.id, unidad_num)
                
                # Si ya existe una devolución para esta unidad, no mostrarla
                if key in devoluciones_existentes:
                    continue
                
                unidades_disponibles += 1

                # Normalizar lote a string para JSON
                lote_val = getattr(item, 'lote', None)
                if lote_val is None:
                    lote_str = ''
                elif isinstance(lote_val, str):
                    lote_str = lote_val
                else:
                    lote_str = getattr(lote_val, 'codigo_lote', None) or getattr(lote_val, 'codigo', None) or str(lote_val)

                productos_devolubles.append({
                    'pedido_id': pedido.id,
                    'producto_id': getattr(item.producto, 'id', None),
                    'producto_nombre': getattr(item.producto, 'nombProduc', str(item.producto)),
                    'unidad': unidad_num,
                    'precio': float(getattr(item, 'precio_unitario', 0) or 0),
                    'item_id': item.id,
                    'lote': lote_str,
                    'codigo_lote': lote_str,
                    'fecha_pedido': pedido.fecha_creacion.strftime('%d/%m/%Y') if getattr(pedido, 'fecha_creacion', None) else ''
                })

        if unidades_disponibles > 0:
            pedidos_agrupados[pedido.id] = {
                'pedido_id': pedido.id,
                'fecha_pedido': pedido.fecha_creacion.strftime('%d/%m/%Y'),
                'cantidad_productos': unidades_disponibles,
                'dias_restantes': 10 - dias_transcurridos  # Días que le quedan para devolver
            }

    # POST: crear devolución
    if request.method == 'POST':
        try:
            pedido_id = int(request.POST.get('pedido_id'))
            motivo = request.POST.get('motivo')
            foto1 = request.FILES.get('foto1')
            foto2 = request.FILES.get('foto2')
            foto3 = request.FILES.get('foto3')
            
            # Procesar producto_data
            producto_data = request.POST.get('producto_id')
            
            if '|' in producto_data:
                # Formato: producto_id|item_id|lote_codigo
                datos = producto_data.split('|')
                producto_id = int(datos[0])
                item_id = int(datos[1]) if len(datos) > 1 and datos[1] and datos[1] != 'None' else None
                lote_codigo = datos[2] if len(datos) > 2 else ''
            elif '-' in producto_data:
                # Formato antiguo: producto_id-unidad
                producto_id, _ = map(int, producto_data.split('-'))
                item_id = None
                lote_codigo = ''
            else:
                producto_id = int(producto_data)
                item_id = None
                lote_codigo = ''
            
            # Obtener unidad del POST
            unidad = int(request.POST.get('unidad', 1))

            # Validar campos obligatorios
            if not producto_id or not pedido_id or not motivo or not unidad:
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({"success": False, "mensaje": "Completa todos los campos"})
                messages.error(request, "Por favor completa todos los campos obligatorios")
                return redirect('productos:devoluciones')

            # Obtener producto y pedido
            producto = Producto.objects.get(id=producto_id)
            pedido = Pedido.objects.get(id=pedido_id, usuario=request.user, estado='entregado')
            
            # Buscar el pedido_item con mejor precisión
            pedido_item = None
            
            # Opción 1: Si tenemos item_id, usarlo directamente
            if item_id:
                pedido_item = pedido.items.filter(id=item_id, producto=producto).first()
            
            # Opción 2: Si no hay item_id, buscar por producto
            if not pedido_item:
                items_producto = pedido.items.filter(producto=producto)
                
                # Si solo hay un item con ese producto, usarlo
                if items_producto.count() == 1:
                    pedido_item = items_producto.first()
                # Si hay múltiples, intentar filtrar por lote si está disponible
                elif items_producto.count() > 1 and lote_codigo:
                    # Intentar filtrar por lote
                    for item in items_producto:
                        item_lote = getattr(item, 'lote', None)
                        if item_lote:
                            if isinstance(item_lote, str):
                                if item_lote == lote_codigo:
                                    pedido_item = item
                                    break
                            else:
                                lote_code = getattr(item_lote, 'codigo_lote', None) or getattr(item_lote, 'codigo', None)
                                if lote_code == lote_codigo:
                                    pedido_item = item
                                    break
                    
                    # Si no se encontró por lote, tomar el primero
                    if not pedido_item:
                        pedido_item = items_producto.first()
                else:
                    # Tomar el primero disponible
                    pedido_item = items_producto.first()

            if not pedido_item:
                error_msg = f"No se encontró el producto en el pedido. Producto ID: {producto_id}, Pedido ID: {pedido_id}, Item ID: {item_id}"
                print(error_msg)  # Para debug en logs
                
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({"success": False, "mensaje": "No se encontró el producto en el pedido"})
                messages.error(request, "No se encontró el producto en el pedido")
                return redirect('productos:devoluciones')

            # Verificar cantidad disponible en el item
            cantidad_item = getattr(pedido_item, 'cantidad', 1) or 1
            if unidad > cantidad_item:
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({"success": False, "mensaje": f"La unidad {unidad} no existe en este producto (máx: {cantidad_item})"})
                messages.error(request, f"La unidad {unidad} no existe en este producto")
                return redirect('productos:devoluciones')

            # Verificar devolución existente (cualquier estado)
            devolucion_existente = Devolucion.objects.filter(
                usuario=request.user,
                producto=producto,
                pedido=pedido,
                unidad=unidad
            ).exists()

            if devolucion_existente:
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({"success": False, "mensaje": "Ya existe una devolución para esta unidad"})
                messages.warning(request, "Ya existe una solicitud de devolución para esta unidad.")
                return redirect('productos:devoluciones')
            
            # Verificar que el pedido tenga menos de 10 días
            dias_transcurridos = (timezone.now() - pedido.fecha_creacion).days
            if dias_transcurridos > 10:
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({"success": False, "mensaje": "Este pedido tiene más de 10 días. Ya no puedes solicitar devoluciones."})
                messages.error(request, "Este pedido tiene más de 10 días. Ya no puedes solicitar devoluciones.")
                return redirect('productos:devoluciones')

            # Obtener el lote del pedido_item
            lote_obj = getattr(pedido_item, 'lote', None)

            # Crear devolución
            devolucion = Devolucion(
                usuario=request.user,
                producto=producto,
                pedido=pedido,
                item=pedido_item,
                lote=lote_obj,
                motivo=motivo,
                estado='Pendiente',
                unidad=unidad,
                seleccionada=True
            )

            if foto1:
                devolucion.foto1 = foto1
            if foto2:
                devolucion.foto2 = foto2
            if foto3:
                devolucion.foto3 = foto3

            devolucion.save()

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    "success": True,
                    "producto_id": producto.id,
                    "pedido_id": pedido.id,
                    "unidad": unidad,
                    "mensaje": f"Devolución #{devolucion.id} enviada exitosamente"
                })

            messages.success(request, f"✅ Solicitud de devolución #{devolucion.id} enviada exitosamente!")
            return redirect('productos:devoluciones')

        except Producto.DoesNotExist:
            error_msg = "Producto no encontrado"
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({"success": False, "mensaje": error_msg})
            messages.error(request, error_msg)
            return redirect('productos:devoluciones')
            
        except Pedido.DoesNotExist:
            error_msg = "Pedido no encontrado o no autorizado"
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({"success": False, "mensaje": error_msg})
            messages.error(request, error_msg)
            return redirect('productos:devoluciones')
            
        except ValueError as e:
            error_msg = f"Error en los datos enviados: {str(e)}"
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({"success": False, "mensaje": error_msg})
            messages.error(request, error_msg)
            return redirect('productos:devoluciones')
            
        except Exception as e:
            error_msg = f"Error inesperado: {str(e)}"
            print(f"Error en devoluciones: {error_msg}")  # Para logs
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({"success": False, "mensaje": "Ocurrió un error al procesar la devolución"})
            messages.error(request, error_msg)
            return redirect('productos:devoluciones')

    # Serializar JSON
    productos_json = json.dumps(productos_devolubles, default=str, ensure_ascii=False)
    mis_devoluciones = Devolucion.objects.filter(
        usuario=request.user
    ).select_related('producto', 'pedido').order_by('-fecha_solicitud')
    
    # Timestamp para cache busting
    import time
    timestamp = str(int(time.time()))

    context = {
        'productos_devolubles': productos_json,
        'pedidos_agrupados': pedidos_agrupados.values(),
        'devoluciones': mis_devoluciones,
        'timestamp': timestamp  # Para evitar caché
    }

    return render(request, 'productos/devoluciones.html', context)# Configurar la API Key de Gemini


