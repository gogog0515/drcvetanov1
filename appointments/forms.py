from datetime import date, datetime, timedelta

from django import forms

from .models import Appointment


class BaseAppointmentForm(forms.ModelForm):
    WEEKDAY_LABELS = {
        0: "Понеделник",
        1: "Вторник",
        2: "Сряда",
        3: "Четвъртък",
        4: "Петък",
        5: "Събота",
        6: "Неделя",
    }

    doctor = forms.ChoiceField(
        label="Лекар",
        choices=Appointment.DOCTOR_CHOICES,
        initial="Д-р Георги Цветанов",
    )
    date = forms.ChoiceField(label="Дата")
    time = forms.ChoiceField(label="Час")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        date_choices = self._build_date_choices()
        time_choices = self._build_time_choices()
        self.fields["email"].required = False
        self.fields["date"].choices = date_choices
        self.fields["time"].choices = time_choices
        if not self.is_bound:
            first_free_date, first_free_time = self._find_first_available_slot(
                date_choices,
                time_choices,
            )
            self.initial["date"] = first_free_date
            self.initial["time"] = first_free_time

    class Meta:
        model = Appointment
        fields = [
            "patient_name",
            "phone",
            "email",
            "patient_group",
            "specialty",
            "doctor",
            "date",
            "time",
            "visit_reason",
            "notes",
        ]
        labels = {
            "patient_name": "Име и фамилия",
            "phone": "Телефон",
            "email": "Имейл",
            "patient_group": "Вид прием",
            "specialty": "Специалност",
            "doctor": "Лекар",
            "date": "Дата",
            "time": "Час",
            "visit_reason": "Причина за посещението",
            "notes": "Допълнителна информация",
        }
        widgets = {
            "patient_name": forms.TextInput(attrs={"placeholder": "Например Мария Иванова"}),
            "phone": forms.TextInput(attrs={"placeholder": "+359 88 123 4567"}),
            "email": forms.EmailInput(attrs={"placeholder": "name@example.com"}),
            "notes": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Допълнителни симптоми, уточнения или вид удостоверение",
                }
            ),
        }

    @staticmethod
    def _build_date_choices():
        choices = []
        current = date.today()
        while len(choices) < 5:
            current += timedelta(days=1)
            if current.weekday() < 5:
                choices.append(
                    (
                        current.isoformat(),
                        f"{BaseAppointmentForm.WEEKDAY_LABELS[current.weekday()]}|{current.strftime('%d.%m.%Y')}",
                    )
                )
        return choices

    def _build_time_choices(self):
        return []

    @staticmethod
    def _time_range(start_time: str, end_time: str, step_minutes: int = 10):
        current = datetime.strptime(start_time, "%H:%M")
        end = datetime.strptime(end_time, "%H:%M")
        choices = []
        while current <= end:
            value = current.strftime("%H:%M")
            choices.append((value, value))
            current += timedelta(minutes=step_minutes)
        return choices

    def clean_date(self):
        value = self.cleaned_data["date"]
        return datetime.strptime(value, "%Y-%m-%d").date()

    def clean_time(self):
        value = self.cleaned_data["time"]
        return datetime.strptime(value, "%H:%M").time()

    def _get_doctor_value(self):
        return "Д-р Георги Цветанов"

    def _find_first_available_slot(self, date_choices, time_choices):
        doctor = self._get_doctor_value()
        if not doctor:
            return date_choices[0][0], time_choices[0][0]

        for date_value, _ in date_choices:
            occupied_times = set(
                Appointment.objects.filter(
                    doctor=doctor,
                    date=date_value,
                )
                .exclude(status="cancelled")
                .values_list("time", flat=True)
            )

            for time_value, _ in time_choices:
                parsed_time = datetime.strptime(time_value, "%H:%M").time()
                if parsed_time not in occupied_times:
                    return date_value, time_value

        return date_choices[0][0], time_choices[0][0]


class GeneralAppointmentForm(BaseAppointmentForm):
    EXCLUDED_REASON = "Ехография на коремни органи"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["visit_reason"].choices = [
            choice
            for choice in Appointment.VISIT_REASON_CHOICES
            if choice[0] != self.EXCLUDED_REASON
        ]

    def _build_time_choices(self):
        return self._time_range("08:30", "09:40") + self._time_range("13:30", "15:40")

    class Meta(BaseAppointmentForm.Meta):
        fields = [
            "patient_name",
            "phone",
            "email",
            "patient_group",
            "doctor",
            "date",
            "time",
            "visit_reason",
            "notes",
        ]

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.specialty = "Обща медицина (Личен лекар)"
        if commit:
            instance.save()
        return instance


class EchoAppointmentForm(BaseAppointmentForm):
    ECHO_REASON = "Ехография на коремни органи"
    ECHO_SPECIALTY = "Ехографска диагностика"
    ECHO_PATIENT_GROUP = "Платен прием"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["patient_group"].choices = [
            (self.ECHO_PATIENT_GROUP, self.ECHO_PATIENT_GROUP),
        ]
        self.fields["visit_reason"].choices = [
            (self.ECHO_REASON, self.ECHO_REASON),
        ]
        if not self.is_bound:
            self.initial["patient_group"] = self.ECHO_PATIENT_GROUP
            self.initial["visit_reason"] = self.ECHO_REASON

    def _build_time_choices(self):
        return self._time_range("14:00", "16:40")

    def clean_patient_group(self):
        return self.ECHO_PATIENT_GROUP

    def clean_visit_reason(self):
        return self.ECHO_REASON

    class Meta(BaseAppointmentForm.Meta):
        fields = [
            "patient_name",
            "phone",
            "email",
            "patient_group",
            "doctor",
            "date",
            "time",
            "visit_reason",
            "notes",
        ]

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.patient_group = self.ECHO_PATIENT_GROUP
        instance.specialty = self.ECHO_SPECIALTY
        instance.visit_reason = self.ECHO_REASON
        if commit:
            instance.save()
        return instance
