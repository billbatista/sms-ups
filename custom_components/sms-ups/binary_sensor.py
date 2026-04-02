"""Binary sensor platform for custom_components/sms-ups."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)

from .entity import SmsUpsEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import SmsUpsDataUpdateCoordinator
    from .data import SmsUpsConfigEntry

ENTITY_DESCRIPTIONS = (
    BinarySensorEntityDescription(
        key="onBattery",
        name="On Battery",
        device_class=BinarySensorDeviceClass.RUNNING,
    ),
    BinarySensorEntityDescription(
        key="lowBattery",
        name="Low Battery",
        device_class=BinarySensorDeviceClass.BATTERY,
    ),
    BinarySensorEntityDescription(
        key="upsOk",
        name="Status",
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    BinarySensorEntityDescription(
        key="testActive",
        name="Running test",
        device_class=BinarySensorDeviceClass.RUNNING,
    ),
    BinarySensorEntityDescription(
        key="beepOn",
        name="Alarm Muted",
        icon="mdi:alarm",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: SmsUpsConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary_sensor platform."""
    async_add_entities(
        SmsUpsBinarySensor(
            coordinator=entry.runtime_data.coordinator,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    )


class SmsUpsBinarySensor(SmsUpsEntity, BinarySensorEntity):
    """SMS UPS binary_sensor class."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SmsUpsDataUpdateCoordinator,
        entity_description: BinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary_sensor class."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_{entity_description.key}"
        )

    @property
    def is_on(self) -> bool:
        """Return true if the binary_sensor is on."""
        if self.coordinator.data is None:
            return False

        original_value = self.coordinator.data.get(self.entity_description.key, False)

        if self.entity_description.key == "upsOk":
            return not original_value
        if self.entity_description.key == "beepOn":
            return not original_value

        return original_value
