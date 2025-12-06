document.addEventListener('DOMContentLoaded', () => {
    // ====== DATOS DE PRODUCTOS ======
    const productosScript = document.getElementById('productosData');
    const todosLosProductos = productosScript ? JSON.parse(productosScript.textContent) : [];
    console.log('Productos cargados:', todosLosProductos);

    // ====== CAMBIAR TABS ======
    function cambiarTab(tab, event) {
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.getElementById(tab).classList.add('active');
        event.currentTarget.classList.add('active');
    }
    window.cambiarTab = cambiarTab;

    // ====== CARGAR PRODUCTOS SEGÚN PEDIDO ======
    function cargarProductos() {
        const selectPedido = document.getElementById('selectPedido');
        const selectProducto = document.getElementById('selectProducto');
        const grupoProducto = document.getElementById('grupoProducto');
        const grupoLote = document.getElementById('grupoLote');

        const pedidoSeleccionado = selectPedido.value;
        if (!pedidoSeleccionado) {
            grupoProducto.style.display = 'none';
            grupoLote.style.display = 'none';
            selectProducto.innerHTML = '<option value="">-- Primero selecciona un pedido --</option>';
            verificarFormulario(); // ⭐ Verificar estado del formulario
            return;
        }

        const pedidoId = parseInt(pedidoSeleccionado);
        const productos = todosLosProductos.filter(p => p.pedido_id === pedidoId);

        selectProducto.innerHTML = '<option value="">-- Selecciona el producto --</option>';
        productos.forEach(p => {
            const option = document.createElement('option');
            option.value = `${p.producto_id}|${p.item_id}|${p.codigo_lote || ''}`;
            option.setAttribute('data-unidad', p.unidad);
            option.textContent = `${p.producto_nombre} - Unidad ${p.unidad} - Lote ${p.codigo_lote || 'Sin lote'} - $${p.precio}`;
            selectProducto.appendChild(option);
        });

        grupoProducto.style.display = 'block';
        grupoLote.style.display = 'none';
        verificarFormulario(); // ⭐ Verificar estado del formulario
    }
    window.cargarProductos = cargarProductos;

    // ====== MOSTRAR LOTE ======
    const selectProducto = document.getElementById('selectProducto');
    const grupoLote = document.getElementById('grupoLote');
    const textoLote = document.getElementById('textoLote');

    if (selectProducto) {
        selectProducto.addEventListener('change', function () {
            const selected = this.options[this.selectedIndex];
            if (!selected || !selected.value) {
                grupoLote.style.display = 'none';
                textoLote.textContent = '';
                verificarFormulario(); // ⭐ Verificar estado del formulario
                return;
            }

            const [productoId, itemId, lotecodigo] = selected.value.split('|');
            console.log('Producto seleccionado - Lote:', lotecodigo);

            if (lotecodigo && lotecodigo.trim() !== '') {
                textoLote.textContent = lotecodigo;
                grupoLote.style.display = 'block';
            } else {
                textoLote.textContent = 'Sin lote asignado';
                grupoLote.style.display = 'block';
            }
            
            verificarFormulario(); // ⭐ Verificar estado del formulario
        });
    }

    // ====== SISTEMA DE FOTOS ======
    let fotosCapturadas = [];
    const MAX_FOTOS = 3;
    const btnAbrirCamara = document.getElementById('btnAbrirCamara');
    const btnCerrarModal = document.getElementById('btnCerrarModal');
    const btnCapturar = document.getElementById('btnCapturar');
    const modalCamara = document.getElementById('modalCamara');
    const videoElement = document.getElementById('videoElement');
    const canvasElement = document.getElementById('canvasElement');
    const previewGrid = document.getElementById('previewGrid');
    const contadorFotos = document.getElementById('contadorFotos');
    const inputArchivo = document.getElementById('inputArchivo');
    const inputFoto1 = document.getElementById('foto1');
    const inputFoto2 = document.getElementById('foto2');
    const inputFoto3 = document.getElementById('foto3');
    let stream = null;

    function actualizarInputs() {
        const dt1 = new DataTransfer();
        const dt2 = new DataTransfer();
        const dt3 = new DataTransfer();

        if (fotosCapturadas[0]) dt1.items.add(fotosCapturadas[0]);
        if (fotosCapturadas[1]) dt2.items.add(fotosCapturadas[1]);
        if (fotosCapturadas[2]) dt3.items.add(fotosCapturadas[2]);

        inputFoto1.files = dt1.files;
        inputFoto2.files = dt2.files;
        inputFoto3.files = dt3.files;
    }

    function actualizarPreview() {
        previewGrid.innerHTML = '';
        fotosCapturadas.forEach((file, index) => {
            const url = URL.createObjectURL(file);
            const div = document.createElement('div');
            div.className = 'foto-item';
            div.innerHTML = `
                <img src="${url}" alt="Foto ${index + 1}">
                <button type="button" class="btn-eliminar-foto" onclick="eliminarFoto(${index})">
                    <i class="fa fa-times"></i>
                </button>
            `;
            previewGrid.appendChild(div);
        });

        for (let i = fotosCapturadas.length; i < MAX_FOTOS; i++) {
            const div = document.createElement('div');
            div.className = 'foto-item empty';
            div.innerHTML = '<i class="fa fa-image"></i>';
            previewGrid.appendChild(div);
        }

        contadorFotos.textContent = fotosCapturadas.length;
        actualizarInputs();
        btnAbrirCamara.disabled = fotosCapturadas.length >= MAX_FOTOS;
        document.querySelector('.btn-archivo').disabled = fotosCapturadas.length >= MAX_FOTOS;
        
        verificarFormulario(); // ⭐ Verificar estado del formulario
    }

    function agregarFoto(file) {
        if (fotosCapturadas.length >= MAX_FOTOS) return;
        fotosCapturadas.push(file);
        actualizarPreview();
    }

    window.eliminarFoto = function (index) {
        fotosCapturadas.splice(index, 1);
        actualizarPreview();
    }

    btnAbrirCamara.addEventListener('click', async () => {
        if (fotosCapturadas.length >= MAX_FOTOS) {
            mostrarAlerta('Límite de fotos', 'Ya has agregado 3 fotos (máximo permitido)');
            return;
        }

        try {
            stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
            videoElement.srcObject = stream;
            modalCamara.classList.add('active');
        } catch (error) {
            mostrarAlerta('Error', 'Error al acceder a la cámara: ' + error.message);
        }
    });

    btnCerrarModal.addEventListener('click', () => {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            stream = null;
        }
        modalCamara.classList.remove('active');
    });

    btnCapturar.addEventListener('click', () => {
        if (fotosCapturadas.length >= MAX_FOTOS) {
            mostrarAlerta('Límite de fotos', 'Ya has agregado 3 fotos');
            return;
        }
        canvasElement.width = videoElement.videoWidth;
        canvasElement.height = videoElement.videoHeight;
        canvasElement.getContext('2d').drawImage(videoElement, 0, 0);
        canvasElement.toBlob(blob => {
            const file = new File([blob], `foto_${Date.now()}.jpg`, { type: 'image/jpeg' });
            agregarFoto(file);
        }, 'image/jpeg', 0.95);

        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            stream = null;
        }
        modalCamara.classList.remove('active');
    });

    inputArchivo.addEventListener('change', (e) => {
        const archivos = Array.from(e.target.files);
        archivos.forEach(file => agregarFoto(file));
        inputArchivo.value = '';
    });

    // ⭐⭐⭐ VERIFICAR ESTADO DEL FORMULARIO Y BLOQUEAR/DESBLOQUEAR BOTÓN ⭐⭐⭐
    function verificarFormulario() {
        const btnSubmit = document.querySelector('.btn-submit');
        if (!btnSubmit) return;

        const selectPedido = document.getElementById('selectPedido');
        const selectProducto = document.getElementById('selectProducto');
        const selectMotivo = document.getElementById('motivo');

        // Verificar que todos los campos estén completos
        const pedidoValido = selectPedido && selectPedido.value !== '';
        const productoValido = selectProducto && selectProducto.value !== '';
        const motivoValido = selectMotivo && selectMotivo.value !== '';
        const fotosValidas = fotosCapturadas.length > 0; // Al menos 1 foto

        // Habilitar o deshabilitar botón
        if (pedidoValido && productoValido && motivoValido && fotosValidas) {
            btnSubmit.disabled = false;
            btnSubmit.classList.remove('btn-disabled');
            btnSubmit.style.cursor = 'pointer';
        } else {
            btnSubmit.disabled = true;
            btnSubmit.classList.add('btn-disabled');
            btnSubmit.style.cursor = 'not-allowed';
        }
    }

    // ⭐ Escuchar cambios en el select de motivo
    const selectMotivo = document.getElementById('motivo');
    if (selectMotivo) {
        selectMotivo.addEventListener('change', verificarFormulario);
    }

    // ⭐ Verificar al cargar la página
    verificarFormulario();

    // ====== ENVÍO DEL FORMULARIO ======
    const formDevolucion = document.getElementById('formDevolucion');
    if (formDevolucion) {
        formDevolucion.addEventListener('submit', function (e) {
            e.preventDefault();

            // Verificar una última vez antes de enviar
            const selectPedido = document.getElementById('selectPedido');
            const selectProducto = document.getElementById('selectProducto');
            const selectMotivo = document.getElementById('motivo');

            if (!selectPedido.value || !selectProducto.value || !selectMotivo.value || fotosCapturadas.length === 0) {
                mostrarAlerta('Formulario incompleto', 'Por favor completa todos los campos obligatorios y agrega al menos 1 foto');
                return;
            }

            // 🔥 DESACTIVAR BOTÓN INMEDIATAMENTE
            const btn = document.querySelector('.btn-submit');
            if (btn) {
                btn.disabled = true;
                btn.classList.add('btn-disabled');
                btn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Enviando...';
            }

            // Añadir la unidad al FormData
            const selectedOption = selectProducto.options[selectProducto.selectedIndex];
            const unidad = selectedOption.getAttribute('data-unidad');

            const formData = new FormData(formDevolucion);
            formData.set('unidad', unidad);

            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

            fetch(formDevolucion.action, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': csrfToken
                },
                body: formData
            })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        mostrarAlerta('Éxito', data.mensaje);
                        
                        // Quitar producto devuelto del select
                        if (selectedOption) selectedOption.remove();

                        // Quitar pedido si no quedan productos
                        const pedidoId = data.pedido_id;
                        const restantes = Array.from(selectProducto.options).filter(o => o.value !== "");
                        if (restantes.length === 0) {
                            const optionPedido = Array.from(selectPedido.options).find(o => parseInt(o.value) === pedidoId);
                            if (optionPedido) optionPedido.remove();
                            document.getElementById('grupoProducto').style.display = 'none';
                            document.getElementById('grupoLote').style.display = 'none';
                        }

                        // Limpiar formulario
                        formDevolucion.reset();
                        fotosCapturadas = [];
                        actualizarPreview();
                        document.getElementById('grupoLote').style.display = 'none';

                        // 🔥 REACTIVAR BOTÓN DESPUÉS DE ÉXITO
                        if (btn) {
                            btn.disabled = false;
                            btn.classList.remove('btn-disabled');
                            btn.innerHTML = '<i class="fa fa-paper-plane"></i> Enviar Solicitud de Devolución';
                        }
                        
                        verificarFormulario(); // ⭐ Verificar de nuevo
                    } else {
                        mostrarAlerta('Error', data.mensaje);
                        
                        // 🔥 REACTIVAR BOTÓN EN CASO DE ERROR
                        if (btn) {
                            btn.disabled = false;
                            btn.classList.remove('btn-disabled');
                            btn.innerHTML = '<i class="fa fa-paper-plane"></i> Enviar Solicitud de Devolución';
                        }
                        
                        verificarFormulario(); // ⭐ Verificar de nuevo
                    }
                })
                .catch(err => {
                    console.error(err);
                    mostrarAlerta('Error', 'Ocurrió un error al enviar la devolución');
                    
                    // 🔥 REACTIVAR BOTÓN EN CASO DE ERROR DE RED
                    if (btn) {
                        btn.disabled = false;
                        btn.classList.remove('btn-disabled');
                        btn.innerHTML = '<i class="fa fa-paper-plane"></i> Enviar Solicitud de Devolución';
                    }
                    
                    verificarFormulario(); // ⭐ Verificar de nuevo
                });
        });
    }
});

function mostrarAlerta(titulo, mensaje) {
    const overlay = document.getElementById("custom-alert");
    const alertTitle = document.getElementById("alert-title");
    const alertMessage = document.getElementById("alert-message");

    alertTitle.textContent = titulo;
    alertMessage.textContent = mensaje;

    overlay.style.display = "flex";

    document.getElementById("btn-aceptar").onclick = function () {
        overlay.style.display = "none";
    };
}