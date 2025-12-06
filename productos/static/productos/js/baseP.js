document.addEventListener('DOMContentLoaded', function () {
    console.log('✅ baseP.js cargado');

    const iconoCarrito = document.getElementById("iconoCarrito");
    const carritoDropdown = document.getElementById("carritoDropdown");

    if (!iconoCarrito) {
        console.error('❌ element #iconoCarrito no encontrado');
        return;
    }
    if (!carritoDropdown) {
        console.error('❌ element #carritoDropdown no encontrado');
        return;
    }

    iconoCarrito.addEventListener('click', function (e) {
        e.preventDefault();
        e.stopPropagation();
        carritoDropdown.classList.toggle('show');
        console.log('🖱️ carrito toggle ->', carritoDropdown.classList.contains('show'));
    });

    // Cerrar al hacer click fuera
    document.addEventListener('click', function (e) {
        if (!iconoCarrito.contains(e.target) && !carritoDropdown.contains(e.target)) {
            carritoDropdown.classList.remove('show');
        }
    });

    // Abrir si viene de ?carrito=1
    if (window.location.search.includes("carrito=1")) {
        carritoDropdown.classList.add("show");
    }

    // Mensaje opcional para debugging
    console.log('iconoCarrito:', iconoCarrito, 'carritoDropdown:', carritoDropdown);

    // MENÚ USUARIO
    const userIcon = document.getElementById('userIcon');
    const menuUsuario = document.getElementById('menuUsuario');
    if (userIcon && menuUsuario) {
        userIcon.onclick = function (e) {
            e.stopPropagation();
            menuUsuario.style.display = menuUsuario.style.display === 'block' ? 'none' : 'block';
        };
        document.addEventListener("click", function (e) {
            if (!userIcon.contains(e.target) && !menuUsuario.contains(e.target)) {
                menuUsuario.style.display = 'none';
            }
        });
    }
});