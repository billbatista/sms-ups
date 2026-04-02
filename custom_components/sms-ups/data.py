"""Custom types for custom_components/sms-ups."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration

    from .api import SmsUpsSerialClient
    from .coordinator import SmsUpsDataUpdateCoordinator


type SmsUpsConfigEntry = ConfigEntry[SmsUpsData]


@dataclass
class SmsUpsData:
    """Data for the SMS UPS integration."""

    client: SmsUpsSerialClient
    coordinator: SmsUpsDataUpdateCoordinator
    integration: Integration
