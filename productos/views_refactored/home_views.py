from django.shortcuts import render
from ..models import Producto, Calificacion


# ---------------------- HOME ----------------------

def homeSoft(request):
    mas_vendidos = Producto.objects.filter(estado=True).order_by("vendidos")[:3]
    comentarios = Calificacion.objects.filter(aprobado=True).order_by('-fecha_creacion')
    return render(request, "productos/homeSoft.html", {
        "mas_vendidos": mas_vendidos,
        "comentarios": comentarios
    })