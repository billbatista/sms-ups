"""Adds config flow for SMS UPS."""

from __future__ import annotations

import serial
import serial.tools.list_ports
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import (
    CONF_NOBREAK_POWER_FACTOR,
    CONF_NOBREAK_TOTAL_POWER,
    CONF_USB_PORT,
    DOMAIN,
    LOGGER,
)


class SmsUpsFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for SMS UPS."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle a flow initialized by the user."""
        _errors = {}

        if user_input is not None:
            port = user_input[CONF_USB_PORT]
            try:
                await self.hass.async_add_executor_job(self._test_port, port)
            except serial.SerialException as exception:
                LOGGER.error("Cannot open serial port %s: %s", port, exception)
                _errors["base"] = "cannot_connect"
            except Exception as exception:  # noqa: BLE001
                LOGGER.exception(exception)
                _errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(port)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"SMS UPS ({port})",
                    data={
                        CONF_USB_PORT: port,
                        CONF_NOBREAK_TOTAL_POWER: user_input[CONF_NOBREAK_TOTAL_POWER],
                        CONF_NOBREAK_POWER_FACTOR: user_input[
                            CONF_NOBREAK_POWER_FACTOR
                        ],
                    },
                )

        ports = await self.hass.async_add_executor_job(self._get_serial_ports)

        if ports:
            default_port = (user_input or {}).get(CONF_USB_PORT, next(iter(ports)))
            port_field = selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[
                        selector.SelectOptionDict(value=k, label=v)
                        for k, v in ports.items()
                    ],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    custom_value=True,
                ),
            )
        else:
            default_port = (user_input or {}).get(CONF_USB_PORT, vol.UNDEFINED)
            port_field = selector.TextSelector(
                selector.TextSelectorConfig(
                    type=selector.TextSelectorType.TEXT,
                ),
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USB_PORT, default=default_port): port_field,
                    vol.Required(
                        CONF_NOBREAK_TOTAL_POWER,
                        default=(user_input or {}).get(
                            CONF_NOBREAK_TOTAL_POWER, vol.UNDEFINED
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=100,
                            max=10000,
                            step=1,
                            unit_of_measurement="W",
                            mode=selector.NumberSelectorMode.BOX,
                        ),
                    ),
                    vol.Required(
                        CONF_NOBREAK_POWER_FACTOR,
                        default=(user_input or {}).get(
                            CONF_NOBREAK_POWER_FACTOR, vol.UNDEFINED
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=0.1,
                            max=1.0,
                            step=0.01,
                            mode=selector.NumberSelectorMode.BOX,
                        ),
                    ),
                }
            ),
            errors=_errors,
        )

    @staticmethod
    def _get_serial_ports() -> dict[str, str]:
        """Return available serial ports as {device: label} mapping."""
        ports = {}
        for port in serial.tools.list_ports.comports():
            description = port.description or port.device
            ports[port.device] = f"{port.device} — {description}"
        return ports

    @staticmethod
    def _test_port(port: str) -> None:
        """Attempt to open the serial port to verify it is accessible."""
        ser = serial.Serial(
            port,
            baudrate=2400,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=2,
        )
        ser.close()
