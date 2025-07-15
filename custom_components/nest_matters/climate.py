"""Climate platform for Nest Matters integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    CONF_GOOGLE_ENTITY,
    CONF_MATTER_ENTITY,
    CONF_NAME,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Nest Matters climate platform."""
    config = hass.data[DOMAIN][config_entry.entry_id]
    
    climate_entity = NestMattersClimate(
        hass,
        config[CONF_NAME],
        config[CONF_MATTER_ENTITY],
        config[CONF_GOOGLE_ENTITY],
        config_entry.entry_id,
    )
    
    async_add_entities([climate_entity])

class NestMattersClimate(ClimateEntity):
    """Unified climate entity combining Matter and Google Nest."""

    def __init__(
        self,
        hass: HomeAssistant,
        name: str,
        matter_entity_id: str,
        google_entity_id: str,
        entry_id: str,
    ) -> None:
        """Initialize the unified climate entity."""
        self.hass = hass
        self._attr_name = name
        self._matter_entity_id = matter_entity_id
        self._google_entity_id = google_entity_id
        self._entry_id = entry_id
        
        # Set unique ID
        self._attr_unique_id = f"{DOMAIN}_{entry_id}"
        
        # Initialize state
        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_supported_features = (
            ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.FAN_MODE
        )
        
        # Track state changes of source entities
        self._remove_listeners = []

    async def async_added_to_hass(self) -> None:
        """Handle entity added to hass."""
        # Listen for changes in source entities
        self._remove_listeners.append(
            async_track_state_change_event(
                self.hass, 
                [self._matter_entity_id, self._google_entity_id],
                self._handle_source_state_change
            )
        )
        
        # Initial state update
        await self.async_update()

    async def async_will_remove_from_hass(self) -> None:
        """Handle entity removal."""
        for remove_listener in self._remove_listeners:
            remove_listener()

    async def _handle_source_state_change(self, event) -> None:
        """Handle state changes from source entities."""
        self.async_write_ha_state()

    @property
    def current_temperature(self) -> float | None:
        """Return current temperature from Matter entity (more responsive)."""
        matter_state = self.hass.states.get(self._matter_entity_id)
        if matter_state and matter_state.attributes:
            return matter_state.attributes.get("current_temperature")
        return None

    @property
    def target_temperature(self) -> float | None:
        """Return target temperature from Matter entity."""
        matter_state = self.hass.states.get(self._matter_entity_id)
        if matter_state and matter_state.attributes:
            return matter_state.attributes.get("temperature")
        return None

    @property
    def hvac_mode(self) -> HVACMode | None:
        """Return HVAC mode from Google entity."""
        google_state = self.hass.states.get(self._google_entity_id)
        if google_state:
            return google_state.state
        return None

    @property
    def hvac_modes(self) -> list[HVACMode]:
        """Return available HVAC modes from Google entity."""
        google_state = self.hass.states.get(self._google_entity_id)
        if google_state and google_state.attributes:
            return google_state.attributes.get("hvac_modes", [])
        return []

    @property
    def fan_mode(self) -> str | None:
        """Return fan mode from Google entity."""
        google_state = self.hass.states.get(self._google_entity_id)
        if google_state and google_state.attributes:
            return google_state.attributes.get("fan_mode")
        return None

    @property
    def fan_modes(self) -> list[str]:
        """Return available fan modes from Google entity."""
        google_state = self.hass.states.get(self._google_entity_id)
        if google_state and google_state.attributes:
            return google_state.attributes.get("fan_modes", [])
        return []

    @property
    def current_humidity(self) -> int | None:
        """Return current humidity from Google entity."""
        google_state = self.hass.states.get(self._google_entity_id)
        if google_state and google_state.attributes:
            return google_state.attributes.get("current_humidity")
        return None

    @property
    def min_temp(self) -> float:
        """Return minimum temperature from Matter entity."""
        matter_state = self.hass.states.get(self._matter_entity_id)
        if matter_state and matter_state.attributes:
            return matter_state.attributes.get("min_temp", 7)
        return 7

    @property
    def max_temp(self) -> float:
        """Return maximum temperature from Matter entity."""
        matter_state = self.hass.states.get(self._matter_entity_id)
        if matter_state and matter_state.attributes:
            return matter_state.attributes.get("max_temp", 35)
        return 35

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        matter_state = self.hass.states.get(self._matter_entity_id)
        google_state = self.hass.states.get(self._google_entity_id)
        
        return (
            matter_state is not None 
            and matter_state.state != "unavailable"
            and google_state is not None 
            and google_state.state != "unavailable"
        )

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set temperature via Matter entity (avoid rate limits)."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return

        _LOGGER.debug(
            "Setting temperature to %s via Matter entity %s", 
            temperature, 
            self._matter_entity_id
        )

        await self.hass.services.async_call(
            "climate",
            "set_temperature",
            {
                "entity_id": self._matter_entity_id,
                "temperature": temperature,
            },
        )

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set HVAC mode via Google entity (full features)."""
        _LOGGER.debug(
            "Setting HVAC mode to %s via Google entity %s", 
            hvac_mode, 
            self._google_entity_id
        )

        await self.hass.services.async_call(
            "climate",
            "set_hvac_mode",
            {
                "entity_id": self._google_entity_id,
                "hvac_mode": hvac_mode,
            },
        )

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set fan mode via Google entity."""
        _LOGGER.debug(
            "Setting fan mode to %s via Google entity %s", 
            fan_mode, 
            self._google_entity_id
        )

        await self.hass.services.async_call(
            "climate",
            "set_fan_mode",
            {
                "entity_id": self._google_entity_id,
                "fan_mode": fan_mode,
            },
        )

    async def async_update(self) -> None:
        """Update the entity state."""
        # Force update of state - the properties will pull from source entities
        pass