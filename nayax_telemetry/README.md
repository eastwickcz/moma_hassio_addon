# Nayax Telemetry Bridge

Home Assistant add-on for pulling Nayax sales and machine status data from Lynx API.

## Configuration

```yaml
nayax_base_url: https://lynx.nayax.com
nayax_token: YOUR_NAYAX_TOKEN
poll_interval: 300
screen_type_id: 1
entity_id: 0
widget_ids: []
widget_filters_json: "[]"
device_query: "pageSize=1000"
verify_ssl: true
entity_prefix: nayax
log_level: info
```

## Notes

- `nayax_token` is required.
- `widget_ids` should contain widget type IDs from your Nayax dashboard.
- If `widget_ids` is empty, the add-on tries auto-discovery from available widgets.
- `entity_id` can be left as `0` when not needed by your widget setup.

## Created Home Assistant Entities

- `sensor.<entity_prefix>_total_devices`
- `sensor.<entity_prefix>_connected_devices`
- `sensor.<entity_prefix>_sales_total`
- `sensor.<entity_prefix>_last_sync`
- `binary_sensor.<entity_prefix>_api_ok`
- `sensor.<entity_prefix>_<widget_name_slug>` for each requested widget
