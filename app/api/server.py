from __future__ import annotations

import io
from functools import wraps
from pathlib import Path

from flask import Flask, jsonify, make_response, request, send_file, send_from_directory

from app.api.service import (
    build_export_payload,
    delete_meter,
    delete_alert_rule,
    delete_report_schedule,
    discover_meters,
    ensure_schema,
    get_email_health,
    get_email_settings,
    get_dashboard_data,
    get_latest_readings,
    get_parameter_catalog,
    get_trend_series,
    list_active_alerts,
    list_alert_history,
    list_alert_rules,
    list_meters,
    list_report_schedules,
    save_email_settings,
    save_alert_rule,
    save_meter,
    save_report_schedule,
    send_report_email,
    send_test_email,
)
from config.settings import load_settings


SETTINGS = load_settings()
FRONTEND_DIST_DIR = Path(__file__).resolve().parents[2] / "frontend" / "dist"


def _json_error(message: str, status_code: int = 400):
    response = jsonify({"error": message})
    response.status_code = status_code
    return response


def _allowed_origin() -> str | None:
    origin = request.headers.get("Origin", "").strip()
    allowed_origins = SETTINGS.cors_allowed_origins

    if not origin:
        return allowed_origins[0] if allowed_origins else None
    if "*" in allowed_origins:
        return "*"
    if origin in allowed_origins:
        return origin
    return None


def _corsify(response):
    allowed_origin = _allowed_origin()
    if allowed_origin is not None:
        response.headers["Access-Control-Allow-Origin"] = allowed_origin
        if allowed_origin != "*":
            response.headers["Vary"] = "Origin"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Expose-Headers"] = "Content-Disposition, X-Row-Count, X-Filename, X-Generated-At, X-Meter-Name"
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


def _route_json(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            payload = fn(*args, **kwargs)
            response = jsonify(payload)
        except ValueError as exc:
            response = _json_error(str(exc), 400)
        except Exception as exc:  # pragma: no cover - defensive API boundary
            response = _json_error(str(exc), 500)
        return _corsify(response)

    return wrapper


def _route_no_content(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            fn(*args, **kwargs)
            response = make_response("", 204)
        except ValueError as exc:
            response = _json_error(str(exc), 400)
        except Exception as exc:  # pragma: no cover - defensive API boundary
            response = _json_error(str(exc), 500)
        return _corsify(response)

    return wrapper


def create_app() -> Flask:
    app = Flask(__name__)

    try:
        ensure_schema()
    except Exception:
        # Keep API startup predictable; endpoints will surface connection issues.
        pass

    @app.after_request
    def add_cors_headers(response):
        return _corsify(response)

    @app.route("/api/health", methods=["GET"])
    def health():
        return _corsify(jsonify({"status": "ok"}))

    @app.route("/api/parameters", methods=["GET"])
    @_route_json
    def parameters():
        return get_parameter_catalog()

    @app.route("/api/meters", methods=["GET"])
    @_route_json
    def meters():
        return list_meters()

    @app.route("/api/meters", methods=["POST"])
    @_route_json
    def create_meter():
        payload = request.get_json(force=True, silent=False) or {}
        return save_meter(payload)

    @app.route("/api/meters/discover", methods=["POST"])
    @_route_json
    def discover_meter_devices():
        payload = request.get_json(force=True, silent=False) or {}
        return discover_meters(payload)

    @app.route("/api/meters/discover/sync", methods=["POST"])
    @_route_json
    def sync_discovered_meter_devices():
        payload = request.get_json(force=True, silent=False) or {}
        from app.api.service import sync_discovered_meters

        return sync_discovered_meters(payload)

    @app.route("/api/meters/<meter_id>", methods=["PUT"])
    @_route_json
    def update_meter(meter_id: str):
        payload = request.get_json(force=True, silent=False) or {}
        payload["meter_id"] = meter_id
        return save_meter(payload)

    @app.route("/api/meters/<meter_id>", methods=["DELETE"])
    @_route_no_content
    def remove_meter(meter_id: str):
        delete_meter(meter_id)

    @app.route("/api/meters/<meter_id>/readings", methods=["GET"])
    @_route_json
    def meter_readings(meter_id: str):
        return get_latest_readings(meter_id)

    @app.route("/api/meters/<meter_id>/trend", methods=["GET"])
    @_route_json
    def meter_trend(meter_id: str):
        parameter_key = request.args.get("parameterKey", "active_power_total")
        limit = int(request.args.get("limit", "12"))
        return get_trend_series(meter_id, parameter_key, limit=limit)

    @app.route("/api/meters/<meter_id>/alert-rules", methods=["GET"])
    @_route_json
    def meter_alert_rules(meter_id: str):
        return list_alert_rules(meter_id)

    @app.route("/api/meters/<meter_id>/alert-rules", methods=["POST"])
    @_route_json
    def meter_alert_rules_save(meter_id: str):
        payload = request.get_json(force=True, silent=False) or {}
        payload["meter_id"] = meter_id
        return save_alert_rule(payload)

    @app.route("/api/alert-rules/<int:rule_id>", methods=["DELETE"])
    @_route_no_content
    def remove_alert_rule(rule_id: int):
        delete_alert_rule(rule_id)

    @app.route("/api/alerts/active", methods=["GET"])
    @_route_json
    def active_alerts():
        meter_id = request.args.get("meterId")
        return list_active_alerts(meter_id)

    @app.route("/api/alerts/history", methods=["GET"])
    @_route_json
    def alert_history():
        meter_id = request.args.get("meterId")
        limit = int(request.args.get("limit", "50"))
        return list_alert_history(meter_id, limit=limit)

    @app.route("/api/dashboard", methods=["GET"])
    @_route_json
    def dashboard():
        meter_id = request.args.get("meterId")
        trend_parameter_key = request.args.get("trendParameterKey", "active_power_total")
        if not meter_id:
            meters = list_meters()
            meter_id = meters[0]["meter_id"] if meters else ""
        return get_dashboard_data(meter_id, trend_parameter_key)

    @app.route("/api/reports/excel", methods=["POST"])
    def report_excel():
        try:
            payload = request.get_json(force=True, silent=False) or {}
            export = build_export_payload(payload, "xlsx")
            response = send_file(
                io.BytesIO(export["bytes"]),
                mimetype=export["mime_type"],
                as_attachment=True,
                download_name=export["filename"],
            )
            response.headers["X-Row-Count"] = str(export["rows"])
            response.headers["X-Filename"] = export["filename"]
            response.headers["X-Generated-At"] = export["generated_at"]
            response.headers["X-Meter-Name"] = export["meter_name"]
            return _corsify(response)
        except ValueError as exc:
            return _corsify(_json_error(str(exc), 400))
        except Exception as exc:  # pragma: no cover - defensive API boundary
            return _corsify(_json_error(str(exc), 500))

    @app.route("/api/reports/word", methods=["POST"])
    def report_word():
        try:
            payload = request.get_json(force=True, silent=False) or {}
            export = build_export_payload(payload, "docx")
            response = send_file(
                io.BytesIO(export["bytes"]),
                mimetype=export["mime_type"],
                as_attachment=True,
                download_name=export["filename"],
            )
            response.headers["X-Row-Count"] = str(export["rows"])
            response.headers["X-Filename"] = export["filename"]
            response.headers["X-Generated-At"] = export["generated_at"]
            response.headers["X-Meter-Name"] = export["meter_name"]
            return _corsify(response)
        except ValueError as exc:
            return _corsify(_json_error(str(exc), 400))
        except Exception as exc:  # pragma: no cover - defensive API boundary
            return _corsify(_json_error(str(exc), 500))

    @app.route("/api/report-schedules", methods=["GET"])
    @_route_json
    def report_schedules():
        return list_report_schedules()

    @app.route("/api/report-schedules", methods=["POST"])
    @_route_json
    def create_report_schedule():
        payload = request.get_json(force=True, silent=False) or {}
        return save_report_schedule(payload)

    @app.route("/api/report-schedules/<int:schedule_id>", methods=["PUT"])
    @_route_json
    def update_report_schedule(schedule_id: int):
        payload = request.get_json(force=True, silent=False) or {}
        payload["id"] = schedule_id
        return save_report_schedule(payload)

    @app.route("/api/report-schedules/<int:schedule_id>", methods=["DELETE"])
    @_route_no_content
    def remove_report_schedule(schedule_id: int):
        delete_report_schedule(schedule_id)

    @app.route("/api/email/settings", methods=["GET"])
    @_route_json
    def email_settings():
        return get_email_settings()

    @app.route("/api/email/settings", methods=["POST"])
    @_route_json
    def update_email_settings():
        payload = request.get_json(force=True, silent=False) or {}
        return save_email_settings(payload)

    @app.route("/api/email/health", methods=["GET"])
    @_route_json
    def email_health():
        return get_email_health()

    @app.route("/api/email/test", methods=["POST"])
    @_route_json
    def email_test():
        payload = request.get_json(force=True, silent=False) or {}
        return send_test_email(payload)

    @app.route("/api/reports/email", methods=["POST"])
    @_route_json
    def reports_email():
        payload = request.get_json(force=True, silent=False) or {}
        return send_report_email(payload)

    @app.route("/", methods=["GET"])
    def frontend_index():
        if not FRONTEND_DIST_DIR.exists():
            return _corsify(_json_error("Frontend build not found. Run the frontend build first.", 503))
        return _corsify(send_from_directory(FRONTEND_DIST_DIR, "index.html"))

    @app.route("/<path:asset_path>", methods=["GET"])
    def frontend_assets(asset_path: str):
        if asset_path.startswith("api/"):
            return _corsify(_json_error("Not Found", 404))
        if not FRONTEND_DIST_DIR.exists():
            return _corsify(_json_error("Frontend build not found. Run the frontend build first.", 503))

        requested_path = FRONTEND_DIST_DIR / asset_path
        if requested_path.is_file():
            return _corsify(send_from_directory(FRONTEND_DIST_DIR, asset_path))
        return _corsify(send_from_directory(FRONTEND_DIST_DIR, "index.html"))

    @app.route("/api/<path:unused>", methods=["OPTIONS"])
    def preflight(unused: str):
        return _corsify(make_response("", 204))

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host=SETTINGS.api_host, port=SETTINGS.api_port, debug=SETTINGS.api_debug)
