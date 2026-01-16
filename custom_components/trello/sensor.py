"""Sensor platform for Trello integration."""
from __future__ import annotations

from datetime import datetime
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import TrelloDataUpdateCoordinator
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Trello sensors based on a config entry."""
    coordinator: TrelloDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []

    # Add account-level sensor showing all available boards
    entities.append(TrelloAccountSensor(coordinator, entry))

    # Create sensors for each board
    for board_id, board_data in coordinator.data.get("boards", {}).items():
        entities.append(TrelloBoardSensor(coordinator, entry, board_id))

        # Create sensors for each list in the board
        for list_id, list_data in board_data.get("lists", {}).items():
            entities.append(TrelloListSensor(coordinator, entry, board_id, list_id))

    async_add_entities(entities)


class TrelloAccountSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Trello Account sensor showing all available boards."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: TrelloDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry_id = entry.entry_id
        self._attr_unique_id = f"{entry.entry_id}_account"
        
        # Set up device to namespace entities per account
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "Trello",
            "model": "Trello Integration",
            "entry_type": "service",
        }

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Account Boards"

    @property
    def native_value(self) -> int:
        """Return the state of the sensor."""
        all_boards = self.coordinator.data.get("all_boards", [])
        return len([b for b in all_boards if not b.get("closed", False)])

    @property
    def native_unit_of_measurement(self) -> str:
        """Return the unit of measurement."""
        return "boards"

    @property
    def icon(self) -> str:
        """Return the icon for the sensor."""
        return "mdi:view-dashboard"

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional state attributes."""
        all_boards = self.coordinator.data.get("all_boards", [])
        monitored_board_ids = set(self.coordinator.board_ids)
        
        _LOGGER.debug(
            "Building account sensor attributes: %d boards from coordinator, %d monitored IDs",
            len(all_boards),
            len(monitored_board_ids)
        )
        
        # Build list of all boards with their status
        boards_list = []
        for board in all_boards:
            board_id = board["id"]
            is_monitored = board_id in monitored_board_ids
            
            board_info = {
                "id": board_id,
                "name": board["name"],
                "url": board.get("url", ""),
                "closed": board.get("closed", False),
                "monitored": is_monitored,
            }
            
            # Add detailed info for monitored boards
            if is_monitored and board_id in self.coordinator.data.get("boards", {}):
                detailed = self.coordinator.data["boards"][board_id]
                board_info.update({
                    "lists": detailed.get("list_count", 0),
                    "total_cards": sum(
                        list_data.get("card_count", 0)
                        for list_data in detailed.get("lists", {}).values()
                        if not list_data.get("closed", False)
                    ),
                })
            
            boards_list.append(board_info)
        
        # Sort by name
        boards_list.sort(key=lambda x: x["name"].lower())
        
        # Separate into open and closed
        open_boards = [b for b in boards_list if not b["closed"]]
        closed_boards = [b for b in boards_list if b["closed"]]
        
        attributes = {
            "all_boards": boards_list,
            "open_boards": open_boards,
            "closed_boards": closed_boards,
            "total_boards": len(all_boards),
            "total_open": len(open_boards),
            "total_closed": len(closed_boards),
            "total_monitored": len([b for b in boards_list if b["monitored"]]),
            "total_unmonitored": len([b for b in boards_list if not b["monitored"]]),
            "last_updated": datetime.now().isoformat(),
        }

        _LOGGER.debug(
            "Account sensor attributes: %d boards in all_boards, %d open, %d closed, %d monitored, %d unmonitored",
            len(boards_list),
            len(open_boards),
            len(closed_boards),
            attributes["total_monitored"],
            attributes["total_unmonitored"]
        )

        return attributes


class TrelloBoardSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Trello Board sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: TrelloDataUpdateCoordinator,
        entry: ConfigEntry,
        board_id: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._board_id = board_id
        self._entry_id = entry.entry_id
        self._attr_unique_id = f"{entry.entry_id}_{board_id}"
        
        # Set up device to namespace entities per account
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "Trello",
            "model": "Trello Integration",
            "entry_type": "service",
        }

    @property
    def board_data(self) -> dict:
        """Return the board data."""
        return self.coordinator.data.get("boards", {}).get(self._board_id, {})

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self.board_data.get("name", "Unknown Board")

    @property
    def native_value(self) -> int:
        """Return the state of the sensor."""
        return self.board_data.get("list_count", 0)

    @property
    def native_unit_of_measurement(self) -> str:
        """Return the unit of measurement."""
        return "lists"

    @property
    def icon(self) -> str:
        """Return the icon for the sensor."""
        return "mdi:trello"

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional state attributes."""
        board = self.board_data
        
        # Count total cards across all lists
        total_cards = sum(
            list_data.get("card_count", 0)
            for list_data in board.get("lists", {}).values()
            if not list_data.get("closed", False)
        )

        # Count cards with due dates
        overdue_cards = 0
        due_soon_cards = 0
        now = datetime.now()

        for list_data in board.get("lists", {}).values():
            for card in list_data.get("cards", []):
                if card.get("due") and not card.get("due_complete"):
                    due_date = datetime.fromisoformat(card["due"].replace("Z", "+00:00"))
                    if due_date < now:
                        overdue_cards += 1
                    elif (due_date - now).days <= 7:
                        due_soon_cards += 1

        attributes = {
            "board_id": board.get("id"),
            "board_url": board.get("url"),
            "closed": board.get("closed", False),
            "total_cards": total_cards,
            "overdue_cards": overdue_cards,
            "due_soon_cards": due_soon_cards,
            "last_updated": datetime.now().isoformat(),
            "lists": [
                {
                    "id": list_id,
                    "name": list_data.get("name"),
                    "card_count": list_data.get("card_count", 0),
                }
                for list_id, list_data in board.get("lists", {}).items()
                if not list_data.get("closed", False)
            ],
        }

        return attributes


class TrelloListSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Trello List sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: TrelloDataUpdateCoordinator,
        entry: ConfigEntry,
        board_id: str,
        list_id: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._board_id = board_id
        self._list_id = list_id
        self._attr_unique_id = f"{entry.entry_id}_{board_id}_{list_id}"
        
        # Set up device to namespace entities per account
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "Trello",
            "model": "Trello Integration",
            "entry_type": "service",
        }

    @property
    def board_data(self) -> dict:
        """Return the board data."""
        return self.coordinator.data.get("boards", {}).get(self._board_id, {})

    @property
    def list_data(self) -> dict:
        """Return the list data."""
        return self.board_data.get("lists", {}).get(self._list_id, {})

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        board_name = self.board_data.get("name", "Unknown")
        list_name = self.list_data.get("name", "Unknown List")
        return f"{board_name} - {list_name}"

    @property
    def native_value(self) -> int:
        """Return the state of the sensor."""
        return self.list_data.get("card_count", 0)

    @property
    def native_unit_of_measurement(self) -> str:
        """Return the unit of measurement."""
        return "cards"

    @property
    def icon(self) -> str:
        """Return the icon for the sensor."""
        return "mdi:format-list-bulleted"

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional state attributes."""
        list_data = self.list_data
        
        attributes = {
            "board_id": self._board_id,
            "board_name": self.board_data.get("name"),
            "list_id": list_data.get("id"),
            "closed": list_data.get("closed", False),
            "cards": list_data.get("cards", []),
            "last_updated": datetime.now().isoformat(),
        }

        return attributes
