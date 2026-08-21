const form = document.querySelector('#nodoForm');
const statusEl = document.querySelector('#status');
const nameInput = document.querySelector('#name');
const emailInput = document.querySelector('#email');
const pref1Select = document.querySelector('#pref1');
const pref2Select = document.querySelector('#pref2');
const ideaInput = document.querySelector('#idea');
const submitBtn = document.querySelector('#submitBtn');

const modal = document.querySelector('#responseModal');
const modalTitle = document.querySelector('#modalTitle');
const modalBadge = document.querySelector('#modalBadge');
const modalDescription = document.querySelector('#modalDescription');
const modalSummary = document.querySelector('#modalSummary');
const modalCloseBtn = document.querySelector('#modalCloseBtn');
const btnEditResponse = document.querySelector('#btnEditResponse');
const btnDeleteResponse = document.querySelector('#btnDeleteResponse');

const nodeNames = Object.fromEntries((window.NODO_CATALOG?.nodes || []).map(n => [n.id, n.name]));

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

function showModal(mode, data) {
  if (mode === 'submitted') {
    modalBadge.textContent = 'CONFIRMACIÓN';
    modalTitle.textContent = '¡Disponibilidad enviada!';
    modalDescription.textContent = 'Tu disponibilidad ha sido registrada exitosamente en el sistema.';
  } else {
    modalBadge.textContent = 'REGISTRO PREVIO';
    modalTitle.textContent = 'Formulario ya enviado';
    modalDescription.textContent = 'Ya has respondido este formulario previamente desde este navegador.';
  }

  const p1Name = nodeNames[data.preference_1] || data.preference_1 || '—';
  const p2Name = nodeNames[data.preference_2] || data.preference_2 || '—';
  const busyCount = data.busy_slots ? data.busy_slots.length : 0;

  modalSummary.innerHTML = `
    <dl>
      <dt>Nombre:</dt><dd>${esc(data.name)}</dd>
      <dt>Correo:</dt><dd>${esc(data.email)}</dd>
      <dt>1ª Preferencia:</dt><dd>${esc(p1Name)}</dd>
      <dt>2ª Preferencia:</dt><dd>${esc(p2Name)}</dd>
      ${data.additional_idea ? `<dt>Temática/Idea:</dt><dd>${esc(data.additional_idea)}</dd>` : ''}
      <dt>Bloques ocupados:</dt><dd>${busyCount} bloque(s) marcados</dd>
    </dl>
  `;

  modal.style.display = 'flex';
  modal.setAttribute('aria-hidden', 'false');
}

function hideModal() {
  modal.style.display = 'none';
  modal.setAttribute('aria-hidden', 'true');
}

function populateForm(data) {
  if (!data) return;
  nameInput.value = data.name || '';
  emailInput.value = data.email || '';
  pref1Select.value = data.preference_1 || '';
  pref2Select.value = data.preference_2 || '';
  ideaInput.value = data.additional_idea || '';
  setBusySlots(data.busy_slots || []);
  submitBtn.textContent = 'Actualizar mi disponibilidad';
}

function clearForm() {
  nameInput.value = '';
  emailInput.value = '';
  pref1Select.value = '';
  pref2Select.value = '';
  ideaInput.value = '';
  setBusySlots([]);
  submitBtn.textContent = 'Enviar mi disponibilidad';
  [nameInput, emailInput].forEach(x => x.parentElement.parentElement.classList.remove('invalid'));
  pref1Select.closest('.pref-row').classList.remove('invalid');
}

modalCloseBtn.onclick = hideModal;
modal.onclick = event => {
  if (event.target === modal) hideModal();
};

btnEditResponse.onclick = () => {
  hideModal();
  statusEl.textContent = 'Puedes modificar tus datos o disponibilidad y presionar "Actualizar mi disponibilidad".';
  statusEl.className = 'status ok';
  nameInput.focus();
};

btnDeleteResponse.onclick = async () => {
  const saved = JSON.parse(localStorage.getItem('nodo_response_data') || '{}');
  const targetEmail = (saved.email || emailInput.value || '').trim();

  if (!confirm('¿Estás seguro de que deseas borrar tu respuesta? Esta acción eliminará tu registro del sistema.')) {
    return;
  }

  if (targetEmail) {
    try {
      const res = await fetch('/api/responses', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: targetEmail })
      });
      if (!res.ok && res.status !== 404) {
        alert('Hubo un problema al eliminar la respuesta del servidor. Se limpiarán los datos locales.');
      }
    } catch (err) {
      console.error('Error al eliminar en servidor:', err);
    }
  }

  localStorage.removeItem('nodo_response_data');
  localStorage.removeItem('nodo_response_submitted');
  clearForm();
  hideModal();
  statusEl.textContent = 'Tu respuesta ha sido eliminada con éxito.';
  statusEl.className = 'status ok';
};

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
      const res = await fetch('/api/responses', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...payload, replace_existing })
      });

      if (res.status === 409) {
        if (confirm('Ya existe una respuesta registrada con este correo. ¿Deseas reemplazarla?')) {
          return send(true);
        }
        statusEl.textContent = 'No se modificó tu respuesta anterior.';
        statusEl.className = 'status err';
        return;
      }

      if (!res.ok) {
        statusEl.textContent = 'No pudimos guardar tu respuesta. Intenta nuevamente.';
        statusEl.className = 'status err';
        return;
      }

      localStorage.setItem('nodo_response_data', JSON.stringify({ ...payload, submitted_at: new Date().toISOString() }));
      localStorage.setItem('nodo_response_submitted', '1');
      submitBtn.textContent = 'Actualizar mi disponibilidad';
      statusEl.textContent = 'Disponibilidad guardada ✓';
      statusEl.className = 'status ok';

      showModal('submitted', payload);
    } catch (err) {
      console.error(err);
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
      showModal('already_submitted', savedData);
      statusEl.textContent = 'Este navegador ya envió una respuesta; puedes actualizarla o borrarla.';
    } catch (err) {
      console.error('Error al cargar datos guardados:', err);
    }
  }
})();

