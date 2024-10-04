"""Tests for the light module."""

from datetime import timedelta
from unittest.mock import MagicMock, patch

from eheimdigital.types import LightMode
from freezegun.api import FrozenDateTimeFactory
import pytest
from syrupy.assertion import SnapshotAssertion

from homeassistant.components.eheimdigital.const import EFFECT_DAYCL_MODE
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_EFFECT,
    DOMAIN as LIGHT_DOMAIN,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from tests.common import MockConfigEntry, async_fire_time_changed, snapshot_platform


@pytest.mark.parametrize(
    "tankconfig",
    [
        [["CLASSIC_DAYLIGHT"], []],
        [[], ["CLASSIC_DAYLIGHT"]],
        [["CLASSIC_DAYLIGHT"], ["CLASSIC_DAYLIGHT"]],
    ],
)
async def test_setup_classic_led_ctrl(
    hass: HomeAssistant,
    eheimdigital_hub_mock: MagicMock,
    tankconfig: list[list[str]],
    mock_config_entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
    snapshot: SnapshotAssertion,
    classic_led_ctrl_mock: MagicMock,
) -> None:
    """Test light platform setup with different channels."""
    mock_config_entry.add_to_hass(hass)

    classic_led_ctrl_mock.tankconfig = tankconfig

    eheimdigital_hub_mock.return_value.devices = {
        "00:00:00:00:00:01": classic_led_ctrl_mock
    }
    eheimdigital_hub_mock.return_value.master = classic_led_ctrl_mock

    with patch("homeassistant.components.eheimdigital.PLATFORMS", [Platform.LIGHT]):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    await snapshot_platform(hass, entity_registry, snapshot, mock_config_entry.entry_id)


async def test_setup_no_devices(
    hass: HomeAssistant,
    eheimdigital_hub_mock: MagicMock,
    entity_registry: er.EntityRegistry,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test light platform setup with different channels."""
    mock_config_entry.add_to_hass(hass)

    eheimdigital_hub_mock.return_value.devices = {}

    with patch("homeassistant.components.eheimdigital.PLATFORMS", [Platform.LIGHT]):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)

    assert (
        len(
            entity_registry.entities.get_entries_for_config_entry_id(
                mock_config_entry.entry_id
            )
        )
        == 0
    )


async def test_setup_remove_channel(
    hass: HomeAssistant,
    eheimdigital_hub_mock: MagicMock,
    mock_config_entry: MockConfigEntry,
    classic_led_ctrl_mock: MagicMock,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test light platform setup with different channels."""
    mock_config_entry.add_to_hass(hass)

    eheimdigital_hub_mock.return_value.devices = {
        "00:00:00:00:00:01": classic_led_ctrl_mock
    }
    eheimdigital_hub_mock.return_value.master = classic_led_ctrl_mock

    classic_led_ctrl_mock.tankconfig = [["CLASSIC_DAYLIGHT"], ["CLASSIC_DAYLIGHT"]]

    with patch("homeassistant.components.eheimdigital.PLATFORMS", [Platform.LIGHT]):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)

    assert len(hass.states.async_all()) == 2

    classic_led_ctrl_mock.tankconfig = [["CLASSIC_DAYLIGHT"], []]

    freezer.tick(timedelta(minutes=5))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert len(hass.states.async_all()) == 1

    classic_led_ctrl_mock.tankconfig = [["CLASSIC_DAYLIGHT"], ["CLASSIC_DAYLIGHT"]]

    freezer.tick(timedelta(minutes=5))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert len(hass.states.async_all()) == 2


async def test_turn_off(
    hass: HomeAssistant,
    eheimdigital_hub_mock: MagicMock,
    mock_config_entry: MockConfigEntry,
    classic_led_ctrl_mock: MagicMock,
) -> None:
    """Test turning off the light."""
    mock_config_entry.add_to_hass(hass)

    eheimdigital_hub_mock.return_value.devices = {
        "00:00:00:00:00:01": classic_led_ctrl_mock
    }
    eheimdigital_hub_mock.return_value.master = classic_led_ctrl_mock

    with patch("homeassistant.components.eheimdigital.PLATFORMS", [Platform.LIGHT]):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: "light.mock_classicledcontrol_e_channel_0"},
        blocking=True,
    )

    classic_led_ctrl_mock.set_light_mode.assert_awaited_once_with(LightMode.MAN_MODE)
    classic_led_ctrl_mock.turn_off.assert_awaited_once_with(0)


@pytest.mark.parametrize(
    ("dim_input", "expected_dim_value"),
    [
        (3, 1),
        (255, 100),
        (128, 50),
    ],
)
async def test_turn_on_brightness(
    hass: HomeAssistant,
    eheimdigital_hub_mock: MagicMock,
    mock_config_entry: MockConfigEntry,
    classic_led_ctrl_mock: MagicMock,
    dim_input: int,
    expected_dim_value: int,
) -> None:
    """Test turning on the light with different brightness values."""
    mock_config_entry.add_to_hass(hass)

    eheimdigital_hub_mock.return_value.devices = {
        "00:00:00:00:00:01": classic_led_ctrl_mock
    }
    eheimdigital_hub_mock.return_value.master = classic_led_ctrl_mock

    with patch("homeassistant.components.eheimdigital.PLATFORMS", [Platform.LIGHT]):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {
            ATTR_ENTITY_ID: "light.mock_classicledcontrol_e_channel_0",
            ATTR_BRIGHTNESS: dim_input,
        },
        blocking=True,
    )

    classic_led_ctrl_mock.set_light_mode.assert_awaited_once_with(LightMode.MAN_MODE)
    classic_led_ctrl_mock.turn_on.assert_awaited_once_with(expected_dim_value, 0)


async def test_turn_on_effect(
    hass: HomeAssistant,
    eheimdigital_hub_mock: MagicMock,
    mock_config_entry: MockConfigEntry,
    classic_led_ctrl_mock: MagicMock,
) -> None:
    """Test turning on the light with an effect value."""
    mock_config_entry.add_to_hass(hass)

    eheimdigital_hub_mock.return_value.devices = {
        "00:00:00:00:00:01": classic_led_ctrl_mock
    }
    eheimdigital_hub_mock.return_value.master = classic_led_ctrl_mock

    classic_led_ctrl_mock.light_mode = LightMode.MAN_MODE

    with patch("homeassistant.components.eheimdigital.PLATFORMS", [Platform.LIGHT]):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {
            ATTR_ENTITY_ID: "light.mock_classicledcontrol_e_channel_0",
            ATTR_EFFECT: EFFECT_DAYCL_MODE,
        },
        blocking=True,
    )

    classic_led_ctrl_mock.set_light_mode.assert_awaited_once_with(LightMode.DAYCL_MODE)
