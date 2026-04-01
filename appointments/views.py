import json

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import EchoAppointmentForm, GeneralAppointmentForm
from .models import Appointment


def normalize_phone(value: str) -> str:
    return "".join(ch for ch in value if ch.isdigit())


def split_time_choices(time_choices):
    morning = []
    afternoon = []
    for value, label in time_choices:
        if value < "12:00":
            morning.append((value, label))
        else:
            afternoon.append((value, label))
    return {"morning": morning, "afternoon": afternoon}


def build_occupied_map(doctor: str) -> dict[str, list[str]]:
    occupied = {}
    appointments = (
        Appointment.objects.filter(doctor=doctor)
        .exclude(status="cancelled")
        .values_list("date", "time")
    )
    for appointment_date, appointment_time in appointments:
        occupied.setdefault(appointment_date.isoformat(), []).append(
            appointment_time.strftime("%H:%M")
        )
    return occupied


def home(request: HttpRequest) -> HttpResponse:
    submitted_form_type = request.GET.get("submitted", "")
    lookup_phone = (request.GET.get("lookup_phone") or "").strip()

    if request.method == "POST":
        form_type = request.POST.get("form_type", "general")
        form_class = EchoAppointmentForm if form_type == "echo" else GeneralAppointmentForm
        submitted_form = form_class(request.POST)
        if submitted_form.is_valid():
            appointment = submitted_form.save()
            messages.success(
                request,
                f"Часът за {appointment.patient_name} е записан успешно за {appointment.date:%d.%m.%Y} в {appointment.time:%H:%M}.",
            )
            return redirect(f"{reverse('home')}?submitted={form_type}")
        general_form = submitted_form if form_type == "general" else GeneralAppointmentForm()
        echo_form = submitted_form if form_type == "echo" else EchoAppointmentForm()
    else:
        general_form = GeneralAppointmentForm()
        echo_form = EchoAppointmentForm()

    appointments = Appointment.objects.all()
    normalized_lookup_phone = normalize_phone(lookup_phone)
    phone_lookup_results = []
    if normalized_lookup_phone:
        phone_lookup_results = [
            appointment
            for appointment in appointments
            if normalize_phone(appointment.phone) == normalized_lookup_phone
        ][:10]

    doctor_name = "Д-р Георги Цветанов"
    general_occupied_map = build_occupied_map(doctor_name)
    echo_occupied_map = build_occupied_map(doctor_name)
    general_initial_date = general_form.initial.get("date")
    echo_initial_date = echo_form.initial.get("date")
    context = {
        "general_form": general_form,
        "echo_form": echo_form,
        "general_time_groups": split_time_choices(general_form.fields["time"].choices),
        "echo_time_groups": split_time_choices(echo_form.fields["time"].choices),
        "general_occupied_json": json.dumps(general_occupied_map, ensure_ascii=False),
        "echo_occupied_json": json.dumps(echo_occupied_map, ensure_ascii=False),
        "general_initial_occupied_times": general_occupied_map.get(general_initial_date, []),
        "echo_initial_occupied_times": echo_occupied_map.get(echo_initial_date, []),
        "recent_appointments": appointments[:4],
        "stats": {
            "total": appointments.count(),
            "pending": appointments.filter(status="pending").count(),
            "confirmed": appointments.filter(status="confirmed").count(),
        },
        "lookup_phone": lookup_phone,
        "phone_lookup_results": phone_lookup_results,
        "submitted_form_type": submitted_form_type,
        "patient_groups": [choice[0] for choice in Appointment.PATIENT_GROUP_CHOICES],
    }
    return render(request, "appointments/home.html", context)


def dashboard(request: HttpRequest) -> HttpResponse:
    appointments = Appointment.objects.all()
    status = request.GET.get("status", "all")
    specialty = request.GET.get("specialty", "all")
    patient_group = request.GET.get("patient_group", "all")

    if status != "all":
        appointments = appointments.filter(status=status)
    if specialty != "all":
        appointments = appointments.filter(specialty=specialty)
    if patient_group != "all":
        appointments = appointments.filter(patient_group=patient_group)

    context = {
        "appointments": appointments,
        "status_filter": status,
        "specialty_filter": specialty,
        "patient_group_filter": patient_group,
        "stats": {
            "total": Appointment.objects.count(),
            "pending": Appointment.objects.filter(status="pending").count(),
            "confirmed": Appointment.objects.filter(status="confirmed").count(),
        },
        "specialties": [choice[0] for choice in Appointment.SPECIALTY_CHOICES],
        "patient_groups": [choice[0] for choice in Appointment.PATIENT_GROUP_CHOICES],
    }
    return render(request, "appointments/dashboard.html", context)


@require_POST
def update_status(request: HttpRequest, pk: int, status: str) -> HttpResponse:
    appointment = get_object_or_404(Appointment, pk=pk)
    allowed_statuses = {choice[0] for choice in Appointment.STATUS_CHOICES}
    if status in allowed_statuses:
        previous_status = appointment.status
        appointment.status = status
        try:
            appointment.full_clean()
            appointment.save(update_fields=["status"])
        except ValidationError as error:
            appointment.status = previous_status
            message = error.message_dict.get("time", error.messages)
            if isinstance(message, list):
                message = " ".join(message)
            messages.error(request, message)
        else:
            messages.success(request, f"Статусът на заявка #{appointment.pk} е обновен.")
    return redirect("dashboard")
