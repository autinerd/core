"""IMAP sensor support."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import CONF_USERNAME
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ImapDataUpdateCoordinator

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from . import ImapConfigEntry

IMAP_MAIL_COUNT_DESCRIPTION = SensorEntityDescription(
    key="imap_mail_count",
    state_class=SensorStateClass.MEASUREMENT,
    suggested_display_precision=0,
    translation_key="imap_mail_count",
    name=None,
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ImapConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Imap sensor."""

    coordinator = entry.runtime_data
    async_add_entities([ImapSensor(coordinator, IMAP_MAIL_COUNT_DESCRIPTION)])


class ImapSensor(CoordinatorEntity[ImapDataUpdateCoordinator], SensorEntity):
    """Representation of an IMAP sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ImapDataUpdateCoordinator,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
            name=f"IMAP ({coordinator.config_entry.data[CONF_USERNAME]})",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def native_value(self) -> int | None:
        """Return the number of emails found."""
        return self.coordinator.data
