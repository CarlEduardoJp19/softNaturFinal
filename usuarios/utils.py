from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse

def enviar_email_activacion(user, request):
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))

    # construye link absoluto: http://127.0.0.1:8000/activar/uid/token/
    link = request.build_absolute_uri(
        reverse("usuarios:activar", kwargs={"uidb64": uid, "token": token})
    )

    asunto = "Activa tu cuenta"
    mensaje = f"Hola {user.nombre}, por favor activa tu cuenta dando clic en el siguiente enlace:\n\n{link}"

    send_mail(asunto, mensaje, settings.DEFAULT_FROM_EMAIL, [user.email])