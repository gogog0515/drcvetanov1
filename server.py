from __future__ import annotations

import json
import sys
from datetime import datetime
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_FILE = DATA_DIR / "appointments.json"


def ensure_data_file() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    if not DATA_FILE.exists():
        DATA_FILE.write_text("[]", encoding="utf-8")


def read_appointments() -> list[dict]:
    ensure_data_file()
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def write_appointments(appointments: list[dict]) -> None:
    ensure_data_file()
    DATA_FILE.write_text(
        json.dumps(appointments, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


class MediSlotHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    def _read_json_body(self) -> dict:
        content_length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(content_length) if content_length else b"{}"
        return json.loads(raw.decode("utf-8"))

    def _send_json(self, payload: object, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_error_json(self, message: str, status: HTTPStatus) -> None:
        self._send_json({"error": message}, status=status)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/appointments":
            self._send_json(read_appointments())
            return
        if parsed.path == "/":
            self.path = "/index.html"
        super().do_GET()

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/appointments":
            self._send_error_json("Маршрутът не съществува.", HTTPStatus.NOT_FOUND)
            return

        try:
            payload = self._read_json_body()
        except json.JSONDecodeError:
            self._send_error_json("Невалиден JSON.", HTTPStatus.BAD_REQUEST)
            return

        required_fields = ["patientName", "phone", "email", "specialty", "doctor", "date", "time"]
        missing = [field for field in required_fields if not str(payload.get(field, "")).strip()]
        if missing:
            self._send_error_json("Липсват задължителни полета.", HTTPStatus.BAD_REQUEST)
            return

        appointments = read_appointments()
        next_id = max((item["id"] for item in appointments), default=0) + 1
        appointment = {
            "id": next_id,
            "patientName": payload["patientName"].strip(),
            "phone": payload["phone"].strip(),
            "email": payload["email"].strip(),
            "specialty": payload["specialty"].strip(),
            "doctor": payload["doctor"].strip(),
            "date": payload["date"].strip(),
            "time": payload["time"].strip(),
            "notes": str(payload.get("notes", "")).strip(),
            "status": "pending",
            "createdAt": datetime.now().strftime("%d.%m.%Y %H:%M"),
        }
        appointments.append(appointment)
        write_appointments(appointments)
        self._send_json(appointment, status=HTTPStatus.CREATED)

    def do_PATCH(self) -> None:
        parts = urlparse(self.path).path.strip("/").split("/")
        if len(parts) != 3 or parts[:2] != ["api", "appointments"]:
            self._send_error_json("Маршрутът не съществува.", HTTPStatus.NOT_FOUND)
            return

        try:
            appointment_id = int(parts[2])
            payload = self._read_json_body()
        except ValueError:
            self._send_error_json("Невалиден идентификатор.", HTTPStatus.BAD_REQUEST)
            return
        except json.JSONDecodeError:
            self._send_error_json("Невалиден JSON.", HTTPStatus.BAD_REQUEST)
            return

        status = payload.get("status")
        if status not in {"pending", "confirmed", "cancelled"}:
            self._send_error_json("Невалиден статус.", HTTPStatus.BAD_REQUEST)
            return

        appointments = read_appointments()
        for item in appointments:
            if item["id"] == appointment_id:
                item["status"] = status
                write_appointments(appointments)
                self._send_json(item)
                return

        self._send_error_json("Заявката не е намерена.", HTTPStatus.NOT_FOUND)


def main() -> None:
    ensure_data_file()
    preferred_port = 8000
    if len(sys.argv) > 1:
        preferred_port = int(sys.argv[1])

    port = preferred_port
    while True:
        try:
            server = ThreadingHTTPServer(("127.0.0.1", port), MediSlotHandler)
            break
        except OSError as error:
            if error.errno != 10048:
                raise
            port += 1

    print(f"MediSlot server started at http://127.0.0.1:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
