from django.shortcuts import render
from django.http import HttpResponse
from ..models import Producto, Calificacion


# ---------------------- CALIFICACIONES ----------------------

def guardar_calificacion(request):
    if request.method == 'POST':
        producto_id = request.POST.get('producto_id')
        puntuacion_servicio = request.POST.get('puntuacion_servicio')
        puntuacion_productos = request.POST.get('puntuacion_productos')
        comentario = request.POST.get('comentario')

        print("Datos recibidos:")
        print("producto_id:", producto_id)
        print("puntuacion_servicio:", puntuacion_servicio)
        print("puntuacion_productos:", puntuacion_productos)
        print("comentario:", comentario)

        try:
            producto = Producto.objects.get(id=producto_id)
        except Producto.DoesNotExist:
            return HttpResponse("❌ Producto no encontrado", status=404)

        usuario_obj = request.user

        Calificacion.objects.create(
            producto=producto,
            usuario=usuario_obj,
            puntuacion_servicio=int(puntuacion_servicio),
            puntuacion_productos=int(puntuacion_productos),
            comentario=comentario
        )

        print("✅ Calificación guardada correctamente")

        return render(request, 'productos/homeSoft.html')

    return HttpResponse("❌ Método no permitido", status=405)