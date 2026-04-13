import json
import logging
import os
import re
import time
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qsl

import requests


def env(name: str, default: Optional[str] = None) -> str:
    value = os.getenv(name, default)
    if value is None:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def to_bool(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def to_slug(name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", name.strip().lower()).strip("_")
    return slug or "unknown"


def normalize_auth(token: str) -> str:
    if token.lower().startswith("bearer "):
        return token
    return f"Bearer {token}"


class NayaxBridge:
    def __init__(self) -> None:
        self.nayax_base_url = env("NAYAX_BASE_URL", "https://lynx.nayax.com").rstrip("/")
        self.nayax_token = env("NAYAX_TOKEN")
        self.poll_interval = int(env("POLL_INTERVAL", "300"))
        self.screen_type_id = int(env("SCREEN_TYPE_ID", "1"))
        self.entity_id = int(env("ENTITY_ID", "0"))
        self.widget_ids = [
            int(x)
            for x in env("WIDGET_IDS", "").split(",")
            if x.strip()
        ]
        self.widget_filters = self._parse_filters(env("WIDGET_FILTERS_JSON", "[]"))
        self.device_query = dict(parse_qsl(env("DEVICE_QUERY", "pageSize=1000"), keep_blank_values=True))
        self.verify_ssl = to_bool(env("VERIFY_SSL", "true"))
        self.entity_prefix = to_slug(env("ENTITY_PREFIX", "nayax"))
        self.supervisor_token = env("SUPERVISOR_TOKEN")
        self.ha_base_url = env("HA_BASE_URL", "http://supervisor/core/api").rstrip("/")

        log_level = env("LOG_LEVEL", "info").upper()
        logging.basicConfig(
            level=getattr(logging, log_level, logging.INFO),
            format="%(asctime)s %(levelname)s %(message)s",
        )
        self.log = logging.getLogger("nayax_bridge")

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": normalize_auth(self.nayax_token),
                "Accept": "application/json",
            }
        )

    def _parse_filters(self, value: str) -> List[Dict[str, Any]]:
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return [x for x in parsed if isinstance(x, dict)]
        except json.JSONDecodeError:
            pass
        return []

    def _nayax_get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        url = f"{self.nayax_base_url}{path}"
        resp = self.session.get(url, params=params, timeout=30, verify=self.verify_ssl)
        resp.raise_for_status()
        return resp.json()

    def _nayax_post(self, path: str, payload: Dict[str, Any]) -> Any:
        url = f"{self.nayax_base_url}{path}"
        resp = self.session.post(url, json=payload, timeout=30, verify=self.verify_ssl)
        resp.raise_for_status()
        return resp.json()

    def _ha_set_state(self, entity_id: str, state: Any, attributes: Dict[str, Any]) -> None:
        url = f"{self.ha_base_url}/states/{entity_id}"
        headers = {
            "Authorization": f"Bearer {self.supervisor_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "state": str(state),
            "attributes": attributes,
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=20)
        resp.raise_for_status()

    def _extract_device_rows(self, payload: Any) -> List[Dict[str, Any]]:
        if isinstance(payload, list):
            return [x for x in payload if isinstance(x, dict)]
        if isinstance(payload, dict):
            for key in ("items", "Items", "data", "Data", "result", "Result"):
                value = payload.get(key)
                if isinstance(value, list):
                    return [x for x in value if isinstance(x, dict)]
        return []

    def _extract_widget_state(self, widget_payload: Dict[str, Any]) -> Any:
        data = widget_payload.get("Data")
        if isinstance(data, dict):
            for key in ("total", "Total", "value", "Value", "sum", "Sum"):
                if key in data:
                    return data[key]
            values = data.get("values") or data.get("Values")
            if isinstance(values, list):
                nums = [x for x in values if isinstance(x, (int, float))]
                if nums:
                    return round(sum(nums), 2)
        if isinstance(data, (int, float, str)):
            return data
        return "ok"

    def _discover_widget_ids(self) -> List[int]:
        widgets = self._nayax_get(
            "/operational/v1/dashboard/widgets",
            params={"screenTypeId": self.screen_type_id},
        )
        if not isinstance(widgets, list):
            return []

        selected: List[int] = []
        for widget in widgets:
            if not isinstance(widget, dict):
                continue
            wid = widget.get("WidgetTypeId")
            name = str(widget.get("WidgetName", "")).lower()
            if isinstance(wid, int) and any(
                token in name for token in ("sales", "revenue", "vend", "status", "alert")
            ):
                selected.append(wid)
        return selected

    def sync_once(self) -> None:
        devices_payload = self._nayax_get("/operational/v1/devices", params=self.device_query)
        device_rows = self._extract_device_rows(devices_payload)

        connected = 0
        for row in device_rows:
            connected_flag = row.get("isConnected")
            if connected_flag is None:
                connected_flag = row.get("IsConnected")
            if bool(connected_flag):
                connected += 1

        self._ha_set_state(
            f"sensor.{self.entity_prefix}_total_devices",
            len(device_rows),
            {
                "friendly_name": "Nayax Total Devices",
                "unit_of_measurement": "devices",
            },
        )
        self._ha_set_state(
            f"sensor.{self.entity_prefix}_connected_devices",
            connected,
            {
                "friendly_name": "Nayax Connected Devices",
                "unit_of_measurement": "devices",
            },
        )

        widget_ids = self.widget_ids or self._discover_widget_ids()
        if not widget_ids:
            self.log.warning("No widget IDs configured or auto-discovered")

        sales_total = 0.0
        for widget_id in widget_ids:
            payload = {
                "ScreenTypeId": self.screen_type_id,
                "EntityId": self.entity_id if self.entity_id > 0 else None,
                "WidgetTypeId": widget_id,
                "Filters": self.widget_filters,
            }
            widget_data = self._nayax_post("/operational/v1/dashboard/get-widget-data", payload)
            state = self._extract_widget_state(widget_data)

            details = widget_data.get("WidgetDetails", {}) if isinstance(widget_data, dict) else {}
            name = details.get("WidgetName") if isinstance(details, dict) else None
            label = str(name or f"Widget {widget_id}")
            entity_slug = to_slug(label)

            if isinstance(state, (int, float)) and any(
                token in label.lower() for token in ("sales", "revenue", "vend")
            ):
                sales_total += float(state)

            self._ha_set_state(
                f"sensor.{self.entity_prefix}_{entity_slug}",
                state,
                {
                    "friendly_name": f"Nayax {label}",
                    "widget_type_id": widget_id,
                    "widget_name": label,
                    "source": "nayax_lynx_dashboard",
                    "raw_data": widget_data.get("Data") if isinstance(widget_data, dict) else widget_data,
                },
            )

        self._ha_set_state(
            f"sensor.{self.entity_prefix}_sales_total",
            round(sales_total, 2),
            {
                "friendly_name": "Nayax Sales Total",
                "source": "calculated_from_widgets",
            },
        )

        self._ha_set_state(
            f"binary_sensor.{self.entity_prefix}_api_ok",
            "on",
            {
                "friendly_name": "Nayax API OK",
                "device_class": "connectivity",
            },
        )
        self._ha_set_state(
            f"sensor.{self.entity_prefix}_last_sync",
            time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            {
                "friendly_name": "Nayax Last Sync",
            },
        )

    def run(self) -> None:
        self.log.info("Starting Nayax bridge, poll interval=%ss", self.poll_interval)
        while True:
            try:
                self.sync_once()
                self.log.info("Sync completed")
            except Exception as exc:
                self.log.exception("Sync failed: %s", exc)
                try:
                    self._ha_set_state(
                        f"binary_sensor.{self.entity_prefix}_api_ok",
                        "off",
                        {
                            "friendly_name": "Nayax API OK",
                            "device_class": "connectivity",
                            "last_error": str(exc),
                        },
                    )
                except Exception:
                    self.log.exception("Failed to update error state in Home Assistant")

            time.sleep(self.poll_interval)


if __name__ == "__main__":
    NayaxBridge().run()
