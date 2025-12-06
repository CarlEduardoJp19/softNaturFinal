// Función para cerrar el modal de agotado
    function cerrarModal() {
        document.getElementById('modalNotificacion').classList.remove('show');
        // Limpiar URL
        window.history.replaceState({}, document.title, window.location.pathname);
    }
    
    // Función para cerrar el modal de stock máximo
    function cerrarModalStock() {
        document.getElementById('modalStockMaximo').classList.remove('show');
        // Limpiar URL pero mantener ?carrito=1
        window.history.replaceState({}, document.title, '{{ request.path }}?carrito=1');
    }
    
    // Verificar si hay parámetros en la URL al cargar la página
    window.addEventListener('DOMContentLoaded', function() {
        const urlParams = new URLSearchParams(window.location.search);
        
        // ⭐ Mostrar modal si producto sin stock
        if (urlParams.has('sin_stock')) {
            const nombreProducto = urlParams.get('nombre') || 'este producto';
            document.getElementById('mensajeModal').textContent = 
                `Lo sentimos, ${nombreProducto} está agotado temporalmente`;
            document.getElementById('modalNotificacion').classList.add('show');
        }
        
        // ⭐ Mostrar modal si stock máximo alcanzado
        if (urlParams.has('stock_maximo')) {
            const nombreProducto = urlParams.get('nombre') || 'este producto';
            document.getElementById('mensajeStockMaximo').textContent = 
                `Ya tienes todo el stock disponible de ${nombreProducto} en tu carrito`;
            document.getElementById('modalStockMaximo').classList.add('show');
        }
    });