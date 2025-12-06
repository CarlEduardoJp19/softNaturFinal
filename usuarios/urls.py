from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views  # ← Para devoluciones (views.py original)
from .views_refactored import (  # ← Para todo lo refactorizado
    auth_views as custom_auth_views,  # Renombrado para evitar conflicto
    public_views,
    dashboard_views,
    admin_views,
    perfil_views,
    exportacion_views,
)

app_name = 'usuarios'

urlpatterns = [
    # ==================== AUTENTICACIÓN ====================
    path('login/', custom_auth_views.login_view, name="login"),
    path('register/', custom_auth_views.register_view, name="register"),
    path('logout/', custom_auth_views.logout_view, name="logout"),
    path('loginAdm/', custom_auth_views.login_admin, name="loginAdmin"),
    
    # Activación y verificación
    path('activar/<uidb64>/<token>/', custom_auth_views.activar_cuenta, name="activar"),
    path('enviar-codigo-verificacion/', custom_auth_views.enviar_codigo_verificacion, name='enviar_codigo'),
    path('verificar-codigo/', custom_auth_views.verificar_codigo, name='verificar_codigo'),

    # ==================== PERFIL Y USUARIO ====================
    path('editar-perfil/', perfil_views.editar_perfil, name='editar_perfil'),
    path('mis-pedidos/', perfil_views.mis_pedidos, name='mis_pedidos'),
    path('guardar-direccion/', perfil_views.guardar_direccion, name='guardar_direccion'),
    path('editar-direccion/', perfil_views.editar_direccion, name='editar_direccion'),

    # ==================== PÁGINAS INFORMATIVAS ====================
    path('contacto/', dashboard_views.contacto, name="contacto"),
    path('nosotros/', public_views.nosotros, name="nosotros"),

    # ==================== PANEL Y GESTIÓN (ADMIN) ====================
    path('dashboard/', dashboard_views.dashboard, name="dashboard"),
    path('dashboard/exportar-excel/', exportacion_views.exportar_dashboard_excel, name='exportar_dashboard_excel'),
    path('gstUsuarios/', admin_views.gstUsuarios, name="gstUsuarios"),
    path('', admin_views.gstUsuarios, name='gstUsuarios'),  # Ruta raíz

    # ==================== GESTIÓN DE USUARIOS (ADMIN) ====================
    path('exportar_usuarios_excel/', exportacion_views.exportar_usuarios_excel, name="exportar_usuarios_excel"),
    path('cambiar_estado/<int:usuario_id>/', admin_views.cambiar_estado_usuario, name='cambiar_estado_usuario'),
    path('agregar/', admin_views.agregar_usuario, name='agregar_usuario'),
    path("editar/<int:pk>/", admin_views.editar_usuario, name="editar_usuario"),

    # ==================== INFORMES (ADMIN) ====================
    path('informe-calificaciones/', admin_views.informe_calificaciones, name='informe_calificaciones'),
    path('ventas/', admin_views.informe_ventas, name='informe_ventas'),
    path('exportar-ventas-excel/', exportacion_views.exportar_ventas_excel, name='exportar_ventas_excel'),
    # ❌ ELIMINADAS (ya no existen): productos_mas_vendidos_view, usuarios_frecuentes_view

    # ==================== COMENTARIOS/CALIFICACIONES ====================
    path('comentario/<int:id>/aprobar/', admin_views.aprobar_comentario, name="aprobar_comentario"),
    path('comentario/<int:id>/rechazar/', admin_views.rechazar_comentario, name="rechazar_comentario"),

    # ==================== PEDIDOS (ADMIN) ====================
    path('pedidos/', admin_views.pedidos_view, name="pedidos"),
    path('pedidos/exportar/', exportacion_views.exportar_pedidos_excel, name='exportar_pedidos_excel'),
    path('pedidos/<int:pedido_id>/cambiar-estado/', admin_views.cambiar_estado_pedido, name='cambiar_estado_pedido'),
    path('detalle_pedido/<int:pedido_id>/', admin_views.detalle_pedido, name='detalle_pedido'),
    path('cambiar_estado_pedido/<int:pedido_id>/', admin_views.cambiar_estado_pedido, name='cambiar_estado_pedido'),  # Duplicada (se puede eliminar)

    # ==================== DEVOLUCIONES (views.py original - SIN TOCAR) ====================
    path('gst-devoluciones/', views.gst_devoluciones, name='gst_devoluciones'),
    path('historial-devoluciones/', views.historial_devoluciones, name='historial_devoluciones'),
    path('aprobar-devolucion/<int:devolucion_id>/', views.aprobar_devolucion, name='aprobar_devolucion'),
    path('rechazar-devolucion/<int:devolucion_id>/', views.rechazar_devolucion, name='rechazar_devolucion'),
    path('exportar-devoluciones-excel/', views.exportar_devoluciones_excel, name='exportar_devoluciones_excel'),

    # ==================== RECUPERACIÓN DE CONTRASEÑA (Django Auth) ====================
    path(
        'password_reset/',
        auth_views.PasswordResetView.as_view(
            template_name='registration/password_reset_form.html',
            email_template_name='registration/password_reset_email.html',
            success_url=reverse_lazy('usuarios:password_reset_done')
        ),
        name='password_reset'
    ),
    path(
        'password_reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='registration/password_reset_done.html'
        ),
        name='password_reset_done'
    ),
    path(
        'reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='registration/password_reset_confirm.html',
            success_url=reverse_lazy('usuarios:password_reset_complete')
        ),
        name='password_reset_confirm'
    ),
    path(
        'reset/done/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='registration/password_reset_complete.html'
        ),
        name='password_reset_complete'
    ),
]

