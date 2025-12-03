document.addEventListener("DOMContentLoaded", function () {
    // ----- ELEMENTOS DEL FORMULARIO -----
    const form = document.querySelector("form");
    const nombre = document.getElementById("id_nombProduc");
    const descripcion = document.getElementById("id_descripcion");
    const precio = document.getElementById("id_precio");
    const categoria = document.getElementById("id_Categoria");
    const stock = document.getElementById("id_stock");
    const fechaCaducidad = document.getElementById("id_fecha_caducidad");
    const imgProduc = document.getElementById("id_imgProduc");

    // ----- ALERTA PERSONALIZADA -----
    const alertOverlay = document.getElementById("custom-alert");
    const btnAceptar = document.getElementById("btn-aceptar");
    const btnCancelar = document.getElementById("btn-cancelar");

    function cerrarAlerta() {
        if (alertOverlay) {
            alertOverlay.style.display = "none";
        }
    }

    function mostrarAlerta(titulo, mensaje) {
        if (!alertOverlay) return;
        
        document.getElementById("alert-title").innerText = titulo;
        document.getElementById("alert-message").innerText = mensaje;
        alertOverlay.style.display = "flex";
    }

    // Eventos para cerrar la alerta
    if (btnAceptar) {
        btnAceptar.onclick = cerrarAlerta;
    }

    if (btnCancelar) {
        btnCancelar.onclick = cerrarAlerta;
    }

    // Cerrar al hacer clic fuera del modal
    if (alertOverlay) {
        alertOverlay.addEventListener('click', function(e) {
            if (e.target === this) {
                cerrarAlerta();
            }
        });
    }

    // Cerrar con tecla ESC
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && alertOverlay && alertOverlay.style.display === 'flex') {
            cerrarAlerta();
        }
    });

    // ----- FUNCIONES DE VALIDACIÓN -----
    function validarTexto(campo, min, max) {
        const regex = /^[A-Za-zÁÉÍÓÚáéíóúñÑ ]+$/;
        if (!regex.test(campo.value.trim()) || campo.value.trim().length < min || campo.value.trim().length > max) {
            return false;
        }
        return true;
    }

    function validarNumero(campo, min, max) {
        const valor = parseFloat(campo.value);
        if (isNaN(valor) || valor < min || valor > max) {
            return false;
        }
        return true;
    }

    function validarFecha(campo) {
        return campo.value.trim() !== "";
    }

    function validarImagen(campo) {
        // Permite solo archivos .jpg, .jpeg, .png
        if (campo.value === "") return true; // No obligatorio
        const extensiones = /(\.jpg|\.jpeg|\.png)$/i;
        return extensiones.test(campo.value);
    }

    // ----- VALIDACIÓN AL ENVIAR -----
    if (form) {
        form.addEventListener("submit", function (e) {
            let errores = [];

            if (!validarTexto(nombre, 3, 50)) {
                errores.push("• Nombre: solo letras y 3-50 caracteres");
            }
            if (!validarTexto(descripcion, 5, 200)) {
                errores.push("• Descripción: 5-200 caracteres");
            }
            if (!validarNumero(precio, 0, 1000000)) {
                errores.push("• Precio: debe ser un número positivo");
            }
            if (!validarNumero(stock, 0, 1000000)) {
                errores.push("• Stock: debe ser un número positivo");
            }
            if (!validarFecha(fechaCaducidad)) {
                errores.push("• Fecha de caducidad: campo obligatorio");
            }
            if (!validarImagen(imgProduc)) {
                errores.push("• Imagen: solo archivos .jpg, .jpeg o .png");
            }

            if (errores.length > 0) {
                e.preventDefault();
                mostrarAlerta("Formulario incompleto", errores.join("\n"));
            } else {
                // Bloquear botón de envío
                const btnGuardar = form.querySelector('.btn-guardar-Editar');
                if (btnGuardar) {
                    btnGuardar.disabled = true;
                    btnGuardar.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Guardando...';
                }
            }
        });
    }
});