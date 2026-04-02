"""Constants for custom_components/sms-ups."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "custom_components/sms-ups"
ATTRIBUTION = "Data provided by SMS UPS via USB serial."

CONF_USB_PORT = "usb_port"
CONF_NOBREAK_TOTAL_POWER = "nobreak_total_power"
CONF_NOBREAK_POWER_FACTOR = "nobreak_power_factor"
