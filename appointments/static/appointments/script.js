function formatBulgarianDate(isoDate) {
  if (!isoDate) {
    return "";
  }

  const [year, month, day] = isoDate.split("-").map(Number);
  const date = new Date(year, month - 1, day);

  return new Intl.DateTimeFormat("bg-BG", {
    weekday: "long",
    day: "2-digit",
    month: "2-digit",
  }).format(date);
}

function updateScheduleForm(form) {
  const occupiedMap = JSON.parse(form.dataset.occupied || "{}");
  const dateInputs = Array.from(form.querySelectorAll("input[data-date-value]"));
  const timeInputs = Array.from(form.querySelectorAll("input[data-time-value]"));
  const pickedDate = form.querySelector(".schedule-picked-date");
  const pickedTime = form.querySelector(".schedule-picked-time");
  const earliestSlot = form.querySelector(".schedule-earliest");

  if (!dateInputs.length || !timeInputs.length) {
    return;
  }

  const selectedDateInput = dateInputs.find((input) => input.checked) || dateInputs[0];
  if (!selectedDateInput.checked) {
    selectedDateInput.checked = true;
  }

  const selectedDate = selectedDateInput.value;
  const occupiedTimes = new Set(occupiedMap[selectedDate] || []);
  let firstFreeInput = null;

  if (pickedDate) {
    pickedDate.textContent = formatBulgarianDate(selectedDate);
  }

  timeInputs.forEach((input) => {
    const card = input.closest(".schedule-choice-card");
    const isOccupied = occupiedTimes.has(input.value);

    input.disabled = isOccupied;

    if (card) {
      card.classList.toggle("is-disabled", isOccupied);
      card.classList.remove("is-first-free");
    }

    if (isOccupied && input.checked) {
      input.checked = false;
    }

    if (!isOccupied && !firstFreeInput) {
      firstFreeInput = input;
    }
  });

  const selectedTimeInput = timeInputs.find((input) => input.checked && !input.disabled);
  const activeTimeInput = selectedTimeInput || firstFreeInput;

  if (!selectedTimeInput && firstFreeInput) {
    firstFreeInput.checked = true;
  }

  if (activeTimeInput) {
    const firstFreeCard = firstFreeInput?.closest(".schedule-choice-card");
    if (firstFreeCard) {
      firstFreeCard.classList.add("is-first-free");
    }

    if (pickedTime) {
      pickedTime.textContent = activeTimeInput.value;
    }

    if (earliestSlot) {
      const prefix = firstFreeInput && activeTimeInput.value === firstFreeInput.value
        ? "Най-ранен свободен час"
        : "Избран час";
      earliestSlot.textContent = `${prefix}: ${formatBulgarianDate(selectedDate)} - ${activeTimeInput.value}`;
    }
  } else {
    if (pickedTime) {
      pickedTime.textContent = "Няма свободен час";
    }

    if (earliestSlot) {
      earliestSlot.textContent = `Няма свободни часове за ${formatBulgarianDate(selectedDate)}`;
    }
  }
}

function initScheduleForm(form) {
  const dateInputs = Array.from(form.querySelectorAll("input[data-date-value]"));
  const timeInputs = Array.from(form.querySelectorAll("input[data-time-value]"));

  dateInputs.forEach((input) => {
    input.addEventListener("change", () => updateScheduleForm(form));
  });

  timeInputs.forEach((input) => {
    input.addEventListener("change", () => updateScheduleForm(form));
  });

  updateScheduleForm(form);
}

function initSubmitButton(form) {
  const submitButton = form.querySelector("[data-submit-button]");
  if (!submitButton) {
    return;
  }

  form.addEventListener("submit", () => {
    submitButton.disabled = true;
    submitButton.classList.add("is-submitting");
    submitButton.textContent = submitButton.dataset.loadingText || "Изпращане...";
  });
}

function openModalById(id) {
  const modal = document.getElementById(id);
  if (modal) {
    modal.classList.add("is-open");
  }
}

function closeModalById(id) {
  const modal = document.getElementById(id);
  if (modal) {
    modal.classList.remove("is-open");
  }
}

function initModals() {
  document.addEventListener("click", (event) => {
    const target = event.target;
    if (!(target instanceof Element)) {
      return;
    }

    const openTrigger = target.closest("[data-open-modal]");
    if (openTrigger instanceof HTMLElement) {
      openModalById(openTrigger.dataset.openModal);
      return;
    }

    const closeTrigger = target.closest("[data-close-modal]");
    if (closeTrigger instanceof HTMLElement) {
      closeModalById(closeTrigger.dataset.closeModal);
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") {
      return;
    }
    document.querySelectorAll(".app-modal-shell.is-open").forEach((modal) => {
      modal.classList.remove("is-open");
    });
  });
}

document.querySelectorAll("[data-schedule-form]").forEach((form) => {
  initScheduleForm(form);
  initSubmitButton(form);
});

initModals();
