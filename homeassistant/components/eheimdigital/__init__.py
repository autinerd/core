"""The EHEIM.digital integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import EheimUpdateCoordinator

PLATFORMS: list[Platform] = [Platform.CLIMATE]

type EheimDigitalConfigEntry = ConfigEntry[EheimUpdateCoordinator]


async def async_setup_entry(
    hass: HomeAssistant, entry: EheimDigitalConfigEntry
) -> bool:
    """Set up EHEIM.digital from a config entry."""

    coordinator = EheimUpdateCoordinator(hass)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: EheimDigitalConfigEntry
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
