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
import logging
import traceback
import sys
from django.shortcuts import render
from django.conf import settings

from ..forms import LoginForm, UsuarioCreationForm
from ..models import Usuario
from ..utils import enviar_email_activacion
from productos.models import CarritoItem, Producto

User = get_user_model()

# Configurar logger
logger = logging.getLogger(__name__)

def register_view(request):
    logger.info("=" * 80)
    logger.info("🔵 INICIO - Vista de registro")
    logger.info(f"Método: {request.method}")
    logger.info(f"Path: {request.path}")
    logger.info("=" * 80)
    
    if request.method == "POST":
        logger.info("📝 POST recibido en registro")
        logger.info(f"Datos recibidos: {list(request.POST.keys())}")
        
        try:
            form = UsuarioCreationForm(request.POST)
            
            logger.info("🔍 Validando formulario...")
            
            if form.is_valid():
                logger.info("✅ Formulario válido")
                
                # Guardar usuario
                logger.info("💾 Guardando usuario en la base de datos...")
                user = form.save()
                
                logger.info(f"✅ Usuario guardado exitosamente:")
                logger.info(f"   ID: {user.id}")
                logger.info(f"   Email: {user.email}")
                logger.info(f"   Nombre: {user.nombre if hasattr(user, 'nombre') else 'N/A'}")
                logger.info(f"   Is Active: {user.is_active}")
                
                # Verificar configuración de email ANTES de enviar
                logger.info("=" * 80)
                logger.info("📧 CONFIGURACIÓN DE EMAIL")
                logger.info(f"Backend: {settings.EMAIL_BACKEND}")
                logger.info(f"From: {settings.DEFAULT_FROM_EMAIL}")
                logger.info(f"RESEND_API_KEY existe: {'✅' if settings.RESEND_API_KEY else '❌'}")
                if settings.RESEND_API_KEY:
                    logger.info(f"API Key preview: {settings.RESEND_API_KEY[:15]}...")
                logger.info("=" * 80)
                
                # Enviar email de activación
                logger.info("📤 Llamando a enviar_email_activacion()...")
                try:
                    enviar_email_activacion(user, request)
                    logger.info("✅ enviar_email_activacion() ejecutada sin errores")
                except Exception as email_error:
                    logger.error("=" * 80)
                    logger.error("❌ ERROR EN enviar_email_activacion()")
                    logger.error(f"Tipo: {type(email_error).__name__}")
                    logger.error(f"Mensaje: {str(email_error)}")
                    logger.error("Traceback:")
                    logger.error(traceback.format_exc())
                    logger.error("=" * 80)
                    
                    # Imprimir también a stderr
                    print("❌ ERROR EMAIL:", str(email_error), file=sys.stderr)
                    print(traceback.format_exc(), file=sys.stderr)
                    
                    # Re-lanzar el error para que se vea el 500
                    raise
                
                logger.info("🎉 Registro completado, mostrando página de confirmación")
                return render(request, "usuarios/confirmacion.html")
                
            else:
                logger.warning("⚠️ Formulario NO válido")
                logger.warning(f"Errores del formulario: {form.errors}")
                logger.warning(f"Errores en JSON: {form.errors.as_json()}")
                print("❌ Errores del formulario:", form.errors)
                
        except Exception as e:
            logger.error("=" * 80)
            logger.error("❌❌❌ ERROR CRÍTICO EN REGISTRO ❌❌❌")
            logger.error(f"Tipo: {type(e).__name__}")
            logger.error(f"Mensaje: {str(e)}")
            logger.error("Traceback completo:")
            logger.error(traceback.format_exc())
            logger.error("=" * 80)
            
            # Imprimir a stderr también
            print("=" * 80, file=sys.stderr)
            print("❌ ERROR CRÍTICO:", str(e), file=sys.stderr)
            print(traceback.format_exc(), file=sys.stderr)
            print("=" * 80, file=sys.stderr)
            
            # Re-lanzar para ver el error 500 real
            raise
            
    else:
        logger.info("📄 GET request - Mostrando formulario de registro")
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
