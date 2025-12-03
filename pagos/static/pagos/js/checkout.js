// ALERTA PERSONALIZADA
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

// VALIDACIÓN DE CAMPOS
function validarCampo(campo, regex, mensajeError) {
    const errorSpan = campo.parentElement.querySelector(".error");
    if (!regex.test(campo.value.trim())) {
        errorSpan.textContent = mensajeError;
        campo.classList.add("input-error");
        return false;
    }
    errorSpan.textContent = "";
    campo.classList.remove("input-error");
    return true;
}

// EVENTOS PRINCIPALES
document.addEventListener("DOMContentLoaded", function() {
    const form = document.getElementById("form-direccion");
    const nombre = document.getElementById("nombre");
    const telefono = document.getElementById("telefono");
    const direccion = document.getElementById("direccion");
    const ciudad = document.getElementById("ciudad");
    const codigo_postal = document.getElementById("codigo_postal");
    const notas = document.getElementById("notas");

    const btnEditar = document.querySelector('.btn-editar');
    const formSection = document.querySelector('.form-section');
    const checkoutContainer = document.querySelector('.checkout-container');

    // VALIDACIÓN EN TIEMPO REAL
    nombre.addEventListener("input", () => validarCampo(nombre, /^[A-Za-zÁÉÍÓÚáéíóúñÑ ]{3,30}$/, "Solo letras (3-30 caracteres)"));
    telefono.addEventListener("input", () => validarCampo(telefono, /^[0-9]{10}$/, "Debe tener 10 números"));
    direccion.addEventListener("input", () => validarCampo(direccion, /^.{5,60}$/, "Debe tener 5-60 caracteres"));
    ciudad.addEventListener("input", () => validarCampo(ciudad, /^[A-Za-zÁÉÍÓÚáéíóúñÑ ]{3,30}$/, "Ciudad inválida"));
    codigo_postal.addEventListener("input", () => validarCampo(codigo_postal, /^[0-9]{0,6}$/, "Máximo 6 números"));
    notas.addEventListener("input", () => validarCampo(notas, /^.{0,150}$/, "Máximo 150 caracteres"));

    // VALIDACIÓN FINAL AL ENVIAR
    form.addEventListener("submit", function(e) {
        const v1 = validarCampo(nombre, /^[A-Za-zÁÉÍÓÚáéíóúñÑ ]{3,30}$/, "Solo letras (3-30 caracteres)");
        const v2 = validarCampo(telefono, /^[0-9]{10}$/, "Debe tener 10 números");
        const v3 = validarCampo(direccion, /^.{5,60}$/, "Debe tener 5-60 caracteres");
        const v4 = validarCampo(ciudad, /^[A-Za-zÁÉÍÓÚáéíóúñÑ ]{3,30}$/, "Ciudad inválida");
        const v5 = validarCampo(codigo_postal, /^[0-9]{0,6}$/, "Máximo 6 números");
        const v6 = validarCampo(notas, /^.{0,150}$/, "Máximo 150 caracteres");

        if (!v1 || !v2 || !v3 || !v4 || !v5 || !v6) {
            e.preventDefault();
            mostrarAlerta("Formulario incompleto", "Por favor completa todos los campos correctamente.");
        }
    });

    // BOTÓN EDITAR INFORMACIÓN
    if (btnEditar) {
        btnEditar.addEventListener("click", function(e) {
            e.preventDefault();
            if (formSection) formSection.style.display = 'block';
            if (checkoutContainer) checkoutContainer.classList.remove('solo-resumen');
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }
});