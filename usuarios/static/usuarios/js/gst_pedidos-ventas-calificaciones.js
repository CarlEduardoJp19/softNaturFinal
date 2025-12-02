const page = document.querySelector("[data-page='gst-pedidos']");

if (page) {
  console.log("JS cargado para gestión de pedidos");
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

  const csrftoken = getCookie('csrftoken');

  function mostrarAlerta(mensaje, tipo) {
    const alertaDiv = document.createElement('div');
    alertaDiv.className = `alerta ${tipo}`;
    alertaDiv.textContent = mensaje;
    document.getElementById('alertas').appendChild(alertaDiv);

    setTimeout(() => {
      alertaDiv.style.animation = 'slideIn 0.3s ease reverse';
      setTimeout(() => alertaDiv.remove(), 300);
    }, 3000);
  }

  function verDetalle(id) {
    const modal = document.getElementById('detalleModal');
    const modalBody = document.getElementById('detalleModalBody');

    modal.style.display = 'block';
    modalBody.innerHTML = `
    <div style="text-align: center; padding: 40px;">
      <div style="border: 4px solid rgba(0, 94, 39, 0.1); border-top: 4px solid #005E27; border-radius: 50%; width: 50px; height: 50px; animation: spin 1s linear infinite; margin: 0 auto 20px;"></div>
      <p style="color: #6c757d;">Cargando detalles...</p>
    </div>
  `;

    fetch(`/usuarios/detalle_pedido/${id}/`, {
      method: 'GET',
      headers: {
        'X-Requested-With': 'XMLHttpRequest',
      }
    })
      .then(response => response.json())
      .then(data => {
        if (!data.success) {
          modalBody.innerHTML = '<p style="text-align: center; color: #dc3545; padding: 40px;">No se pudieron cargar los detalles.</p>';
          return;
        }

        const p = data.pedido;

        let html = `
  <div class="pedido-info">
    <div class="info-item">
      <span class="info-label">Usuario</span>
      <span class="info-value">${p.usuario}</span>
    </div>
    <div class="info-item">
      <span class="info-label">Email</span>
      <span class="info-value">${p.email}</span>
    </div>
    <div class="info-item">
      <span class="info-label">Teléfono</span>
      <span class="info-value">${p.telefono}</span>
    </div>
    <div class="info-item">
      <span class="info-label">Dirección</span>
      <span class="info-value">${p.direccion}</span>
    </div>
    <div class="info-item">
      <span class="info-label">Estado</span>
      <span class="info-value"><span class="estado-actual ${p.estado.toLowerCase()}">${p.estado}</span></span>
    </div>
    <div class="info-item">
  <span class="info-label">Estado de Pago</span>
  <span class="info-value">${p.pago ? '<span style="color: green; font-weight: bold;"> Pagado</span>' : '<span style="color: red; font-weight: bold;">No pagado</span>'}</span>
</div>
    <div class="info-item">
      <span class="info-label">Fecha</span>
      <span class="info-value">${p.fecha}</span>
    </div>
  </div>
      <div class="productos-section">
        <h3 class="section-title">Productos del Pedido</h3>
        <table class="productos-table">
          <thead>
            <tr>
              <th>Producto</th>
              <th style="text-align: center;">Cantidad</th>
              <th style="text-align: right;">Precio</th>
              <th style="text-align: right;">Subtotal</th>
            </tr>
          </thead>
          <tbody>
    `;

        if (p.productos && p.productos.length > 0) {
          p.productos.forEach(prod => {
            html += `
          <tr>
            <td>${prod.nombre}</td>
            <td style="text-align: center;"><span class="cantidad-badge">${prod.cantidad}</span></td>
            <td style="text-align: right;" class="precio-cell">$${parseFloat(prod.precio).toFixed(2)}</td>
            <td style="text-align: right;" class="precio-cell">$${parseFloat(prod.subtotal).toFixed(2)}</td>
          </tr>
        `;
          });
        } else {
          html += '<tr><td colspan="4" style="text-align: center; color: #6c757d; font-style: italic; padding: 30px;">Sin productos</td></tr>';
        }

        html += `
          </tbody>
        </table>
      </div>

      <div class="total-pedido">
        <div class="total-label">Total del Pedido</div>
        <div class="total-amount">$${parseFloat(p.total).toFixed(2)}</div>
      </div>
    `;

        modalBody.innerHTML = html;
      })
      .catch(error => {
        console.error('Error:', error);
        modalBody.innerHTML = '<p style="text-align: center; color: #dc3545; padding: 40px;">Ocurrió un error al cargar los detalles.</p>';
      });
  }

  function cerrarModal() {
    document.getElementById('detalleModal').style.display = 'none';
  }

  window.onclick = function (event) {
    const modal = document.getElementById('detalleModal');
    if (event.target === modal) {
      cerrarModal();
    }
  }

  function cambiarEstado(id, nuevoEstado) {
    const confirmDiv = document.getElementById('confirmacion');

    const estadosNombres = {
      'pendiente': 'Pendiente',
      'enviado': 'Enviado',
      'entregado': 'Entregado'
    };

    confirmDiv.innerHTML = `
    <div class="confirmar">
      <div class="confirmar-box">
        <h3>¿Confirmar cambio de estado?</h3>
        <p>¿Desea cambiar el estado del pedido #${id} a <strong>${estadosNombres[nuevoEstado]}</strong>?</p>
        <button class="btn-si" onclick="confirmarCambioEstado('${id}', '${nuevoEstado}')">Sí, cambiar</button>
        <button class="btn-no" onclick="cancelarCambioEstado()">Cancelar</button>
      </div>
    </div>
  `;
    confirmDiv.style.display = 'block';
  }

  function confirmarCambioEstado(id, nuevoEstado) {
    document.getElementById('confirmacion').style.display = 'none';

    fetch(`/usuarios/cambiar_estado_pedido/${id}/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrftoken,
        'X-Requested-With': 'XMLHttpRequest',
      },
      body: JSON.stringify({ estado: nuevoEstado })
    })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          mostrarAlerta('Estado actualizado correctamente', 'success');

          const row = document.querySelector(`tr[data-id="${id}"]`);
          if (row) {
            const estadoCell = row.querySelector('.estado-actual');
            estadoCell.className = `estado-actual ${nuevoEstado}`;
            estadoCell.textContent = nuevoEstado.charAt(0).toUpperCase() + nuevoEstado.slice(1);
            row.setAttribute('data-estado', nuevoEstado);
          }

          setTimeout(() => location.reload(), 1000);
        } else {
          mostrarAlerta('Error al cambiar el estado: ' + (data.message || 'Error desconocido'), 'error');
        }
      })
      .catch(error => {
        console.error('Error:', error);
        mostrarAlerta('Error al cambiar el estado', 'error');
      });
  }

  function cancelarCambioEstado() {
    document.getElementById('confirmacion').style.display = 'none';
  }

  function filtrar(estado) {
    const rows = document.querySelectorAll('#pedidosTable tr[data-estado]');
    const buttons = document.querySelectorAll('.filtro-btn');

    buttons.forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');

    rows.forEach(row => {
      if (estado === 'todos') {
        row.style.display = '';
      } else {
        row.style.display = row.getAttribute('data-estado') === estado ? '' : 'none';
      }
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    const searchInput = document.getElementById('searchInput');

    if (searchInput) {
      searchInput.addEventListener('input', function () {
        const searchTerm = this.value.toLowerCase();
        const rows = document.querySelectorAll('#pedidosTable tr[data-search]');

        rows.forEach(row => {
          const searchText = row.getAttribute('data-search');
          row.style.display = searchText.includes(searchTerm) ? '' : 'none';
        });
      });
    }
  });
  function exportarPedidosExcel() {
    const estado = document.getElementById('estadoFilter')?.value || '';
    const mes = document.getElementById('mesFilter')?.value || '';
    const anio = document.getElementById('anioFilter')?.value || '';
    window.location.href = `{% url 'usuarios:exportar_pedidos_excel' %}?estado=${estado}&mes=${mes}&anio=${anio}`;
  }

}

// VENTAS
const page2 = document.querySelector("[data-page='ventas']");

if (page2) {
  console.log("JS cargado para gestión de ventas");
  document.addEventListener('DOMContentLoaded', function () {
    const searchInput = document.getElementById('searchInput');
    const mesFilter = document.getElementById('mesFilter');
    const anioFilter = document.getElementById('anioFilter');
    const ventasTable = document.getElementById('ventasTable');
    const totalVentasElement = document.getElementById('totalVentas');
    const btnExportar = document.getElementById('btnExportar');

    // Llenar el selector de años dinámicamente
    function populateYears() {
      const rows = ventasTable.querySelectorAll('tr[data-fecha]');
      const years = new Set();

      rows.forEach(row => {
        const fecha = row.getAttribute('data-fecha');
        if (fecha) {
          const year = fecha.split('-')[0];
          years.add(year);
        }
      });

      const sortedYears = Array.from(years).sort((a, b) => b - a);
      sortedYears.forEach(year => {
        const option = document.createElement('option');
        option.value = year;
        option.textContent = year;
        anioFilter.appendChild(option);
      });
    }

    populateYears();

    // Función para actualizar el total de ventas
    function updateTotalVentas() {
      const visibleRows = ventasTable.querySelectorAll('tr[data-monto]:not([style*="display: none"])');
      let total = 0;

      visibleRows.forEach(row => {
        const monto = parseFloat(row.getAttribute('data-monto')) || 0;
        total += monto;
      });

      // Formatear el total con separadores de miles
      totalVentasElement.textContent = '$' + total.toLocaleString('es-CO');
    }

    // Función para aplicar todos los filtros
    function applyFilters() {
      const searchTerm = searchInput.value.toLowerCase().trim();
      const selectedMes = mesFilter.value;
      const selectedAnio = anioFilter.value;
      const rows = ventasTable.querySelectorAll('tr[data-search]');

      rows.forEach(row => {
        const searchText = row.getAttribute('data-search') || '';
        const fecha = row.getAttribute('data-fecha') || '';

        let showRow = true;

        // Filtro de búsqueda
        if (searchTerm !== '' && !searchText.includes(searchTerm)) {
          showRow = false;
        }

        // Filtro de mes
        if (selectedMes !== '' && fecha) {
          const mesRow = fecha.split('-')[1];
          if (mesRow !== selectedMes) {
            showRow = false;
          }
        }

        // Filtro de año
        if (selectedAnio !== '' && fecha) {
          const anioRow = fecha.split('-')[0];
          if (anioRow !== selectedAnio) {
            showRow = false;
          }
        }

        row.style.display = showRow ? '' : 'none';
      });

      updateTotalVentas();
    }

    // Función para exportar a Excel
    function exportarExcel() {
      const mes = document.getElementById('mesFilter')?.value || '';
      const anio = document.getElementById('anioFilter')?.value || '';
      window.location.href = `{% url 'usuarios:exportar_ventas_excel' %}?mes=${mes}&anio=${anio}`;
    }

    // Event listeners
    if (searchInput) {
      searchInput.addEventListener('input', applyFilters);
    }

    if (mesFilter) {
      mesFilter.addEventListener('change', applyFilters);
    }

    if (anioFilter) {
      anioFilter.addEventListener('change', applyFilters);
    }

    if (btnExportar) {
      btnExportar.addEventListener('click', exportarExcel);
    }

    // Calcular el total inicial
    updateTotalVentas();
  });
}



// CALIFICACIONES

const page3 = document.querySelector("[data-page='calificaciones']");

if (page3) {
  console.log("JS cargado para gestión de calificaciones");
  document.addEventListener('DOMContentLoaded', function () {
    const searchInput = document.getElementById('searchInput');
    const searchStats = document.getElementById('searchStats');
    const tbody = document.querySelector('#calificacionesTable tbody');
    const rows = tbody.querySelectorAll('tr[data-search-text]');
    const totalRows = rows.length;

    function actualizarEstadisticas() {
      const visibleRows = Array.from(rows).filter(row => row.style.display !== 'none').length;

      if (searchInput.value.trim() === '') {
        searchStats.textContent = `Mostrando ${totalRows} calificación${totalRows !== 1 ? 'es' : ''}`;
      } else {
        searchStats.textContent = `Encontradas ${visibleRows} de ${totalRows} calificación${totalRows !== 1 ? 'es' : ''}`;
      }
    }

    if (searchInput) {
      // Mostrar estadísticas iniciales
      actualizarEstadisticas();

      searchInput.addEventListener('input', function () {
        const searchTerm = this.value.toLowerCase().trim();

        rows.forEach(row => {
          const searchText = row.dataset.searchText || '';

          if (searchTerm === '' || searchText.includes(searchTerm)) {
            row.style.display = '';
          } else {
            row.style.display = 'none';
          }
        });

        actualizarEstadisticas();
      });
    }
  });
  document.getElementById("btnExportar").addEventListener("click", function () {
    window.location.href = window.location.pathname + "?exportar=excel";
  });
}