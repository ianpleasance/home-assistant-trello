"""The Trello integration."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_API_KEY,
    CONF_API_TOKEN,
    CONF_BOARDS,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    TRELLO_API_BASE,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

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


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Trello from a config entry."""
    api_key = entry.data[CONF_API_KEY]
    api_token = entry.data[CONF_API_TOKEN]
    boards = entry.data.get(CONF_BOARDS, [])
    update_interval = entry.options.get(
        CONF_UPDATE_INTERVAL, 
        entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
    )

    session = async_get_clientsession(hass)
    
    # Test the connection
    try:
        async with async_timeout(10):
            url = f"{TRELLO_API_BASE}/members/me"
            params = {"key": api_key, "token": api_token}
            async with session.get(url, params=params) as response:
                if response.status == 401:
                    raise ConfigEntryAuthFailed("Invalid API key or token")
                elif response.status != 200:
                    raise ConfigEntryNotReady(f"Trello API returned status {response.status}")
                await response.json()
    except aiohttp.ClientError as err:
        raise ConfigEntryNotReady(f"Unable to connect to Trello: {err}") from err
    except (TimeoutError, asyncio.TimeoutError) as err:
        raise ConfigEntryNotReady(f"Timeout connecting to Trello: {err}") from err

    coordinator = TrelloDataUpdateCoordinator(
        hass,
        session=session,
        api_key=api_key,
        api_token=api_token,
        boards=boards,
        update_interval=timedelta(minutes=update_interval),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


class TrelloDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Trello data."""

    def __init__(
        self,
        hass: HomeAssistant,
        session: aiohttp.ClientSession,
        api_key: str,
        api_token: str,
        boards: list[str],
        update_interval: timedelta,
    ) -> None:
        """Initialize."""
        self.session = session
        self.api_key = api_key
        self.api_token = api_token
        self.board_ids = boards

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )

    async def _async_update_data(self) -> dict:
        """Fetch data from Trello."""
        try:
            return await self._fetch_data()
        except aiohttp.ClientResponseError as err:
            if err.status == 401:
                raise ConfigEntryAuthFailed("Authentication failed") from err
            raise UpdateFailed(f"Error communicating with Trello: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Error communicating with Trello: {err}") from err

    async def _fetch_data(self) -> dict:
        """Fetch data from Trello API."""
        _LOGGER.info("Starting Trello data fetch for %d monitored boards", len(self.board_ids))
        data = {"boards": {}, "all_boards": []}
        params = {"key": self.api_key, "token": self.api_token}

        # First, fetch all available boards for the account sensor
        try:
            async with async_timeout(15):
                boards_url = f"{TRELLO_API_BASE}/members/me/boards"
                boards_params = {**params, "filter": "all", "fields": "id,name,url,closed"}
                _LOGGER.debug("Fetching all boards from Trello account")
                async with self.session.get(boards_url, params=boards_params) as response:
                    if response.status == 200:
                        all_boards_data = await response.json()
                        _LOGGER.debug("Retrieved %d total boards from Trello", len(all_boards_data))
                        data["all_boards"] = [
                            {
                                "id": board["id"],
                                "name": board["name"],
                                "url": board.get("url", ""),
                                "closed": board.get("closed", False),
                            }
                            for board in all_boards_data
                        ]
                    else:
                        _LOGGER.warning("Failed to fetch all boards, status: %s", response.status)
        except (TimeoutError, asyncio.TimeoutError):
            _LOGGER.error("Timeout fetching all boards list")
        except Exception as err:
            _LOGGER.error("Error fetching all boards list: %s", err, exc_info=True)

        # Now fetch detailed data for selected boards
        for board_id in self.board_ids:
            try:
                async with async_timeout(30):
                    # Fetch board info
                    board_url = f"{TRELLO_API_BASE}/boards/{board_id}"
                    async with self.session.get(board_url, params=params) as response:
                        if response.status != 200:
                            _LOGGER.error("Error fetching board %s: status %s", board_id, response.status)
                            continue
                        board_data = await response.json()

                    # Fetch lists
                    lists_url = f"{TRELLO_API_BASE}/boards/{board_id}/lists"
                    async with self.session.get(lists_url, params=params) as response:
                        if response.status != 200:
                            _LOGGER.error("Error fetching lists for board %s: status %s", board_id, response.status)
                            continue
                        lists_data = await response.json()

                    board_info = {
                        "id": board_data["id"],
                        "name": board_data["name"],
                        "url": board_data.get("url", ""),
                        "closed": board_data.get("closed", False),
                        "lists": {},
                    }

                    # Fetch cards for each list
                    for trello_list in lists_data:
                        list_id = trello_list["id"]
                        
                        # Fetch cards for this list
                        cards_url = f"{TRELLO_API_BASE}/lists/{list_id}/cards"
                        cards_params = {
                            **params,
                            "fields": "id,name,url,closed,due,dueComplete,desc,labels,idMembers,badges",
                            "members": "true",
                            "member_fields": "fullName,username",
                        }
                        
                        async with self.session.get(cards_url, params=cards_params) as response:
                            if response.status != 200:
                                _LOGGER.warning("Error fetching cards for list %s: status %s", list_id, response.status)
                                cards_data = []
                            else:
                                cards_data = await response.json()

                        card_list = []
                        for card in cards_data:
                            card_info = {
                                "id": card["id"],
                                "name": card["name"],
                                "url": card.get("url", ""),
                                "closed": card.get("closed", False),
                                "due": card.get("due"),
                                "due_complete": card.get("dueComplete", False),
                                "description": card.get("desc", "")[:512],
                                "labels": [label["name"] for label in card.get("labels", []) if label.get("name")],
                                "members": [member.get("fullName", member.get("username", "Unknown")) 
                                           for member in card.get("members", [])],
                                "checklist_items": card.get("badges", {}).get("checkItems", 0),
                                "checklist_items_checked": card.get("badges", {}).get("checkItemsChecked", 0),
                                "attachments": card.get("badges", {}).get("attachments", 0),
                                "comments": card.get("badges", {}).get("comments", 0),
                            }
                            card_list.append(card_info)

                        board_info["lists"][list_id] = {
                            "id": list_id,
                            "name": trello_list["name"],
                            "closed": trello_list.get("closed", False),
                            "cards": card_list,
                            "card_count": len(card_list),
                        }

                    board_info["list_count"] = len([l for l in board_info["lists"].values() if not l["closed"]])
                    data["boards"][board_id] = board_info

            except TimeoutError:
                _LOGGER.error("Timeout fetching board %s", board_id)
                continue
            except Exception as err:
                _LOGGER.error("Error fetching board %s: %s", board_id, err)
                continue

        _LOGGER.info(
            "Trello data fetch complete: %d total boards in account, %d monitored boards with data",
            len(data.get("all_boards", [])),
            len(data.get("boards", {}))
        )
        return data
