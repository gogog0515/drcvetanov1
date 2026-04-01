from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.utils.html import format_html

from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "patient_name",
        "phone",
        "appointment_summary",
        "notes_preview",
        "status",
        "quick_actions",
        "created_at",
    )
    list_filter = ("status", "patient_group", "specialty", "doctor", "date", "visit_reason")
    search_fields = ("patient_name", "phone", "email", "notes")
    readonly_fields = ("created_at",)
    fieldsets = (
        (
            "Пациент",
            {
                "fields": ("patient_name", "phone", "email"),
            },
        ),
        (
            "Записване",
            {
                "fields": ("patient_group", "specialty", "doctor", "visit_reason", "date", "time", "status"),
            },
        ),
        (
            "Допълнително",
            {
                "fields": ("notes", "created_at"),
            },
        ),
    )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:appointment_id>/confirm/",
                self.admin_site.admin_view(self.confirm_appointment),
                name="appointments_appointment_confirm",
            ),
            path(
                "<int:appointment_id>/cancel/",
                self.admin_site.admin_view(self.cancel_appointment),
                name="appointments_appointment_cancel",
            ),
        ]
        return custom_urls + urls

    @admin.display(description="Информация за заявката")
    def appointment_summary(self, obj):
        return f"{obj.patient_group} | {obj.specialty} | {obj.doctor} | {obj.date:%d.%m.%Y} {obj.time:%H:%M} | {obj.visit_reason}"

    @admin.display(description="Бележка")
    def notes_preview(self, obj):
        if not obj.notes:
            return "-"
        return obj.notes if len(obj.notes) <= 60 else f"{obj.notes[:57]}..."

    @admin.display(description="Действия")
    def quick_actions(self, obj):
        if obj.status == "confirmed":
            cancel_url = reverse("admin:appointments_appointment_cancel", args=[obj.pk])
            return format_html('<a class="button" href="{}">Откажи</a>', cancel_url)
        if obj.status == "cancelled":
            confirm_url = reverse("admin:appointments_appointment_confirm", args=[obj.pk])
            return format_html('<a class="button" href="{}">Потвърди</a>', confirm_url)

        confirm_url = reverse("admin:appointments_appointment_confirm", args=[obj.pk])
        cancel_url = reverse("admin:appointments_appointment_cancel", args=[obj.pk])
        return format_html(
            '<a class="button" href="{}">Потвърди</a>&nbsp;<a class="button" href="{}">Откажи</a>',
            confirm_url,
            cancel_url,
        )

    def confirm_appointment(self, request, appointment_id):
        appointment = self.get_object(request, appointment_id)
        if appointment:
            previous_status = appointment.status
            appointment.status = "confirmed"
            try:
                appointment.full_clean()
                appointment.save(update_fields=["status"])
            except ValidationError as error:
                appointment.status = previous_status
                message = error.message_dict.get("time", error.messages)
                if isinstance(message, list):
                    message = " ".join(message)
                self.message_user(request, message, level=messages.ERROR)
            else:
                self.message_user(request, "Заявката е потвърдена.", level=messages.SUCCESS)
        return HttpResponseRedirect(reverse("admin:appointments_appointment_changelist"))

    def cancel_appointment(self, request, appointment_id):
        appointment = self.get_object(request, appointment_id)
        if appointment:
            appointment.status = "cancelled"
            appointment.save(update_fields=["status"])
            self.message_user(request, "Заявката е отказана.", level=messages.WARNING)
        return HttpResponseRedirect(reverse("admin:appointments_appointment_changelist"))
