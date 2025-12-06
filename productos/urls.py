from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

# Imports refactorizados
from .views import devoluciones  # Solo devoluciones en views.py principal
from .views_refactored.admin_views import (
    agregar_producto,
    editar_producto,
    list_product,
    exportar_inventario_excel,
    activar_producto,
    inactivar_producto,
    agregar_categoria,
    listar_categorias,
    editar_categoria,
    eliminar_categoria,
    agregar_lote,
)
from .views_refactored.carrito_views import (
    agregarAlCarrito,
    restar_producto,
    limpiar,
    actualizar_stock_carrito,
)
from .views_refactored.producto_views import (
    productos,
    productos_view,
    productos_por_categoria,
    detalle_producto,
    lote_activo,
)
from .views_refactored.calificacion_views import guardar_calificacion
from .views_refactored.home_views import homeSoft
from .views_refactored.chatbot_views import chatbot_ajax

app_name = 'productos'

urlpatterns = [
    # ============ PRODUCTOS (Vistas públicas) ============
    path('', productos_view, name="producto"),
    path('categoria/<int:categoria_id>/', productos_por_categoria, name='productos_por_categoria'),
    path("producto/<int:pk>/", detalle_producto, name="detalle"),
    path('lote_activo/<int:producto_id>/', lote_activo, name='lote_activo'),
    
    # ============ CARRITO ============
    path('agregar/<int:producto_id>/', agregarAlCarrito, name="agregar"),
    path('restar/<int:producto_id>/', restar_producto, name='restar'),
    path('limpiar/', limpiar, name="limpiar"),
    path('actualizar-stock-carrito/', actualizar_stock_carrito, name='actualizar_stock_carrito'),
    
    # ============ ADMIN - PRODUCTOS ============
    path('agregar_producto/', agregar_producto, name="agregar_producto"),
    path('editar/<int:id>/', editar_producto, name='editar_producto'),
    path('list_produc/', list_product, name='list_product'),
    path('exportar_excel/', exportar_inventario_excel, name='exportar_excel'),
    path('activar/<int:id>/', activar_producto, name='activar_producto'),
    path('inactivar/<int:id>/', inactivar_producto, name='inactivar_producto'),
    path('agregar_lote/', agregar_lote, name='agregar_lote'),
    
    # ============ ADMIN - CATEGORÍAS ============
    path('agregar_categoria/', agregar_categoria, name='agregar_categoria'),
    path("categorias/", listar_categorias, name="listar_categorias"),
    path("categorias/editar/<int:id>/", editar_categoria, name="editar_categoria"),
    path("categorias/eliminar/<int:id>/", eliminar_categoria, name="eliminar_categoria"),
    
    # ============ CALIFICACIONES ============
    path('guardar-calificacion/', guardar_calificacion, name='guardar_calificacion'),
    
    # ============ HOME ============
    path('homesoft/', homeSoft, name="homesoft"),
    
    # ============ DEVOLUCIONES ============
    path('devoluciones/', devoluciones, name='devoluciones'),
    
    # ============ CHATBOT ============
    path("chatbot/ask/", chatbot_ajax, name="chatbot_ajax"),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
