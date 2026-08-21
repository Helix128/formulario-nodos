const formView = document.querySelector('#formView');
const submittedView = document.querySelector('#submittedView');
const submittedSummary = document.querySelector('#submittedSummary');
const editBanner = document.querySelector('#editBanner');
const btnCancelEdit = document.querySelector('#btnCancelEdit');

const form = document.querySelector('#nodoForm');
const statusEl = document.querySelector('#status');
const nameInput = document.querySelector('#name');
const emailInput = document.querySelector('#email');
const pref1Select = document.querySelector('#pref1');
const pref2Select = document.querySelector('#pref2');
const ideaInput = document.querySelector('#idea');
const submitBtn = document.querySelector('#submitBtn');

const btnEditResponse = document.querySelector('#btnEditResponse');
const btnDeleteResponse = document.querySelector('#btnDeleteResponse');

const deleteConfirmModal = document.querySelector('#deleteConfirmModal');
const btnCancelDelete = document.querySelector('#btnCancelDelete');
const btnCancelDeleteClose = document.querySelector('#btnCancelDeleteClose');
const btnConfirmDelete = document.querySelector('#btnConfirmDelete');

const nodeNames = Object.fromEntries((window.NODO_CATALOG?.nodes || []).map(n => [n.id, n.name]));
const dayMap = Object.fromEntries((window.NODO_CATALOG?.days || []).map(d => [d.id, d.short || d.name]));
const slotMap = Object.fromEntries((window.NODO_CATALOG?.slots || []).map(s => [s.id, s.id.toUpperCase()]));

const esc = x => String(x || '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

// Matrix cell selection
document.querySelectorAll('.cell').forEach(cell => {
  cell.onclick = () => {
    cell.classList.toggle('busy');
    cell.setAttribute('aria-pressed', cell.classList.contains('busy'));
  };
});

function getBusySlots() {
  return [...document.querySelectorAll('.cell.busy')].map(x => ({
    day_id: x.dataset.day,
    slot_id: x.dataset.slot
  }));
}

function setBusySlots(slots) {
  const busySet = new Set((slots || []).map(s => `${s.day_id}:${s.slot_id}`));
  document.querySelectorAll('.cell').forEach(cell => {
    const isBusy = busySet.has(`${cell.dataset.day}:${cell.dataset.slot}`);
    cell.classList.toggle('busy', isBusy);
    cell.setAttribute('aria-pressed', isBusy ? 'true' : 'false');
  });
}

function formatSubmittedDate(isoString) {
  try {
    const d = isoString ? new Date(isoString) : new Date();
    return d.toLocaleString('es-CL', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch {
    return 'Hoy';
  }
}

function showSubmittedView(data) {
  if (!data) return;

  const p1Name = nodeNames[data.preference_1] || data.preference_1 || '—';
  const p2Name = nodeNames[data.preference_2] || data.preference_2 || '—';
  const busySlots = data.busy_slots || [];
  const busyCount = busySlots.length;

  let slotsHtml = '';
  if (busyCount > 0) {
    const pills = busySlots
      .map(s => `<span class="slot-pill">${esc(dayMap[s.day_id] || s.day_id)} ${esc(slotMap[s.slot_id] || s.slot_id)}</span>`)
      .join(' ');
    slotsHtml = `
      <dt>Horarios ocupados:</dt>
      <dd>
        <strong>${busyCount} bloque(s) con clases</strong>
        <div class="summary-slots-list">${pills}</div>
      </dd>
    `;
  } else {
    slotsHtml = `
      <dt>Horarios ocupados:</dt>
      <dd><em>Ninguno marcado (disponibilidad completa)</em></dd>
    `;
  }

  const dateFormatted = formatSubmittedDate(data.submitted_at);

  submittedSummary.innerHTML = `
    <dl>
      <dt>Nombre:</dt><dd>${esc(data.name)}</dd>
      <dt>Correo UDD:</dt><dd>${esc(data.email)}</dd>
      <dt>1ª Preferencia:</dt><dd><strong>${esc(p1Name)}</strong></dd>
      <dt>2ª Preferencia:</dt><dd><strong>${esc(p2Name)}</strong></dd>
      ${data.additional_idea ? `<dt>Temática/Idea:</dt><dd>${esc(data.additional_idea)}</dd>` : ''}
      ${slotsHtml}
      <dt>Fecha de registro:</dt><dd>${esc(dateFormatted)}</dd>
    </dl>
  `;

  formView.style.display = 'none';
  submittedView.style.display = 'block';
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function showFormView(isEditing = false) {
  submittedView.style.display = 'none';
  formView.style.display = 'block';

  if (isEditing) {
    editBanner.style.display = 'flex';
    submitBtn.textContent = 'Guardar cambios';
    statusEl.textContent = 'Modo de edición activo. Haz tus cambios y guarda cuando estés listo.';
    statusEl.className = 'status ok';
  } else {
    editBanner.style.display = 'none';
    submitBtn.textContent = 'Enviar mi disponibilidad';
    statusEl.textContent = '';
    statusEl.className = 'status';
  }

  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function populateForm(data) {
  if (!data) return;
  nameInput.value = data.name || '';
  emailInput.value = data.email || '';
  pref1Select.value = data.preference_1 || '';
  pref2Select.value = data.preference_2 || '';
  ideaInput.value = data.additional_idea || '';
  setBusySlots(data.busy_slots || []);
}

function clearForm() {
  nameInput.value = '';
  emailInput.value = '';
  pref1Select.value = '';
  pref2Select.value = '';
  ideaInput.value = '';
  setBusySlots([]);
  [nameInput, emailInput].forEach(x => x.parentElement.parentElement.classList.remove('invalid'));
  pref1Select.closest('.pref-row').classList.remove('invalid');
}

function openDeleteModal() {
  deleteConfirmModal.style.display = 'flex';
  deleteConfirmModal.setAttribute('aria-hidden', 'false');
}

function closeDeleteModal() {
  deleteConfirmModal.style.display = 'none';
  deleteConfirmModal.setAttribute('aria-hidden', 'true');
}

// Botón Editar respuesta
btnEditResponse.onclick = () => {
  const savedJson = localStorage.getItem('nodo_response_data');
  if (savedJson) {
    try {
      populateForm(JSON.parse(savedJson));
    } catch (e) {
      console.error(e);
    }
  }
  showFormView(true);
  nameInput.focus();
};

// Botón Cancelar edición y volver al comprobante
btnCancelEdit.onclick = () => {
  const savedJson = localStorage.getItem('nodo_response_data');
  if (savedJson) {
    try {
      showSubmittedView(JSON.parse(savedJson));
    } catch (e) {
      showFormView(false);
    }
  } else {
    showFormView(false);
  }
};

// Modal de confirmación para Borrar
btnDeleteResponse.onclick = () => {
  openDeleteModal();
};

btnCancelDelete.onclick = closeDeleteModal;
btnCancelDeleteClose.onclick = closeDeleteModal;
deleteConfirmModal.onclick = event => {
  if (event.target === deleteConfirmModal) closeDeleteModal();
};

// Confirmación de borrado
btnConfirmDelete.onclick = async () => {
  const saved = JSON.parse(localStorage.getItem('nodo_response_data') || '{}');
  const targetEmail = (saved.email || emailInput.value || '').trim();

  closeDeleteModal();

  if (targetEmail) {
    try {
      const res = await fetch('/api/responses', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: targetEmail })
      });
      if (!res.ok && res.status !== 404) {
        console.warn('Error al eliminar en servidor');
      }
    } catch (err) {
      console.error('Error al eliminar en servidor:', err);
    }
  }

  localStorage.removeItem('nodo_response_data');
  localStorage.removeItem('nodo_response_submitted');
  clearForm();
  showFormView(false);
  statusEl.textContent = 'Tu respuesta ha sido eliminada con éxito del sistema.';
  statusEl.className = 'status ok';
};

// Enviar formulario
form.onsubmit = async event => {
  event.preventDefault();
  const name = nameInput.value.trim();
  const email = emailInput.value.trim();
  const p1 = pref1Select.value;
  const p2 = pref2Select.value;

  const validName = name.length >= 3;
  const validEmail = /^[^\s@]+@udd\.cl$/i.test(email);
  const validPrefs = p1 && p2 && p1 !== p2;
  const valid = validName && validEmail && validPrefs;

  [nameInput, emailInput].forEach(x => x.parentElement.parentElement.classList.remove('invalid'));
  pref1Select.closest('.pref-row').classList.remove('invalid');

  if (!validName) nameInput.parentElement.parentElement.classList.add('invalid');
  if (!validEmail) emailInput.parentElement.parentElement.classList.add('invalid');
  if (!validPrefs) pref1Select.closest('.pref-row').classList.add('invalid');

  if (!valid) {
    statusEl.textContent = 'Revisa los campos marcados en rojo.';
    statusEl.className = 'status err';
    return;
  }

  const payload = {
    name,
    email,
    preference_1: p1,
    preference_2: p2,
    additional_idea: ideaInput.value.trim(),
    busy_slots: getBusySlots()
  };

  async function send(replace_existing = false) {
    try {
      submitBtn.disabled = true;
      submitBtn.textContent = 'Guardando...';

      const res = await fetch('/api/responses', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...payload, replace_existing })
      });

      submitBtn.disabled = false;

      if (res.status === 409) {
        if (confirm('Ya existe una respuesta registrada con este correo. ¿Deseas reemplazarla?')) {
          return send(true);
        }
        submitBtn.textContent = editBanner.style.display === 'flex' ? 'Guardar cambios' : 'Enviar mi disponibilidad';
        statusEl.textContent = 'No se modificó tu respuesta anterior.';
        statusEl.className = 'status err';
        return;
      }

      if (!res.ok) {
        submitBtn.textContent = editBanner.style.display === 'flex' ? 'Guardar cambios' : 'Enviar mi disponibilidad';
        statusEl.textContent = 'No pudimos guardar tu respuesta. Intenta nuevamente.';
        statusEl.className = 'status err';
        return;
      }

      const fullData = { ...payload, submitted_at: new Date().toISOString() };
      localStorage.setItem('nodo_response_data', JSON.stringify(fullData));
      localStorage.setItem('nodo_response_submitted', '1');

      showSubmittedView(fullData);
    } catch (err) {
      console.error(err);
      submitBtn.disabled = false;
      submitBtn.textContent = editBanner.style.display === 'flex' ? 'Guardar cambios' : 'Enviar mi disponibilidad';
      statusEl.textContent = 'Error de conexión. Intenta nuevamente.';
      statusEl.className = 'status err';
    }
  }

  const isEditing = Boolean(localStorage.getItem('nodo_response_data'));
  send(isEditing);
};

// Check on page load if response already exists
(() => {
  const savedJson = localStorage.getItem('nodo_response_data');
  if (savedJson) {
    try {
      const savedData = JSON.parse(savedJson);
      populateForm(savedData);
      showSubmittedView(savedData);
    } catch (err) {
      console.error('Error al cargar datos guardados:', err);
      showFormView(false);
    }
  } else {
    showFormView(false);
  }
})();


