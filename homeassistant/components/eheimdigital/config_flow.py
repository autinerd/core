"""Config flow for EHEIM.digital."""

from eheimdigital.hub import EheimDigitalHub

from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_flow

from .const import DOMAIN


async def _async_has_devices(hass: HomeAssistant) -> bool:
    """Return if there are devices that can be discovered."""
    devices = await hass.async_add_executor_job(EheimDigitalHub().discover_devices)
    return len(devices) > 0


config_entry_flow.register_discovery_flow(DOMAIN, "EHEIM.digital", _async_has_devices)
