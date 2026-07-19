function getJsonData(elementId, defaultVal) {
  const el = document.getElementById(elementId);

  if (!el) {
    console.warn(`No existe <script id="${elementId}">`);
    return defaultVal;
  }

  const txt = (el.textContent || "").trim();
  if (!txt) {
    console.warn(`<script id="${elementId}"> está vacío`);
    return defaultVal;
  }

  try {
    return JSON.parse(txt);
  } catch (e) {
    console.error(`Error parseando ${elementId}:`, e);
    console.error("Contenido recibido (primeros 200 chars):", txt.slice(0, 200));
    return defaultVal;
  }
}

const datosPeso = getJsonData("datos_peso_json", []);
const datosUnidades = getJsonData("datos_unidades_json", {});
const datosLiquidos = getJsonData("datos_liquidos_json", {
  habilitado: false,
  total_litros: 0,
  capacidad: 200,
  porcentaje: 0,
  tipos: {},
});
let chartUnidades = null;

const categoriasBD = getJsonData("categorias_bd", []);
const tiposBD = getJsonData("tipos_bd", []);
const destinosBD = getJsonData("destinos_bd", []);

window.datosPeso = datosPeso;
window.datosUnidades = datosUnidades;
window.datosLiquidos = datosLiquidos;

function actualizarVisualUnidades(datos) {
  const total = Math.max(Number(datos?.total) || 0, 0);
  const limite = Math.max(Number(datos?.limite_total) || 1000, 1);
  const disponibles = Math.max(limite - total, 0);
  const porcentaje = Math.max(Number(datos?.porcentaje_global) || 0, 0);

  if (chartUnidades) {
    chartUnidades.data.datasets[0].data = [total, disponibles];
    chartUnidades.update('none');
  }

  const totalTexto = document.getElementById('totalUnidadesTexto');
  const porcentajeTexto = document.getElementById('porcentajeUnidadesTexto');
  const limiteTexto = document.getElementById('limiteUnidadesTexto');
  if (totalTexto) totalTexto.textContent = `${total} / ${limite}`;
  if (porcentajeTexto) porcentajeTexto.textContent = `${porcentaje.toFixed(1)}%`;
  if (limiteTexto) limiteTexto.textContent = `Límite: ${limite} unidades`;
}

async function refrescarUnidadesDashboard() {
  const url = window.AppUrls?.dashboardUnidades;
  if (!url || document.visibilityState === 'hidden') return;
  try {
    const response = await fetch(url, {
      credentials: 'same-origin',
      cache: 'no-store',
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
    });
    if (!response.ok) return;
    actualizarVisualUnidades(await response.json());
  } catch (error) {
    console.warn('No se pudo actualizar el gráfico de unidades.', error);
  }
}

window.categoriasBD = categoriasBD;
window.tiposBD = tiposBD;
window.destinosBD = destinosBD;

// ---------------------------------------------------------------------
// 2. HELPERS
// ---------------------------------------------------------------------
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

function showCustomAlert(message, type) {
  return window.AppPopup.alert(message, {
    type: type === "alert" ? "warning" : type,
    title: "Alerta operativa",
  });
}

// ---------------------------------------------------------------------
// 3. MODAL: SUBTIPOS Y DESTINOS
// ---------------------------------------------------------------------

// ---------------------------------------------------------------------
// 3. MODAL: SUBTIPOS Y DESTINOS (SIN API, usando destinosBD)
// ---------------------------------------------------------------------

// Guarda el tipo del retiro actual (orgánico o inorgánico).
window.__modalTipoRetiro = null;

function normalizeTipo(tipo) {
  const t = String(tipo || "").trim().toLowerCase();
  if (t.includes("inorg")) return "inorganico";
  return "organico";
}

function categoriaEs(cat, tipo) {
  const tipoOperacional = String(cat?.tipo_operacional || "").trim().toLowerCase();
  if (tipoOperacional) return tipoOperacional === tipo;

  const nombre = String(cat?.nombre || "").toLowerCase();
  if (tipo === "inorganico") return nombre.includes("inorg");
  return nombre.includes("org") || nombre.includes("compost");
}

// ✅ Cargar destinos por TIPO + categoría seleccionada (desde destinosBD)
window.actualizarDestinos = function () {
  const selectDestino = document.getElementById("modal-destino");
  if (!selectDestino) return;

  const catIdRaw = document.getElementById("modal-categoria")?.value || "";
  const catId = parseInt(catIdRaw, 10);

  selectDestino.innerHTML = '<option value="">-- Seleccione Destino --</option>';

  // Si no hay categoría, queda deshabilitado
  if (!catId) {
    selectDestino.disabled = true;
    return;
  }

  // Filtrar destinos por categoria_id (desde JSON inyectado)
  const filtrados = destinosBD.filter(d => parseInt(d.categoria_id, 10) === catId);

  filtrados.forEach(d => {
    const opt = document.createElement("option");
    opt.value = d.id;
    opt.textContent = d.nombre;
    selectDestino.appendChild(opt);
  });

  selectDestino.disabled = filtrados.length === 0;
};

window.actualizarSubtipos = function () {
  const selectSub = document.getElementById("modal-subtipo");
  if (!selectSub) return;

  const catIdRaw = document.getElementById("modal-categoria")?.value || "";
  const catId = parseInt(catIdRaw, 10);

  selectSub.innerHTML = '<option value="">-- Seleccione Subtipo --</option>';

  if (!catId) {
    selectSub.disabled = true;
    window.actualizarDestinos();
    return;
  }

  const filtrados = tiposBD.filter(t => parseInt(t.categoria_id, 10) === catId);

  filtrados.forEach(tipo => {
    const opt = document.createElement("option");
    opt.value = tipo.id_tipo;
    opt.textContent = tipo.nombre_residuo;
    selectSub.appendChild(opt);
  });

  selectSub.disabled = false;

  // ✅ destinos dependen de categoría seleccionada
  window.actualizarDestinos();

};

// ---------------------------------------------------------------------
// 4. MODAL: ABRIR / CERRAR / SUBMIT
// ---------------------------------------------------------------------
window.openVaciarModal = function (origen, tipo) {
  window.__modalTipoRetiro = normalizeTipo(tipo);

  const modal = document.getElementById("vaciar-modal");
  const inputDisplay = document.getElementById("modal-origen-display");
  const inputValue = document.getElementById("modal-origen-value");
  const selectCat = document.getElementById("modal-categoria");
  const selectSub = document.getElementById("modal-subtipo");
  const selectDestino = document.getElementById("modal-destino");
  const form = document.getElementById("form-vaciar");

  if (!modal || !inputDisplay || !inputValue || !selectCat || !selectSub || !form) return;

  inputDisplay.value = origen;
  inputValue.value = origen;

  // Reset combos
  selectCat.innerHTML = '<option value="">-- Seleccione Categoría --</option>';
  selectSub.innerHTML = '<option value="">-- Seleccione primero Categoría --</option>';
  selectSub.disabled = true;

  if (selectDestino) {
    selectDestino.innerHTML = '<option value="">-- Seleccione una categoria --</option>';
    selectDestino.disabled = true;
  }

  // Llenar categorías (todas)
  categoriasBD.forEach(cat => {
    const opt = document.createElement("option");
    opt.value = cat.id_categoria;
    opt.textContent = cat.nombre;
    selectCat.appendChild(opt);
  });

  // Campo cantidad parcial (si no existe)
  let cantidadDiv = document.getElementById("modal-cantidad-div");
  if (!cantidadDiv) {
    cantidadDiv = document.createElement("div");
    cantidadDiv.id = "modal-cantidad-div";
    cantidadDiv.classList.add("mb-4");
    cantidadDiv.innerHTML = `
      <label class="block text-sm font-medium text-gray-700">Cantidad a Vaciar (deje en 0 para total)</label>
      <input type="number" id="modal-cantidad" name="cantidad" min="0" step="0.001" value="0"
             class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-cyan-500 focus:ring-cyan-500 sm:text-sm px-3 py-2">
      <p class="mt-1 text-xs text-gray-500">Unidades para inorgánico y kg para orgánico. 0 = vaciar todo.</p>
    `;
    const beforeNode = form.querySelector(".mb-6");
    if (beforeNode) form.insertBefore(cantidadDiv, beforeNode);
    else form.appendChild(cantidadDiv);
  }

  // ✅ Preselección según tipo (para ayudar)
  if (window.__modalTipoRetiro === "inorganico") {
    const catInorganico = categoriasBD.find(c => categoriaEs(c, "inorganico"));
    if (catInorganico) {
      selectCat.value = catInorganico.id_categoria;
      window.actualizarSubtipos(); // esto llama actualizarDestinos()
    }
  } else if (window.__modalTipoRetiro === "organico") {
    const catOrganico = categoriasBD.find(c => categoriaEs(c, "organico"));
    if (catOrganico) {
      selectCat.value = catOrganico.id_categoria;
      window.actualizarSubtipos();
    }
  }

  modal.classList.remove("hidden");
};

window.closeVaciarModal = function () {
  document.getElementById("vaciar-modal")?.classList.add("hidden");
  document.getElementById("modal-status-msg")?.classList.add("hidden");
};

window.submitVaciado = function () {
  const form = document.getElementById("form-vaciar");
  if (!form) return;

  const formData = new FormData(form);

  if (!formData.get("categoria") || !formData.get("subtipo") || !formData.get("destino")) {
    alert("Por favor seleccione Categoría, Subtipo y Destino");
    return;
  }

  const csrftoken = getCookie("csrftoken");

  fetch(window.AppUrls?.registrarRetiro || "/registrar_retiro/", {
    method: "POST",
    headers: { "X-CSRFToken": csrftoken },
    body: formData
  })
    .then(r => r.json())
    .then(async data => {
      if (data.success) {
        await window.AppPopup.alert(data.msg, {
          type: "success",
          title: "Retiro registrado",
        });
        location.reload();
      } else {
        await window.AppPopup.alert(
          data.error || data.msg || "Ocurrió un error",
          { type: "error" }
        );
      }
    })
    .catch(err => window.AppPopup.alert(
      "Error de conexión: " + err,
      { type: "error" }
    ));
};

window.confirmarRetiro = async function (origen, tipo) {
  const confirmado = await window.AppPopup.confirm(
    `¿Confirma vaciar ${origen}? Esto registrará el retiro y actualizará los gráficos.`,
    {
      title: "Confirmar retiro",
      acceptText: "Continuar",
    }
  );
  if (confirmado) {
    window.openVaciarModal(origen, tipo);
  }
};


// ---------------------------------------------------------------------
// 5. GRÁFICOS (Chart.js)
// ---------------------------------------------------------------------
Chart.defaults.font.family = "'Inter', sans-serif";
Chart.defaults.color = '#64748b';

document.addEventListener('DOMContentLoaded', () => {

  // 1. SÓLIDOS (Barras)
  const ctxPeso = document.getElementById('chartPeso');
  if (ctxPeso && Array.isArray(datosPeso) && datosPeso.length > 0) {
    new Chart(ctxPeso, {
      type: 'bar',
      data: {
        labels: datosPeso.map(d => String(d.device_name || '').replace('Compostera ', 'C')),
        datasets: [{
          label: 'Llenado %',
          data: datosPeso.map(d => d.porcentaje),
          backgroundColor: datosPeso.map(d => !d.habilitado ? '#94a3b8' : (d.porcentaje > 85 ? '#ef4444' : '#10b981')),
          borderRadius: 4
        }]
      },
      options: {
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true, max: 100 } }
      }
    });
  }

  // 2. LÍQUIDOS (lógica completa conservada, operación deshabilitada)
  const ctxLiq = document.getElementById('chartLiquidos');
  if (ctxLiq) {
    const liquidosHabilitados = datosLiquidos?.habilitado === true;
    const porcentajeLiquidos = Math.min(
      Math.max(Number(datosLiquidos?.porcentaje) || 0, 0),
      100
    );
    new Chart(ctxLiq, {
      type: 'doughnut',
      data: {
        labels: ['Ocupado', 'Disponible'],
        datasets: [{
          data: [porcentajeLiquidos, Math.max(100 - porcentajeLiquidos, 0)],
          backgroundColor: liquidosHabilitados
            ? ['#5f6368', '#e2e8f0']
            : ['#9ca3af', '#e5e7eb'],
          borderWidth: 0,
          circumference: 180,
          rotation: 270,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        events: liquidosHabilitados
          ? ['mousemove', 'mouseout', 'click', 'touchstart', 'touchmove']
          : [],
        plugins: {
          legend: { display: false },
          tooltip: {
            enabled: liquidosHabilitados,
            callbacks: {
              label: function (context) {
                return `${context.label}: ${context.raw}%`;
              }
            }
          }
        }
      }
    });
  }

  // 3. UNIDADES (capacidad utilizada frente a capacidad disponible)
  const ctxUni = document.getElementById('chartUnidades');
  if (ctxUni) {
    const totalUnidades = Math.max(Number(datosUnidades?.total) || 0, 0);
    const limiteUnidades = Math.max(Number(datosUnidades?.limite_total) || 1000, 1);
    const unidadesDisponibles = Math.max(limiteUnidades - totalUnidades, 0);
    chartUnidades = new Chart(ctxUni, {
      type: 'doughnut',
      data: {
        labels: ['Registradas', 'Disponibles'],
        datasets: [{
          data: [totalUnidades, unidadesDisponibles],
          backgroundColor: ['#5f6368', '#e2e8f0'],
          borderWidth: 0,
          hoverOffset: 4,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '62%',
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: function (context) {
                return `${context.label}: ${context.raw} unidades`;
              }
            }
          }
        }
      }
    });
    actualizarVisualUnidades(datosUnidades);
    window.setInterval(refrescarUnidadesDashboard, 5000);
    document.addEventListener('visibilitychange', function () {
      if (document.visibilityState === 'visible') refrescarUnidadesDashboard();
    });
  }

  // Alertas
  function mostrarAlertas() {
    const compostera1 = datosPeso.find(d => d.device_name === 'Compostera 1');
    if (compostera1 && compostera1.porcentaje >= 90) {
      showCustomAlert(`Compostera 1 está al ${compostera1.porcentaje}% de capacidad. Recomendamos vaciar pronto.`, 'alert');
    }
    const compostera2 = datosPeso.find(d => d.device_name === 'Compostera 2');
    if (compostera2 && compostera2.porcentaje >= 90) {
      showCustomAlert(`Compostera 2 está al ${compostera2.porcentaje}% de capacidad. Recomendamos vaciar pronto.`, 'alert');
    }
    if (datosUnidades.porcentaje_global >= 80) {
      showCustomAlert(`Almacén de Unidades está al ${datosUnidades.porcentaje_global}% de capacidad. Recomendamos reciclar/vaciar.`, 'alert');
    }
    if (datosLiquidos.habilitado && datosLiquidos.porcentaje >= 80) {
      showCustomAlert(`Tanque de líquidos está al ${datosLiquidos.porcentaje}% de capacidad. Recomendamos vaciar pronto.`, 'alert');
    }
  }

  mostrarAlertas();
});
