"""DataUpdateCoordinator for iotty."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
import logging
from typing import TYPE_CHECKING

from iottycloud.verbs import RESULT, STATUS

from homeassistant.helpers import aiohttp_client, device_registry as dr
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from . import api
from .const import DOMAIN

if TYPE_CHECKING:
    from iottycloud.device import Device

    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.config_entry_oauth2_flow import OAuth2Session
    from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(seconds=30)


@dataclass
class IottyData:
    """iotty data stored in the DataUpdateCoordinator."""

    devices: list[Device]


class IottyDataUpdateCoordinator(DataUpdateCoordinator[IottyData]):
    """Class to manage fetching Iotty data."""

    config_entry: ConfigEntry
    _entities: dict[str, Entity]
    _devices: list[Device]
    _device_registry: dr.DeviceRegistry

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, session: OAuth2Session
    ) -> None:
        """Initialize the coordinator."""
        _LOGGER.debug("Initializing iotty data update coordinator")

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_coordinator",
            update_interval=UPDATE_INTERVAL,
        )

        self.config_entry = entry
        self._entities = {}
        self._devices = []
        self.iotty = api.IottyProxy(
            hass, aiohttp_client.async_get_clientsession(hass), session
        )
        self._device_registry = dr.async_get(hass)

    async def async_config_entry_first_refresh(self) -> None:
        """Override the first refresh to also fetch iotty devices list."""
        _LOGGER.debug("Fetching devices list from iottyCloud")
        self._devices = await self.iotty.get_devices()
        _LOGGER.debug("There are %d devices", len(self._devices))

        await super().async_config_entry_first_refresh()

    async def _async_update_data(self) -> IottyData:
        """Fetch data from iottyCloud device."""
        _LOGGER.debug("Fetching devices status from iottyCloud")

        current_devices = await self.iotty.get_devices()

        removed_devices = [
            d
            for d in self._devices
            if not any(x.device_id == d.device_id for x in current_devices)
        ]

        for removed_device in removed_devices:
            device_to_remove = self._device_registry.async_get_device(
                {(DOMAIN, removed_device.device_id)}
            )
            if device_to_remove is not None:
                self._device_registry.async_remove_device(device_to_remove.id)

        self._devices = current_devices

        for device in self._devices:
            res = await self.iotty.get_status(device.device_id)
            json = res.get(RESULT, {})
            if (
                not isinstance(res, dict)
                or RESULT not in res
                or not isinstance(json := res[RESULT], dict)
                or not (status := json.get(STATUS))
            ):
                _LOGGER.warning("Unable to read status for device %s", device.device_id)
            else:
                _LOGGER.debug(
                    "Retrieved status: '%s' for device %s", status, device.device_id
                )
                device.update_status(status)

        return IottyData(self._devices)
