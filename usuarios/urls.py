from django.urls import path, reverse_lazy
from django.conf import settings
from django.contrib.auth import views as auth_views
from . import views

app_name = 'usuarios'

urlpatterns = [
    # Autenticación
    path('login/', views.login_view, name="login"),
    path('register/', views.register_view, name="register"),
    path('logout/', views.logout_view, name="logout"),
    path('loginAdm/', views.login_admin, name="loginAdmin"),

    # Perfil y usuario
    path('editar-perfil/', views.editar_perfil, name='editar_perfil'),
    path('mis-pedidos/', views.mis_pedidos, name='mis_pedidos'),

    # Páginas informativas
    path('contacto/', views.contacto, name="contacto"),
    path('nosotros/', views.nosotros, name="nosotros"),

    # Panel y gestión
    path('dashboard/', views.dashboard, name="dashboard"),
    path('gstUsuarios/', views.gstUsuarios, name="gstUsuarios"),
    path('exportar_usuarios_excel/', views.exportar_usuarios_excel, name="exportar_usuarios_excel"),
    path('', views.gstUsuarios, name='gstUsuarios'),

    # Usuarios
    path('cambiar_estado/<int:usuario_id>/', views.cambiar_estado_usuario, name='cambiar_estado_usuario'),
    path('agregar/', views.agregar_usuario, name='agregar_usuario'),
    path("editar/<int:pk>/", views.editar_usuario, name="editar_usuario"),

    # Informes
    path('informe-calificaciones/', views.informe_calificaciones, name='informe_calificaciones'),
    path('ventas/', views.informe_ventas, name='informe_ventas'),
    path('exportar-ventas-excel/', views.exportar_ventas_excel, name='exportar_ventas_excel'),
    path('productos-mas-vendidos/', views.productos_mas_vendidos_view, name="productos_mas_vendidos"),
    path('usuarios-frecuentes/', views.usuarios_frecuentes_view, name="usuarios_frecuentes"),

    # Comentarios
    path('comentario/<int:id>/aprobar/', views.aprobar_comentario, name="aprobar_comentario"),
    path('comentario/<int:id>/rechazar/', views.rechazar_comentario, name="rechazar_comentario"),

    # Pedidos
    path('pedidos/', views.pedidos_view, name="pedidos"),
    path('exportar-pedidos-excel/', views.exportar_pedidos_excel, name='exportar_pedidos_excel'),
    path('pedidos/<int:pedido_id>/cambiar-estado/', views.cambiar_estado_pedido, name='cambiar_estado_pedido'),
    path('detalle_pedido/<int:pedido_id>/', views.detalle_pedido, name='detalle_pedido'),
    path('cambiar_estado_pedido/<int:pedido_id>/', views.cambiar_estado_pedido, name='cambiar_estado_pedido'),

    # Activación y verificación
    path('activar/<uidb64>/<token>/', views.activar_cuenta, name="activar"),
    path('enviar-codigo-verificacion/', views.enviar_codigo_verificacion, name='enviar_codigo'),
    path('verificar-codigo/', views.verificar_codigo, name='verificar_codigo'),

    # ====================== URLS DE DEVOLUCIONES (ADMIN) - AGREGADAS ======================
    path('gst-devoluciones/', views.gst_devoluciones, name='gst_devoluciones'),
    path('historial-devoluciones/', views.historial_devoluciones, name='historial_devoluciones'),
    path('aprobar-devolucion/<int:devolucion_id>/', views.aprobar_devolucion, name='aprobar_devolucion'),
    path('rechazar-devolucion/<int:devolucion_id>/', views.rechazar_devolucion, name='rechazar_devolucion'),
    path('exportar-devoluciones-excel/', views.exportar_devoluciones_excel, name='exportar_devoluciones_excel'),
    # ====================== FIN URLS DEVOLUCIONES ======================
    path('guardar-direccion/', views.guardar_direccion, name='guardar_direccion'),
    path('editar-direccion/', views.editar_direccion, name='editar_direccion'),  # 👈 NUEVA RUTA AGREGADA

    # Recuperación de contraseña
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
