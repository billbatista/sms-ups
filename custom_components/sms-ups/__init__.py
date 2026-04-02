"""
Custom integration to integrate custom_components/sms-ups with Home Assistant.

For more details about this integration, please refer to
https://github.com/billbatista/custom_components/sms-ups
"""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.const import Platform
from homeassistant.loader import async_get_loaded_integration

from .api import SmsUpsSerialClient
from .const import CONF_USB_PORT, DOMAIN, LOGGER
from .coordinator import SmsUpsDataUpdateCoordinator
from .data import SmsUpsData

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import SmsUpsConfigEntry

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
]


# https://developers.home-assistant.io/docs/config_entries_index/#setting-up-an-entry
async def async_setup_entry(
    hass: HomeAssistant,
    entry: SmsUpsConfigEntry,
) -> bool:
    """Set up this integration using UI."""
    usb_port = entry.data[CONF_USB_PORT]
    LOGGER.debug("Setting up SMS UPS on port %s", usb_port)

    client = SmsUpsSerialClient(port=usb_port)
    await hass.async_add_executor_job(client.connect)

    coordinator = SmsUpsDataUpdateCoordinator(
        hass=hass,
        logger=LOGGER,
        name=DOMAIN,
        update_interval=timedelta(seconds=3),
    )
    entry.runtime_data = SmsUpsData(
        client=client,
        integration=async_get_loaded_integration(hass, entry.domain),
        coordinator=coordinator,
    )

    # https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: SmsUpsConfigEntry,
) -> bool:
    """Handle removal of an entry."""
    await hass.async_add_executor_job(entry.runtime_data.client.disconnect)
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(
    hass: HomeAssistant,
    entry: SmsUpsConfigEntry,
) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)
