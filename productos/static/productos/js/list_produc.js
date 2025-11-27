// Búsqueda de productos
document.addEventListener('DOMContentLoaded', function () {
    const searchInput = document.getElementById('searchInput');
    const searchStats = document.getElementById('searchStats');
    const cards = document.querySelectorAll('.product-card[data-search-text]');
    const totalCards = cards.length;

    function actualizarEstadisticas() {
        const visibleCards = Array.from(cards).filter(card => card.style.display !== 'none').length;
        if (searchInput.value.trim() === '') {
            searchStats.textContent = `Mostrando ${totalCards} producto${totalCards !== 1 ? 's' : ''}`;
        } else {
            searchStats.textContent = `Encontrados ${visibleCards} de ${totalCards} producto${totalCards !== 1 ? 's' : ''}`;
        }
    }

    if (searchInput) {
        actualizarEstadisticas();
        searchInput.addEventListener('input', function () {
            const searchTerm = this.value.toLowerCase().trim();
            cards.forEach(card => {
                const searchText = card.dataset.searchText || '';
                card.style.display = (searchTerm === '' || searchText.includes(searchTerm)) ? '' : 'none';
            });
            actualizarEstadisticas();
        });
    }
});

function toggleCategorias() {
    const list = document.getElementById("categoryList");
    list.style.display = (list.style.display === "block") ? "none" : "block";
}

function abrirModal(id) {
    document.getElementById(id).style.display = "flex";

    if (id === 'modalAgregarProducto') {
        const form = document.getElementById('formProducto');
        if (form) {
            form.reset();
            const errorDivs = form.querySelectorAll('.form-errors, .errorlist');
            errorDivs.forEach(div => div.innerHTML = '');
        }
    }
}

function cerrarModal(id) {
    document.getElementById(id).style.display = "none";
}

function abrirEditar(element) {
    const modalEditar = document.getElementById("modalEditar");
    const inputNombre = document.getElementById("editNombre");
    const form = document.getElementById("editarForm");
    inputNombre.value = element.getAttribute("data-nombre");
    form.action = element.getAttribute("data-url");
    modalEditar.style.display = "flex";
}

function abrirModalLote(productoId) {
    document.getElementById("productoIdLote").value = productoId;
    document.getElementById("modalAgregarLote").style.display = "block";
}

function cerrarModal(id) {
    document.getElementById(id).style.display = "none";
}
