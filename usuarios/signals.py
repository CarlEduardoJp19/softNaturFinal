# usuarios/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Devolucion

@receiver(post_save, sender=Devolucion)
def enviar_correo_estado_devolucion(sender, instance, created, **kwargs):
    """
    Envía correos automáticamente cuando cambia el estado de una devolución.
    NO maneja stock (eso se hace en la vista).
    """

    if created:
        return  # no enviar nada cuando se crea una solicitud

    # ----------- CORREO: APROBADA --------------
    if instance.estado == "Aprobada":
        asunto = f"Devolución #{instance.id} aprobada"
        mensaje = f"""
Hola {instance.usuario.nombre},

Tu devolución del producto "{instance.producto.nombProduc}" ha sido APROBADA.
Pronto recibirás un reemplazo por tu producto de fecha (Vencimiento o estropeado).

Gracias por confiar en nosotros.
Equipo Unidos Pensando en su Salud.
"""
        send_mail(
            asunto, mensaje,
            settings.DEFAULT_FROM_EMAIL,
            [instance.usuario.email], fail_silently=False
        )

    # ----------- CORREO: RECHAZADA --------------
    elif instance.estado == "Rechazada":
        asunto = f"Devolución #{instance.id} rechazada"
        mensaje = f"""
Hola {instance.usuario.nombre},

Tu solicitud de devolución del producto "{instance.producto.nombProduc}" ha sido RECHAZADA.

Si crees que hubo un error, puedes comunicarte con nuestro soporte con nuestro número 3124824262.

Equipo Unidos Pensando en su Salud.
"""
        send_mail(
            asunto, mensaje,
            settings.DEFAULT_FROM_EMAIL,
            [instance.usuario.email], fail_silently=False
        )

    # ----------- CORREO: PRODUCTO EQUIVOCADO --------------
    elif instance.motivo == "Producto equivocado" and instance.estado == "Aprobada":
        # Este entra en la parte aprobada, pero lo dejo por claridad
        asunto = f"Devolución #{instance.id} por producto equivocado"
        mensaje = f"""
Hola {instance.usuario.nombre},

Confirmamos que tu devolución por **producto equivocado** ha sido gestionada.
El producto correcto será enviado.

Gracias por tu paciencia.
Equipo Unidos Pensando en su Salud.
"""
        send_mail(
            asunto, mensaje,
            settings.DEFAULT_FROM_EMAIL,
            [instance.usuario.email], fail_silently=False
        )
