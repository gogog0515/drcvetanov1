from django.core.exceptions import ValidationError
from django.db import models


class Appointment(models.Model):
    PATIENT_GROUP_CHOICES = [
        ("Пациент на Д-р Георги Цветанов - осигурен", "Пациент на Д-р Георги Цветанов - осигурен"),
        ("Пациент на Д-р Георги Цветанов - неосигурен", "Пациент на Д-р Георги Цветанов - неосигурен"),
        ("Платен прием", "Платен прием"),
    ]
    SPECIALTY_CHOICES = [
        ("Обща медицина (Личен лекар)", "Обща медицина (Личен лекар)"),
        ("Ехографска диагностика", "Ехографска диагностика"),
    ]
    DOCTOR_CHOICES = [
        ("Д-р Георги Цветанов", "Д-р Георги Цветанов"),
    ]
    STATUS_CHOICES = [
        ("pending", "Чакаща"),
        ("confirmed", "Потвърдена"),
        ("cancelled", "Отказана"),
    ]
    VISIT_REASON_CHOICES = [
        ("Преглед", "Преглед"),
        ("Профилактичен преглед", "Профилактичен преглед"),
        ("Издаване на рецепти", "Издаване на рецепти"),
        (
            "Издаване на медицински удостоверения",
            "Издаване на медицински удостоверения",
        ),
        ("Ехография на коремни органи", "Ехография на коремни органи"),
    ]

    patient_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=32)
    email = models.EmailField(blank=True)
    patient_group = models.CharField(
        max_length=64,
        choices=PATIENT_GROUP_CHOICES,
        default="Пациент на Д-р Георги Цветанов - осигурен",
    )
    specialty = models.CharField(max_length=32, choices=SPECIALTY_CHOICES)
    doctor = models.CharField(max_length=64, choices=DOCTOR_CHOICES)
    date = models.DateField()
    time = models.TimeField()
    visit_reason = models.CharField(
        max_length=64,
        choices=VISIT_REASON_CHOICES,
        default="Преглед",
    )
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.patient_name} - {self.specialty} ({self.date} {self.time})"

    def clean(self) -> None:
        super().clean()
        conflicting_appointment = (
            Appointment.objects.exclude(pk=self.pk)
            .filter(
                doctor=self.doctor,
                date=self.date,
                time=self.time,
            )
            .exclude(status="cancelled")
            .exists()
        )

        if conflicting_appointment:
            raise ValidationError(
                {"time": "Този час вече е зает. Моля, избери друг свободен час."}
            )

# Create your models here.
