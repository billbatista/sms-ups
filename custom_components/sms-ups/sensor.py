"""Sensor platform for custom_components/sms-ups."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfElectricPotential, UnitOfPower

from .const import CONF_NOBREAK_POWER_FACTOR, CONF_NOBREAK_TOTAL_POWER
from .entity import SmsUpsEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import SmsUpsDataUpdateCoordinator
    from .data import SmsUpsConfigEntry

ENTITY_DESCRIPTIONS = (
    SensorEntityDescription(
        key="inputVac",
        name="Input Voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
    ),
    SensorEntityDescription(
        key="outputPower",
        name="Output Power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: SmsUpsConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    async_add_entities(
        SmsUpsSensor(
            coordinator=entry.runtime_data.coordinator,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    )


class SmsUpsSensor(SmsUpsEntity, SensorEntity):
    """SMS UPS Sensor class."""

    def __init__(
        self,
        coordinator: SmsUpsDataUpdateCoordinator,
        entity_description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor class."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_{entity_description.key}"
        )

    @property
    def native_value(self) -> float | None:
        """Return the sensor value from coordinator data using the description key."""
        if self.coordinator.data is None:
            return None

        raw = self.coordinator.data.get(self.entity_description.key)

        if raw is None:
            return None

        if self.entity_description.key == "outputPower":
            entry_data = self.coordinator.config_entry.data
            total_power: float = entry_data[CONF_NOBREAK_TOTAL_POWER]
            power_factor: float = entry_data[CONF_NOBREAK_POWER_FACTOR]
            return (raw * total_power) * power_factor / 100

        return raw
