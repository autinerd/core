"""Support for the EHEIM.digital aquarium heater."""
from eheimdigital.EheimDigitalHeater import EheimDigitalHeater
from eheimdigital.EheimDigitalHub import EheimDigitalHub

from homeassistant.components.climate import (
    ATTR_HVAC_MODE,
    ATTR_TEMPERATURE,
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PRECISION_TENTHS, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo, format_mac
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import EheimUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the EHEIM.digital aquarium heater."""
    coordinator: EheimUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    await coordinator.async_config_entry_first_refresh()
    async_add_entities(
        [
            EheimEHeater(coordinator, device.mac_address)
            for device in await EheimDigitalHub().discover_devices()
            if type(device) == EheimDigitalHeater
        ]
    )


class EheimEHeater(CoordinatorEntity, ClimateEntity):
    """Representation of an EHEIM thermocontrol+ aquarium heater."""

    coordinator: EheimUpdateCoordinator
    _attr_precision = PRECISION_TENTHS
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]
    _attr_hvac_mode = HVACMode.OFF
    _attr_has_entity_name = True
    _attr_name = None

    def __init__(self, coordinator: EheimUpdateCoordinator, mac_address) -> None:
        """Initialize an EHEIM thermocontrol+ aquarium heater."""
        super().__init__(coordinator, context=mac_address)
        self.mac_address = mac_address
        if self.coordinator.data is None:
            self._attr_available = False
            return
        usrdta = [
            a
            for a in self.coordinator.data
            if "title" in a and a["title"] == "USRDTA" and a["from"] == self.mac_address
        ][0]
        heater_data = [
            a
            for a in self.coordinator.data
            if "title" in a
            and a["title"] == "HEATER_DATA"
            and a["from"] == self.mac_address
        ][0]
        self._attr_temperature_unit = (
            UnitOfTemperature.FAHRENHEIT
            if heater_data["mUnit"] == 1
            else UnitOfTemperature.CELSIUS
        )
        self._attr_min_temp = (
            18.0 if self._attr_temperature_unit == UnitOfTemperature.CELSIUS else 64.0
        )
        self._attr_max_temp = (
            32.0 if self._attr_temperature_unit == UnitOfTemperature.CELSIUS else 90.0
        )
        self._attr_unique_id = format_mac(mac_address)
        self._attr_device_info = DeviceInfo(
            name=usrdta["name"],
            identifiers={(DOMAIN, mac_address)},
            configuration_url="http://eheimdigital/",
            manufacturer="EHEIM",
            model="EHEIM thermocontrol+",
            sw_version=f"{usrdta['revision'][0] // 1000}.{(usrdta['revision'][0] % 1000) // 100}.{usrdta['revision'][0] % 100}_{usrdta['revision'][1] // 1000}.{(usrdta['revision'][1] % 1000) // 100}.{usrdta['revision'][1] % 100}",
        )
        self._attr_current_temperature = heater_data["isTemp"] / 10
        self._attr_target_temperature = heater_data["sollTemp"] / 10
        self._attr_hvac_mode = (
            HVACMode.HEAT if heater_data["active"] == 1 else HVACMode.OFF
        )
        self._attr_hvac_action = (
            HVACAction.HEATING if heater_data["isHeating"] == 1 else HVACAction.IDLE
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        if self.coordinator.data is None:
            self._attr_available = False
            return
        heater_data = [
            a
            for a in self.coordinator.data
            if "title" in a
            and a["title"] == "HEATER_DATA"
            and a["from"] == self.mac_address
        ][0]
        self._attr_current_temperature = heater_data["isTemp"] / 10
        self._attr_target_temperature = heater_data["sollTemp"] / 10
        self._attr_hvac_mode = (
            HVACMode.HEAT if heater_data["active"] == 1 else HVACMode.OFF
        )
        self._attr_hvac_action = (
            HVACAction.HEATING if heater_data["isHeating"] == 1 else HVACAction.IDLE
        )
        self.async_write_ha_state()

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        if kwargs.get(ATTR_HVAC_MODE) is not None:
            hvac_mode = kwargs[ATTR_HVAC_MODE]
            await self.async_set_hvac_mode(hvac_mode)
        elif kwargs.get(ATTR_TEMPERATURE) is not None:
            temperature = kwargs[ATTR_TEMPERATURE]
            EheimDigitalHeater(EheimDigitalHub(), self.mac_address).set_target_temp(
                temperature
            )
        await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new operation mode."""
        EheimDigitalHeater(EheimDigitalHub(), self.mac_address).set_active(
            hvac_mode == HVACMode.HEAT
        )
        await self.coordinator.async_request_refresh()
