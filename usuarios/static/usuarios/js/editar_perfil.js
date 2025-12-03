// ==================== ALERTA GLOBAL ====================
function mostrarAlerta(titulo, mensaje, callbackAceptar = null, mostrarCancelar = false) {
    const alertOverlay = document.getElementById("custom-alert");
    const btnCancelar = document.getElementById("btn-cancelar");

    document.getElementById("alert-title").innerText = titulo;
    document.getElementById("alert-message").innerText = mensaje;

    alertOverlay.style.display = "flex";
    btnCancelar.style.display = mostrarCancelar ? "inline-block" : "none";

    document.getElementById("btn-aceptar").onclick = function () {
        alertOverlay.style.display = "none";
        if (callbackAceptar) callbackAceptar();
    };

    btnCancelar.onclick = function () {
        alertOverlay.style.display = "none";
    };
}
document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("profileForm");

    form.addEventListener("submit", function (e) {

        let nombre = form.nombre.value.trim();
        let email = form.email.value.trim();
        let telefono = form.phone_number.value.trim();

        // REGEX
        const regexNombre = /^[A-Za-zÁÉÍÓÚáéíóúñÑ\s]+$/;
        const regexEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        const regexTelefono = /^\d{10}$/;

        // === VALIDACIÓN NOMBRE ===
        if (nombre === "") {
            e.preventDefault();
            mostrarAlerta("Validación", "El nombre es obligatorio.");
            return;
        }
        if (!regexNombre.test(nombre)) {
            e.preventDefault();
            mostrarAlerta("Validación", "El nombre solo puede contener letras y espacios.");
            return;
        }

        // === VALIDACIÓN CORREO ===
        if (email === "") {
            e.preventDefault();
            mostrarAlerta("Validación", "El correo electrónico es obligatorio.");
            return;
        }
        if (!regexEmail.test(email)) {
            e.preventDefault();
            mostrarAlerta("Validación", "Ingrese un correo electrónico válido.");
            return;
        }

        // === VALIDACIÓN TELÉFONO ===
        if (telefono !== "") {
            if (!regexTelefono.test(telefono)) {
                e.preventDefault();
                mostrarAlerta("Validación", "El teléfono debe tener exactamente 10 dígitos numéricos.");
                return;
            }
        }
    });
});

// Desactivar botón al enviar el formulario
document.getElementById('profileForm').addEventListener('submit', function (e) {
    const btn = document.getElementById('btnGuardar');
    btn.disabled = true;
    btn.textContent = 'Actualizando...';
});