
/*******************************************
 *  GESTIÓN DE DEVOLUCIONES (ADMIN + AJAX)
 *******************************************/
const page = document.querySelector("[data-page='devoluciones']");

// CSRF desde <meta>
const CSRF_TOKEN = document.querySelector("meta[name='csrf-token']")?.content || "";

if (page) {
    console.log("JS cargado para gestión de devoluciones (AJAX)");

    let devolucionesData = [];

    // Cargar JSON
    try {
        devolucionesData = JSON.parse(document.getElementById("datosJson")?.textContent || "[]");
    } catch (e) {
        console.error("Error al procesar datos JSON:", e);
    }

    /*****************************
     *  MOSTRAR DETALLES EN MODAL
     *****************************/
    window.verDetalles = function (id) {
        id = parseInt(id);
        const d = devolucionesData.find(x => x.id === id);
        if (!d) return;

        // ---------------- FOTOS ----------------
        let fotosHTML = "";
        if (d.fotos?.length > 0) {
            fotosHTML = `<div class="galeria-fotos">`;
            d.fotos.forEach(foto => {
                fotosHTML += `
                    <div class="foto-item-modal" data-img="${foto}">
                        <img src="${foto}">
                    </div>`;
            });
            fotosHTML += `</div>`;
        } else {
            fotosHTML = `
                <div class="sin-fotos">
                    <i class="fa fa-image"></i>
                    <p>No se adjuntaron fotos</p>
                </div>`;
        }

        // ---------------- ACCIONES ----------------
        let accionesHTML = "";
        if (d.estado === "Pendiente") {
            accionesHTML = `
                <div class="acciones-modal">
                    <button class="btn-aprobar" data-action="aprobar" data-id="${d.id}">
                        <i class="fa fa-check"></i> Aprobar Devolución
                    </button>

                    <button class="btn-rechazar" data-action="rechazar" data-id="${d.id}">
                        <i class="fa fa-times"></i> Rechazar Devolución
                    </button>
                </div>`;
        }

        // ---------------- CONTENIDO ----------------
        document.getElementById("contenidoModal").innerHTML = `
            <div class="detalle-seccion">
                <h4><i class="fa fa-user"></i> Información del Cliente</h4>
                <div class="detalle-info">
                    <p><strong>Nombre:</strong> ${d.usuario_nombre}</p>
                    <p><strong>Email:</strong> ${d.usuario_email}</p>
                </div>
            </div>

            <div class="detalle-seccion">
                <h4><i class="fa fa-box"></i> Información del Producto</h4>
                <div class="detalle-info">
                    <p><strong>Producto:</strong> ${d.producto_nombre}</p>
                    <p><strong>Lote:</strong> ${d.lote}</p>
                    <p><strong>Pedido:</strong> #${d.pedido_id}</p>
                    <p><strong>Fecha de solicitud:</strong> ${d.fecha}</p>
                </div>
            </div>

            <div class="detalle-seccion">
                <h4><i class="fa fa-comment-dots"></i> Motivo</h4>
                <div class="detalle-info">
                    <p>${d.motivo}</p>
                </div>
            </div>

            <div class="detalle-seccion">
                <h4><i class="fa fa-camera"></i> Fotos</h4>
                ${fotosHTML}
            </div>

            ${accionesHTML}
        `;

        document.getElementById("modalDetalles").classList.add("active");
    };

    window.cerrarModal = () => {
        document.getElementById("modalDetalles").classList.remove("active");
    };

    /*****************************
     *  VER FOTO GRANDE (delegado)
     *****************************/
    document.addEventListener("click", e => {
        if (e.target.closest(".foto-item-modal")) {
            const src = e.target.closest(".foto-item-modal").dataset.img;
            document.getElementById("imagenGrande").src = src;
            document.getElementById("modalImagen").classList.add("active");
        }
    });

    window.cerrarImagen = () => {
        document.getElementById("modalImagen").classList.remove("active");
    };

    /*****************************
     *  MODAL DE RECHAZO
     *****************************/
    window.abrirModalRechazo = function(devolucionId) {
        document.getElementById('devolucionIdRechazo').value = devolucionId;
        document.getElementById('motivoRechazo').value = '';
        document.getElementById('modalRechazar').classList.add('active');
    };

    window.cerrarModalRechazo = function() {
        document.getElementById('modalRechazar').classList.remove('active');
    };

    /****************************************
     *   DELEGACIÓN PARA APROBAR / RECHAZAR
     ****************************************/
    document.addEventListener("click", e => {
        const btn = e.target.closest("[data-action]");
        if (!btn) return;

        const accion = btn.dataset.action;
        const id = parseInt(btn.dataset.id);

        // ⭐ Si es RECHAZAR, abrir el modal
        if (accion === "rechazar") {
            cerrarModal(); // Cerrar modal de detalles
            abrirModalRechazo(id);
        } 
        // ⭐ Si es APROBAR, ejecutar DIRECTAMENTE sin confirmación
        else if (accion === "aprobar") {
            enviarAccionAjax(id, accion);
        }
    });

    /****************************************
     *   ENVIAR FORMULARIO DE RECHAZO
     ****************************************/
    document.getElementById('formRechazo')?.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const devolucionId = document.getElementById('devolucionIdRechazo').value;
        const motivoRechazo = document.getElementById('motivoRechazo').value.trim();

        if (!motivoRechazo) {
            mostrarNotificacion('Debes escribir un motivo de rechazo');
            return;
        }

        // ⭐ Enviar como JSON (no FormData)
        enviarRechazoConMotivo(devolucionId, motivoRechazo);
    });

    /****************************************
     *   FUNCIÓN AJAX PARA APROBAR
     ****************************************/
    function enviarAccionAjax(id, tipo) {
        const url = `/usuarios/aprobar-devolucion/${id}/`;

        fetch(url, {
            method: "POST",
            headers: {
                "X-CSRFToken": getCookie('csrftoken'),
                "X-Requested-With": "XMLHttpRequest",
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ accion: tipo }),
        })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    // ⭐ SIN alert de éxito, solo actualizar la UI
                    const fila = document.getElementById(`devolucion-${id}`);
                    if (fila) {
                        const badge = fila.querySelector('.estado-badge');
                        badge.textContent = 'Aprobada';
                        badge.className = 'estado-badge estado-aprobada';
                        
                        const btnContainer = fila.querySelector('.botones-accion');
                        btnContainer.querySelectorAll('.btn-aprobar, .btn-rechazar').forEach(b => b.remove());
                    }

                    cerrarModal();
                    
                    // Opcional: Mostrar un mensaje sutil en lugar de alert
                    mostrarNotificacion('Devolución aprobada correctamente', 'success');
                } else {
                    mostrarNotificacion("Error: " + (data.error || 'No se pudo aprobar'), 'error');
                }
            })
            .catch(err => {
                console.error("Error en AJAX:", err);
                mostrarNotificacion('Error al procesar la solicitud', 'error');
            });
    }

    /****************************************
     *   FUNCIÓN AJAX PARA RECHAZAR CON MOTIVO
     *   ⭐ AHORA ENVÍA JSON EN LUGAR DE FORMDATA
     ****************************************/
    function enviarRechazoConMotivo(id, motivo) {
        const url = `/usuarios/rechazar-devolucion/${id}/`;

        fetch(url, {
            method: "POST",
            headers: {
                "X-CSRFToken": getCookie('csrftoken'),
                "X-Requested-With": "XMLHttpRequest",
                "Content-Type": "application/json",  // ⭐ Cambio importante
            },
            body: JSON.stringify({
                motivo_rechazo: motivo  // ⭐ Enviar como JSON
            })
        })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    // ⭐ SIN alert de éxito
                    cerrarModalRechazo();
                    
                    const fila = document.getElementById(`devolucion-${id}`);
                    if (fila) {
                        const badge = fila.querySelector('.estado-badge');
                        badge.textContent = 'Rechazada';
                        badge.className = 'estado-badge estado-rechazada';
                        
                        const btnContainer = fila.querySelector('.botones-accion');
                        btnContainer.querySelectorAll('.btn-aprobar, .btn-rechazar').forEach(b => b.remove());
                    }
                    
                    // Opcional: Mostrar un mensaje sutil
                    mostrarNotificacion('Devolución rechazada correctamente', 'error');
                } else {
                    mostrarNotificacion("Error: " + (data.error || 'No se pudo rechazar'), 'error');
                }
            })
            .catch(err => {
                console.error("Error en AJAX:", err);
                mostrarNotificacion('Error al procesar la solicitud', 'error');
            });
    }

    /****************************************
     *   NOTIFICACIÓN SUTIL (OPCIONAL)
     *   Sistema de mensajes no intrusivo
     ****************************************/
    function mostrarNotificacion(mensaje, tipo = 'success') {
        // Crear elemento de notificación
        const notif = document.createElement('div');
        notif.className = `notificacion notificacion-${tipo}`;
        notif.textContent = mensaje;
        notif.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            background: ${tipo === 'success' ? '#10b981' : '#ef4444'};
            color: white;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            z-index: 10000;
            animation: slideIn 0.3s ease-out;
        `;
        
        document.body.appendChild(notif);
        
        // Remover después de 3 segundos
        setTimeout(() => {
            notif.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => notif.remove(), 300);
        }, 3000);
    }

    /****************************************
     *   EXPORTAR A EXCEL
     ****************************************/
    window.exportarDevolucionesExcel = function() {
        const estado = document.getElementById('estadoFilter')?.value || '';
        window.location.href = `/usuarios/exportar-devoluciones-excel/?estado=${estado}`;
    }

    /****************************************
     *   OBTENER COOKIE CSRF
     ****************************************/
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
} // Fin devoluciones

/*********************************************
 *  GESTIÓN DE USUARIOS (Código original)
 *********************************************/
const page1 = document.querySelector("[data-page='gst-usuarios']");

if (page1) {
    console.log("JS cargado para gestión de usuarios");

    // ================= MODALES =================
    window.abrirModalAgregar = function () {
        document.getElementById("modal-agregar").style.display = "block";
        document.getElementById("modal-overlay").style.display = "block";
        document.body.style.overflow = "hidden";
    };

    window.cerrarModalAgregar = function () {
        document.getElementById("modal-agregar").style.display = "none";
        document.getElementById("modal-overlay").style.display = "none";
        document.body.style.overflow = "";
    };

    window.abrirModalEditar = function () {
        document.getElementById("modal-editar").style.display = "block";
        document.getElementById("modal-overlay").style.display = "block";
        document.body.style.overflow = "hidden";
    };

    window.cerrarModalEditar = function () {
        document.getElementById("modal-editar").style.display = "none";
        document.getElementById("modal-overlay").style.display = "none";
        document.body.style.overflow = "";
    };

    // ================= EVENTOS EDITAR =================
    document.addEventListener("DOMContentLoaded", function () {
        document.querySelectorAll(".editar:not([disabled])").forEach((boton) => {
            boton.addEventListener("click", function (e) {
                e.preventDefault();

                let userId = boton.dataset.id;

                document.getElementById("editar-id").value = userId;
                document.getElementById("editar-nombre").value = boton.dataset.nombre || "";
                document.getElementById("editar-email").value = boton.dataset.email || "";
                document.getElementById("editar-telefono").value = boton.dataset.telefono || "";
                document.getElementById("editar-rol").value = boton.dataset.rol || "cliente";

                document.getElementById("form-editar").action = `/usuarios/editar/${userId}/`;

                abrirModalEditar();
            });
        });
    });

    // ================= BUSCADOR UNIVERSAL =================
    function configurarBuscador(inputId, tableId, statsId, textoEntidad) {
        const searchInput = document.getElementById(inputId);
        const searchStats = statsId ? document.getElementById(statsId) : null;
        const tbody = document.querySelector(`#${tableId} tbody`);
        const rows = tbody
            ? tbody.querySelectorAll("tr[data-search-text]")
            : document.querySelectorAll(`#${tableId} tr[data-search-text]`);

        const totalRows = rows.length;

        function actualizarEstadisticas() {
            if (!searchStats) return;

            const visibles = Array.from(rows).filter(r => r.style.display !== "none").length;

            if (searchInput.value.trim() === "") {
                searchStats.textContent = `Mostrando ${totalRows} ${textoEntidad}${totalRows !== 1 ? "s" : ""}`;
            } else {
                searchStats.textContent = `Encontrados ${visibles} de ${totalRows} ${textoEntidad}${totalRows !== 1 ? "s" : ""}`;
            }
        }

        if (searchInput) {
            actualizarEstadisticas();

            searchInput.addEventListener("input", function () {
                const searchTerm = this.value.toLowerCase().trim();

                rows.forEach(row => {
                    const searchText = row.dataset.searchText || "";
                    row.style.display = searchText.includes(searchTerm) ? "" : "none";
                });

                actualizarEstadisticas();
            });
        }
    }

    configurarBuscador("searchInput", "usuariosTable", "searchStatsUsuarios", "usuario");
    configurarBuscador("searchInputCalif", "calificacionesTable", "searchStatsCalif", "calificación");
}
