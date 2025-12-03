from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse

from ..forms import EditarPerfilForm
from ..models import Pedido, Direccion


@login_required(login_url='usuarios:login')
def editar_perfil(request):
    user = request.user

    if request.method == 'POST':
        print("🔍 POST recibido")  # Para debug
        print("📦 Datos:", request.POST)  # Para debug
        
        form = EditarPerfilForm(request.POST, instance=user)
        
        if form.is_valid():
            form.save()
            print("✅ Guardado exitoso")  # Para debug
            messages.success(request, "Perfil actualizado correctamente.", extra_tags="perfil_editado")
            return redirect('usuarios:editar_perfil')
        else:
            print("❌ Errores:", form.errors)  # Para debug
            messages.error(request, "Hubo errores en el formulario.")
    else:
        form = EditarPerfilForm(instance=user)

    return render(request, 'usuarios/editar_perfil.html', {'form': form})

@login_required(login_url='usuarios:login')
def mis_pedidos(request):
    pedidos = (
        Pedido.objects
        .filter(usuario=request.user, pago=True)  # 👈 Solo los pagados
        .prefetch_related('items__producto')
        .order_by('-fecha_creacion')  # 👈 Los más recientes primero
    )
    return render(request, 'usuarios/mis_pedidos.html', {'pedidos': pedidos})

@login_required(login_url='usuarios:login')
def guardar_direccion(request):
    """Guarda la dirección de envío del usuario en la base de datos"""
    if request.method == 'POST':
        try:
            # Crear o actualizar la dirección principal del usuario
            direccion, creada = Direccion.objects.update_or_create(
                usuario=request.user,
                es_principal=True,
                defaults={
                    'nombre_completo': request.POST.get('nombre_completo', ''),
                    'telefono': request.POST.get('telefono', ''),
                    'direccion_completa': request.POST.get('direccion_completa', ''),
                    'ciudad': request.POST.get('ciudad', ''),
                    'codigo_postal': request.POST.get('codigo_postal', ''),
                    'notas_entrega': request.POST.get('notas_entrega', ''),
                }
            )
            
            if creada:
                messages.success(request, 'Dirección guardada correctamente.')
            else:
                messages.success(request, 'Dirección actualizada correctamente.')
                
        except Exception as e:
            messages.error(request, f'Error al guardar la dirección: {str(e)}')
    
    return redirect('pagos:checkout')

@login_required(login_url='usuarios:login')
def editar_direccion(request):
    """Permite al usuario editar su dirección guardada"""
    # 🔥 CORRECCIÓN: Usar reverse con parámetros GET
    from django.urls import reverse
    url = reverse('pagos:checkout')
    return redirect(f"{url}?editar=true")