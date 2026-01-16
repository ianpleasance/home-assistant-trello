"""Config flow for Trello integration."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv

from .const import (
    CONF_API_KEY,
    CONF_API_TOKEN,
    CONF_BOARDS,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    MAX_UPDATE_INTERVAL,
    MIN_UPDATE_INTERVAL,
    TRELLO_API_BASE,
)

_LOGGER = logging.getLogger(__name__)

# Try to use asyncio.timeout (Python 3.11+) or fall back to async_timeout
try:
    from asyncio import timeout as async_timeout
except ImportError:
    try:
        from async_timeout import timeout as async_timeout
    except ImportError:
        # Last resort - create a simple timeout wrapper
        from contextlib import asynccontextmanager
        
        @asynccontextmanager
        async def async_timeout(seconds):
            """Simple timeout context manager."""
            try:
                yield
            except asyncio.TimeoutError:
                raise TimeoutError(f"Timeout after {seconds} seconds")

class TrelloConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Trello."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._api_key: str | None = None
        self._api_token: str | None = None
        self._boards: list[dict[str, str]] = []
        self._member_name: str | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            self._api_key = user_input[CONF_API_KEY]
            self._api_token = user_input[CONF_API_TOKEN]

            try:
                session = async_get_clientsession(self.hass)
                params = {"key": self._api_key, "token": self._api_token}
                
                # Test the credentials and get member info
                _LOGGER.debug("Testing Trello credentials")
                async with async_timeout(10):
                    member_url = f"{TRELLO_API_BASE}/members/me"
                    async with session.get(member_url, params=params) as response:
                        if response.status == 401:
                            errors["base"] = "invalid_auth"
                        elif response.status != 200:
                            _LOGGER.error("Trello API returned status %s", response.status)
                            errors["base"] = "cannot_connect"
                        else:
                            member_data = await response.json()
                            self._member_name = (
                                member_data.get("username") 
                                or member_data.get("fullName") 
                                or "Trello Account"
                            )
                            _LOGGER.debug("Member name: %s", self._member_name)
                
                if not errors:
                    # Fetch boards
                    _LOGGER.debug("Fetching boards list")
                    async with async_timeout(10):
                        boards_url = f"{TRELLO_API_BASE}/members/me/boards"
                        boards_params = {**params, "filter": "open"}
                        async with session.get(boards_url, params=boards_params) as response:
                            if response.status != 200:
                                _LOGGER.error("Failed to fetch boards: status %s", response.status)
                                errors["base"] = "cannot_connect"
                            else:
                                boards_data = await response.json()
                                self._boards = [
                                    {"id": board["id"], "name": board["name"]}
                                    for board in boards_data
                                ]
                                _LOGGER.debug("Found %d boards", len(self._boards))

                if not errors:
                    return await self.async_step_boards()

            except aiohttp.ClientError as err:
                _LOGGER.error("Connection error: %s", err)
                errors["base"] = "cannot_connect"
            except (TimeoutError, asyncio.TimeoutError):
                _LOGGER.error("Timeout connecting to Trello")
                errors["base"] = "cannot_connect"
            except Exception as err:
                _LOGGER.exception("Unexpected exception: %s", err)
                errors["base"] = "cannot_connect"

        data_schema = vol.Schema(
            {
                vol.Required(CONF_API_KEY): str,
                vol.Required(CONF_API_TOKEN): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "docs_url": "https://trello.com/app-key"
            },
        )

    async def async_step_boards(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle board selection step."""
        errors = {}

        if user_input is not None:
            selected_boards = user_input[CONF_BOARDS]
            update_interval = user_input.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)

            # Create a unique ID based on the API key
            await self.async_set_unique_id(self._api_key)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"Trello ({self._member_name})",
                data={
                    CONF_API_KEY: self._api_key,
                    CONF_API_TOKEN: self._api_token,
                    CONF_BOARDS: selected_boards,
                    CONF_UPDATE_INTERVAL: update_interval,
                },
            )

        if not self._boards:
            return self.async_abort(reason="no_boards")

        board_options = {board["id"]: board["name"] for board in self._boards}

        data_schema = vol.Schema(
            {
                vol.Required(CONF_BOARDS): cv.multi_select(board_options),
                vol.Optional(
                    CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL
                ): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=MIN_UPDATE_INTERVAL, max=MAX_UPDATE_INTERVAL),
                ),
            }
        )

        return self.async_show_form(
            step_id="boards",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "board_count": str(len(self._boards))
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> TrelloOptionsFlow:
        """Get the options flow for this handler."""
        return TrelloOptionsFlow(config_entry)


class TrelloOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Trello integration."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        errors = {}

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_interval = self.config_entry.options.get(
            CONF_UPDATE_INTERVAL,
            self.config_entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
        )

        options_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_UPDATE_INTERVAL,
                    default=current_interval,
                ): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=MIN_UPDATE_INTERVAL, max=MAX_UPDATE_INTERVAL),
                ),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=options_schema,
            errors=errors,
        )
