"""DataUpdateCoordinator for custom_components/sms-ups."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import SmsUpsSerialClientCommunicationError, SmsUpsSerialClientError

if TYPE_CHECKING:
    from .data import SmsUpsConfigEntry


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class SmsUpsDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinator that polls UPS data via USB serial."""

    config_entry: SmsUpsConfigEntry

    async def _async_update_data(self) -> Any:
        """Fetch latest UPS data from the serial port."""
        client = self.config_entry.runtime_data.client
        try:
            return await self.hass.async_add_executor_job(client.get_data)
        except SmsUpsSerialClientCommunicationError as exception:
            msg = f"UPS communication error: {exception}"
            raise UpdateFailed(msg) from exception
        except SmsUpsSerialClientError as exception:
            msg = f"UPS serial error: {exception}"
            raise UpdateFailed(msg) from exception
