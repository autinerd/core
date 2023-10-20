"""Data update coordinator for EHEIM.digital devices."""
from datetime import timedelta
import logging

from eheimdigital.EheimDigitalHub import EheimDigitalHub

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN


class EheimUpdateCoordinator(DataUpdateCoordinator):
    """EHEIM.digital device data update coordinator."""

    def __init__(self, hass):
        """Initialize the data update coordinator."""
        super().__init__(
            hass,
            logging.getLogger(__package__),
            name=DOMAIN,
            update_interval=timedelta(seconds=30),
        )
        self.hub = EheimDigitalHub()

    async def _async_update_data(self):
        return self.hub.fetch_data()
