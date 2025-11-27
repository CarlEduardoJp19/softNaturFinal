import random
import json
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.tokens import default_token_generator
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils.http import urlsafe_base64_decode
from django.views.decorators.csrf import csrf_exempt

from ..forms import LoginForm, UsuarioCreationForm
from ..models import Usuario
from ..utils import enviar_email_activacion
from productos.models import CarritoItem, Producto

User = get_user_model()

def register_view(request):
    if request.method == "POST":
        form = UsuarioCreationForm(request.POST)
        if form.is_valid():
            user = form.save()  # ya se guarda como is_active=False
            enviar_email_activacion(user, request)  # enviamos el correo de activación
            return render(request, "usuarios/confirmacion.html")  # mensaje de revisa tu correo
        else:
            print("❌ Errores del formulario:", form.errors)
    else:
        form = UsuarioCreationForm()
    return render(request, "usuarios/register.html", {"form": form})

def login_view(request):
    mensaje = ""

    if request.GET.get("inactividad") == "1":
        messages.error(request, "Tu sesión fue cerrada por inactividad.")

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            user = authenticate(request, username=email, password=password)
            if user is not None and user.rol == "cliente":
                login(request, user)

                # ✅ sincronizar carrito de sesión con BD
                carrito_sesion = request.session.get("carrito", {})
                for key, value in carrito_sesion.items():
                    producto_id = int(key)
                    cantidad = int(value["cantidad"])
                    producto = Producto.objects.get(id=producto_id)

                    item, creado = CarritoItem.objects.get_or_create(
                        usuario=user, producto=producto,
                        defaults={"cantidad": cantidad}
                    )
                    if not creado:
                        item.cantidad += cantidad
                        item.save()

                # ✅ cargar carrito de BD a la sesión
                carrito_db = CarritoItem.objects.filter(usuario=user)
                carrito_dict = {}
                for item in carrito_db:
                    carrito_dict[str(item.producto.id)] = {
                        "cantidad": item.cantidad,
                        "precio": float(item.producto.precio),
                        "nombProduc": item.producto.nombProduc,
                        "imgProduc": item.producto.imgProduc.url,
                    }
                request.session["carrito"] = carrito_dict
                request.session.modified = True

                return redirect('productos:producto')
            else:
                mensaje = "Correo o contraseña incorrectos o no eres cliente"
    else:
        form = LoginForm()

    return render(request, 'usuarios/login.html', {"form": form, "mensaje": mensaje})

def logout_view(request):
    logout(request)
    request.session.pop("carrito", None)

    if request.GET.get("inactividad") == "1":
        return redirect("/usuarios/login/?inactividad=1")

    return redirect("usuarios:login")

def login_admin(request):
    """
    Login de administrador con verificación por código (2 pasos)
    """
    if request.method == 'POST':
        # Si ya tiene el código ingresado
        if 'codigo_verificacion' in request.POST:
            codigo = request.POST.get('codigo_verificacion')
            email = request.POST.get('email_verified')
            password = request.POST.get('password_verified')

            cache_key = f'verification_code_{email}'
            codigo_guardado = cache.get(cache_key)

            if codigo_guardado is None:
                return render(request, 'usuarios/loginAdm.html', {
                    'mensaje': 'El código ha expirado. Solicita uno nuevo.'
                })

            if codigo != codigo_guardado:
                return render(request, 'usuarios/loginAdm.html', {
                    'mensaje': 'Código de verificación incorrecto.'
                })

            # Autenticar usuario
            user = authenticate(request, username=email, password=password)
            if user is not None and user.rol == 'admin':
                cache.delete(cache_key)
                login(request, user)
                return redirect('usuarios:dashboard')
            else:
                return render(request, 'usuarios/loginAdm.html', {
                    'mensaje': 'Error: usuario no válido o sin permisos.'
                })

        # Si es el primer paso (ingreso de credenciales)
        else:
            email = request.POST.get('email')
            password = request.POST.get('password')

            user = authenticate(request, username=email, password=password)
            if user is not None and user.rol == 'admin':
                # Generar y guardar código temporal
                codigo = ''.join([str(random.randint(0, 9)) for _ in range(6)])
                cache_key = f'verification_code_{email}'
                cache.set(cache_key, codigo, 600)  # 10 minutos

                # Enviar correo
                asunto = 'Código de verificación - Unidos pensando en su salud'
                mensaje = f'Tu código de verificación es: {codigo}'
                send_mail(asunto, mensaje, settings.DEFAULT_FROM_EMAIL, [email])

                return render(request, 'usuarios/loginAdm.html', {
                    'verificacion': True,
                    'email_verified': email,
                    'password_verified': password
                })
            else:
                return render(request, 'usuarios/loginAdm.html', {
                    'mensaje': 'Credenciales incorrectas o no eres administrador.'
                })

    return render(request, 'usuarios/loginAdm.html')

User = get_user_model()
@csrf_exempt
def enviar_codigo_verificacion(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            password = data.get('password')
            
            # Verificar credenciales
            user = authenticate(request, username=email, password=password)
            
            if user is None:
                return JsonResponse({
                    'success': False,
                    'mensaje': 'Credenciales incorrectas'
                })
            
            # Generar código de 6 dígitos
            codigo = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            
            # Guardar código en cache por 10 minutos
            cache_key = f'verification_code_{email}'
            cache.set(cache_key, codigo, 600)  # 600 segundos = 10 minutos
            
            # Enviar email con código
            asunto = 'Código de verificación - Unidos pensando en su salud'
            mensaje = f'''
Hola {user.nombre or 'Usuario'},

Tu código de verificación es: {codigo}

Este código expirará en 10 minutos.

Si no solicitaste este código, ignora este mensaje.

Saludos,
Equipo de Unidos pensando en su salud
            '''
            
            send_mail(
                asunto,
                mensaje,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
                html_message=f'''
                <html>
                    <body style="font-family: Arial; color: #333;">
                        <h2 style="color: #0066ff;">Código de verificación</h2>
                        <p>Hola <b>{user.nombre or 'Usuario'}</b>,</p>
                        <p>Tu código de verificación es:</p>
                        <div style="font-size: 22px; font-weight: bold; color: #d93025;">{codigo}</div>
                        <p>Este código expirará en 10 minutos.</p>
                        <p>Si no solicitaste este código, puedes ignorar este correo.</p>
                        <br>
                        <p style="font-size: 14px;">Equipo de <b>Unidos pensando en su salud</b></p>
                    </body>
                </html>
                '''
            )
            
            return JsonResponse({
                'success': True,
                'mensaje': 'Código enviado exitosamente al correo.'
            })
            
        except Exception as e:
            print(f"Error al enviar código: {str(e)}")
            return JsonResponse({
                'success': False,
                'mensaje': f'Error al enviar el código: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'mensaje': 'Método no permitido'})

def verificar_codigo(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            password = data.get('password')
            codigo_ingresado = data.get('codigo_verificacion')

            # Obtener código desde cache
            cache_key = f'verification_code_{email}'
            codigo_cache = cache.get(cache_key)

            # Obtener intentos desde cache
            intentos_key = f'intentos_codigo_{email}'
            intentos = cache.get(intentos_key, 0)

            # ✅ Verificar primero si es correcto
            if codigo_ingresado == codigo_cache:
                user = authenticate(request, username=email, password=password)
                if user:
                    login(request, user)
                    # Limpiar cache
                    cache.delete(cache_key)
                    cache.delete(intentos_key)
                    return JsonResponse({
                        'success': True,
                        'mensaje': 'Código correcto. Redirigiendo...',
                        'redirect_url': '/usuarios/dashboard/'
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'mensaje': 'Usuario o contraseña incorrectos. Vuelve a iniciar sesión.',
                        'redirect': True
                    })

            # Código incorrecto → aumentar intentos
            intentos += 1
            cache.set(intentos_key, intentos, 600)  # Guardar 10 minutos también

            if intentos >= 3:
                cache.delete(cache_key)
                cache.delete(intentos_key)
                return JsonResponse({
                    'success': False,
                    'mensaje': 'Has superado los 3 intentos. Vuelve a iniciar sesión.',
                    'redirect': True
                })

            return JsonResponse({
                'success': False,
                'mensaje': f'Código incorrecto. Intento {intentos} de 3.'
            })

        except Exception as e:
            print(f"Error al verificar código: {str(e)}")
            return JsonResponse({
                'success': False,
                'mensaje': f'Error al verificar el código: {str(e)}'
            })

    return JsonResponse({'success': False, 'mensaje': 'Método no permitido'})

User = get_user_model()

def activar_cuenta(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        return render(request, "usuarios/activado.html")
    else:
        return render(request, "usuarios/activacion_invalida.html")
