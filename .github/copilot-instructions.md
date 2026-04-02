# Copilot Instructions

## Project overview

Home Assistant custom integration that reads UPS (Uninterruptible Power Supply) status from SMS-brand devices over USB serial. It is distributed via HACS and validated with `hassfest`.

## Commands

```bash
# Install dependencies
scripts/setup                    # or: python3 -m pip install -r requirements.txt

# Lint (format + check with auto-fix)
scripts/lint                     # or: ruff format . && ruff check . --fix

# Lint check only (as CI does)
python3 -m ruff check .
python3 -m ruff format . --check

# Run local HA instance for manual testing
scripts/develop                  # starts Home Assistant on http://localhost:8123
```

There is no automated test suite.

## Architecture

```
api.py              USB serial client — all I/O is blocking; must be called via hass.async_add_executor_job()
coordinator.py      DataUpdateCoordinator — polls api.py every 3 s; wraps errors as UpdateFailed
entity.py           SmsUpsEntity base — sets device_info and attribution for all platforms
sensor.py           Numeric sensors (voltage, power, Hz, battery %, temperature)
binary_sensor.py    Boolean sensors (on-battery, low-battery, bypass, boost, etc.)
switch.py           Switch platform (stub — not yet wired to real commands)
config_flow.py      UI config flow — discovers serial ports; unique ID = port path
data.py             SmsUpsConfigEntry type alias and SmsUpsData dataclass (stored in entry.runtime_data)
const.py            DOMAIN, LOGGER, shared config-entry keys
```

Data flows: `api.get_data()` → `coordinator.data` (a `dict[str, Any]`) → each platform reads its key via `entity_description.key`.

## Key conventions

**Blocking I/O always in executor**  
`api.py` methods (`connect`, `disconnect`, `get_data`) are synchronous/blocking. Always call them with `await hass.async_add_executor_job(...)`, never directly from async context.

**Entity keys must match `api.get_data()` output**  
`ENTITY_DESCRIPTIONS` in each platform file use `key=` values that must exactly match the dict keys returned by `SmsUpsSerialClient.get_data()` (e.g. `"inputVac"`, `"batteryLevel"`, `"onBattery"`). The coordinator stores this dict as `coordinator.data`.

**TYPE_CHECKING imports**  
HA types used only for type hints are imported inside `if TYPE_CHECKING:` blocks to avoid circular imports and keep runtime overhead low. Use `from __future__ import annotations` at the top of every file.

**PYTHONPATH for development**  
The `scripts/develop` script exports `PYTHONPATH` to include the repo root's `custom_components/` directory. This allows HA to find the integration even though it lives at `custom_components/sms-ups/` (one level deeper than a normal install).

**Ruff config**  
`ruff` is configured in `.ruff.toml` targeting Python 3.14 with `select = ["ALL"]`. Ignored rules: `ANN401`, `D203`, `D212`, `COM812`, `ISC001`. Max cyclomatic complexity is 25.

**Unique ID = port path**  
The config entry unique ID is the USB port device path (e.g. `/dev/ttyUSB0`). This prevents duplicate entries for the same physical device.
