const page = document.body.dataset.page;
const apiBase = "/api/appointments";

function formatStatus(status) {
  if (status === "confirmed") return "Потвърдена";
  if (status === "cancelled") return "Отказана";
  return "Чакаща";
}

function formatDate(isoDate) {
  if (!isoDate) return "-";
  const date = new Date(`${isoDate}T00:00:00`);
  return new Intl.DateTimeFormat("bg-BG", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  }).format(date);
}

function statusBadge(status) {
  return `<span class="badge ${status}">${formatStatus(status)}</span>`;
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || "Request failed.");
  }

  return response.json();
}

async function loadAppointments() {
  return requestJson(apiBase);
}

function updateMetrics(appointments) {
  const total = appointments.length;
  const pending = appointments.filter((item) => item.status === "pending").length;
  const confirmed = appointments.filter((item) => item.status === "confirmed").length;

  const totalEl = document.querySelector("#metric-total");
  const pendingEl = document.querySelector("#metric-pending");
  const confirmedEl = document.querySelector("#metric-confirmed");

  if (totalEl) totalEl.textContent = String(total);
  if (pendingEl) pendingEl.textContent = String(pending);
  if (confirmedEl) confirmedEl.textContent = String(confirmed);
}

function renderTrackingList(container, appointments, emptyMessage, mode) {
  if (!container) return;

  if (!appointments.length) {
    container.innerHTML = `<div class="empty-state">${emptyMessage}</div>`;
    return;
  }

  container.innerHTML = appointments
    .sort((a, b) => b.id - a.id)
    .map((item) => {
      const description =
        mode === "pending"
          ? "Заявката е подадена и очаква потвърждение."
          : "Часът е потвърден. Явете се 10 минути по-рано.";

      const meta = mode === "pending"
        ? `Предложен час: ${formatDate(item.date)} в ${item.time}`
        : `Потвърден час: ${formatDate(item.date)} в ${item.time}`;

      return `
        <article class="appointment-item tracked-item">
          <div class="appointment-meta">
            <strong>${item.specialty}</strong>
            <span>${item.doctor}</span>
            <span>${meta}</span>
            <span>${description}</span>
          </div>
          <div class="appointment-side">
            ${statusBadge(item.status)}
            <span class="appointment-id">Заявка №${item.id}</span>
          </div>
        </article>
      `;
    })
    .join("");
}

function renderPatientTracking(appointments) {
  const pendingContainer = document.querySelector("#pending-appointments");
  const confirmedContainer = document.querySelector("#confirmed-appointments");

  const pendingAppointments = appointments.filter((item) => item.status === "pending");
  const confirmedAppointments = appointments.filter((item) => item.status === "confirmed");

  renderTrackingList(
    pendingContainer,
    pendingAppointments,
    "Все още няма подадени заявки, които да чакат потвърждение.",
    "pending",
  );
  renderTrackingList(
    confirmedContainer,
    confirmedAppointments,
    "Все още няма потвърдени часове.",
    "confirmed",
  );
}

async function initPatientPage() {
  const form = document.querySelector("#appointment-form");
  const modal = document.querySelector("#success-modal");
  const closeModalButton = document.querySelector("#close-modal");
  const confirmationDetails = document.querySelector("#confirmation-details");
  const dateInput = document.querySelector('input[name="date"]');
  const feedback = document.querySelector("#form-feedback");
  const submitButton = document.querySelector("#submit-button");

  if (dateInput) {
    dateInput.min = new Date().toISOString().split("T")[0];
  }

  const refresh = async () => {
    const appointments = await loadAppointments();
    updateMetrics(appointments);
    renderPatientTracking(appointments);
  };

  try {
    await refresh();
  } catch (error) {
    if (feedback) {
      feedback.textContent = "Сървърът не отговаря. Стартирай приложението през Python сървъра.";
    }
  }

  form?.addEventListener("submit", async (event) => {
    event.preventDefault();

    const formData = new FormData(form);
    const payload = {
      patientName: String(formData.get("patientName") || "").trim(),
      phone: String(formData.get("phone") || "").trim(),
      email: String(formData.get("email") || "").trim(),
      specialty: String(formData.get("specialty") || "").trim(),
      doctor: String(formData.get("doctor") || "").trim(),
      date: String(formData.get("date") || "").trim(),
      time: String(formData.get("time") || "").trim(),
      notes: String(formData.get("notes") || "").trim(),
    };

    if (feedback) feedback.textContent = "";
    submitButton.disabled = true;
    submitButton.textContent = "Изпращане...";

    try {
      const created = await requestJson(apiBase, {
        method: "POST",
        body: JSON.stringify(payload),
      });

      if (confirmationDetails) {
        confirmationDetails.textContent =
          `${created.patientName}, заявка №${created.id} за ${created.specialty.toLowerCase()} при ${created.doctor} ` +
          `на ${formatDate(created.date)} в ${created.time} е подадена успешно. ` +
          "Провери секцията „Моите заявки“, докато чакаш потвърждение.";
      }

      if (typeof modal?.showModal === "function") modal.showModal();
      form.reset();
      if (dateInput) dateInput.min = new Date().toISOString().split("T")[0];
      await refresh();
    } catch (error) {
      if (feedback) {
        feedback.textContent = "Не успяхме да запазим заявката. Провери дали сървърът е стартиран.";
      }
    } finally {
      submitButton.disabled = false;
      submitButton.textContent = "Изпрати заявката";
    }
  });

  closeModalButton?.addEventListener("click", () => modal?.close());
  modal?.addEventListener("click", (event) => {
    const dialogDimensions = modal.getBoundingClientRect();
    const clickedInsideDialog =
      event.clientX >= dialogDimensions.left &&
      event.clientX <= dialogDimensions.right &&
      event.clientY >= dialogDimensions.top &&
      event.clientY <= dialogDimensions.bottom;
    if (!clickedInsideDialog) modal.close();
  });
}

function renderAdminTable(appointments) {
  const tableBody = document.querySelector("#admin-table-body");
  if (!tableBody) return;

  if (!appointments.length) {
    tableBody.innerHTML = '<tr><td colspan="8" class="empty-state">Няма заявки по текущите филтри.</td></tr>';
    return;
  }

  tableBody.innerHTML = appointments
    .sort((a, b) => b.id - a.id)
    .map((item) => `
      <tr>
        <td>#${item.id}</td>
        <td><strong>${item.patientName}</strong><br><span class="table-muted">${item.phone}<br>${item.email}</span></td>
        <td>${item.specialty}<br><span class="table-muted">${item.doctor}</span></td>
        <td>${formatDate(item.date)}<br><span class="table-muted">${item.time}</span></td>
        <td>${item.notes || '<span class="table-muted">Няма бележка</span>'}</td>
        <td>${statusBadge(item.status)}</td>
        <td class="table-muted">${item.createdAt}</td>
        <td>
          <div class="row-actions">
            <button class="inline-button confirm" data-action="confirmed" data-id="${item.id}">Потвърди</button>
            <button class="inline-button cancel" data-action="cancelled" data-id="${item.id}">Откажи</button>
          </div>
        </td>
      </tr>
    `)
    .join("");
}

async function initAdminPage() {
  const statusFilter = document.querySelector("#status-filter");
  const specialtyFilter = document.querySelector("#specialty-filter");
  const reloadButton = document.querySelector("#reload-button");
  const tableBody = document.querySelector("#admin-table-body");
  const adminFeedback = document.querySelector("#admin-feedback");

  let allAppointments = [];

  const applyFilters = () => {
    const status = statusFilter?.value || "all";
    const specialty = specialtyFilter?.value || "all";
    const filtered = allAppointments.filter((item) => {
      const statusMatches = status === "all" || item.status === status;
      const specialtyMatches = specialty === "all" || item.specialty === specialty;
      return statusMatches && specialtyMatches;
    });
    renderAdminTable(filtered);
    updateMetrics(allAppointments);
  };

  const refresh = async () => {
    allAppointments = await loadAppointments();
    applyFilters();
    if (adminFeedback) adminFeedback.textContent = `Заредени са ${allAppointments.length} заявки.`;
  };

  try {
    await refresh();
  } catch (error) {
    if (adminFeedback) adminFeedback.textContent = "Неуспешна връзка със сървъра. Стартирай server.py.";
  }

  statusFilter?.addEventListener("change", applyFilters);
  specialtyFilter?.addEventListener("change", applyFilters);
  reloadButton?.addEventListener("click", refresh);

  tableBody?.addEventListener("click", async (event) => {
    const target = event.target;
    if (!(target instanceof HTMLButtonElement)) return;

    const { id, action } = target.dataset;
    if (!id || !action) return;

    target.disabled = true;
    try {
      await requestJson(`${apiBase}/${id}`, {
        method: "PATCH",
        body: JSON.stringify({ status: action }),
      });
      await refresh();
    } catch (error) {
      if (adminFeedback) adminFeedback.textContent = "Промяната не беше запазена.";
    } finally {
      target.disabled = false;
    }
  });
}

if (page === "patient") initPatientPage();
if (page === "admin") initAdminPage();
