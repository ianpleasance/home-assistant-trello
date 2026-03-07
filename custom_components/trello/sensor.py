"""Sensor platform for Trello integration."""
from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

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
    entities.append(TrelloAccountSensor(coordinator, entry))

    for board_id, board_data in coordinator.data.get("boards", {}).items():
        entities.append(TrelloBoardSensor(coordinator, entry, board_id))
        for list_id in board_data.get("lists", {}).keys():
            entities.append(TrelloListSensor(coordinator, entry, board_id, list_id))

    async_add_entities(entities)


def _make_device_info(entry: ConfigEntry) -> DeviceInfo:
    """Return shared DeviceInfo for all sensors in this config entry."""
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.title,
        manufacturer="Trello",
        model="Trello Integration",
        entry_type=DeviceEntryType.SERVICE,
    )


class TrelloAccountSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Trello Account sensor showing all available boards."""

    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:view-dashboard"
    _attr_native_unit_of_measurement = "boards"

    def __init__(
        self,
        coordinator: TrelloDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry_id = entry.entry_id
        self._attr_unique_id = f"{entry.entry_id}_account"
        self._attr_device_info = _make_device_info(entry)

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
    def extra_state_attributes(self) -> dict:
        """Return additional state attributes."""
        all_boards = self.coordinator.data.get("all_boards", [])
        monitored_board_ids = set(self.coordinator.board_ids)

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

        boards_list.sort(key=lambda x: x["name"].lower())
        open_boards = [b for b in boards_list if not b["closed"]]
        closed_boards = [b for b in boards_list if b["closed"]]

        return {
            "all_boards": boards_list,
            "open_boards": open_boards,
            "closed_boards": closed_boards,
            "total_boards": len(all_boards),
            "total_open": len(open_boards),
            "total_closed": len(closed_boards),
            "total_monitored": len([b for b in boards_list if b["monitored"]]),
            "total_unmonitored": len([b for b in boards_list if not b["monitored"]]),
            "last_updated": dt_util.now(),
        }


class TrelloBoardSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Trello Board sensor."""

    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:trello"
    _attr_native_unit_of_measurement = "lists"

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
        self._attr_device_info = _make_device_info(entry)

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
    def extra_state_attributes(self) -> dict:
        """Return additional state attributes."""
        board = self.board_data
        now = dt_util.now()

        total_cards = 0
        overdue_cards = 0
        due_soon_cards = 0

        for list_data in board.get("lists", {}).values():
            if list_data.get("closed", False):
                continue
            open_cards = [c for c in list_data.get("cards", []) if not c.get("closed", False)]
            total_cards += len(open_cards)

            for card in open_cards:
                if card.get("due") and not card.get("due_complete"):
                    try:
                        due_date = dt_util.parse_datetime(card["due"])
                        if due_date is not None:
                            if due_date < now:
                                overdue_cards += 1
                            elif (due_date - now).total_seconds() <= 7 * 86400:
                                due_soon_cards += 1
                    except (ValueError, TypeError):
                        pass

        return {
            "board_id": board.get("id"),
            "board_url": board.get("url"),
            "closed": board.get("closed", False),
            "total_cards": total_cards,
            "overdue_cards": overdue_cards,
            "due_soon_cards": due_soon_cards,
            "lists": [
                {
                    "id": list_id,
                    "name": list_data.get("name"),
                    "card_count": len([
                        c for c in list_data.get("cards", [])
                        if not c.get("closed", False)
                    ]),
                }
                for list_id, list_data in board.get("lists", {}).items()
                if not list_data.get("closed", False)
            ],
            "last_updated": dt_util.now(),
        }


class TrelloListSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Trello List sensor."""

    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:format-list-bulleted"
    _attr_native_unit_of_measurement = "cards"

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
        self._attr_device_info = _make_device_info(entry)

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
        """Return the state of the sensor (open cards only)."""
        return len([c for c in self.list_data.get("cards", []) if not c.get("closed", False)])

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional state attributes."""
        list_data = self.list_data
        open_cards = [c for c in list_data.get("cards", []) if not c.get("closed", False)]

        return {
            "board_id": self._board_id,
            "board_name": self.board_data.get("name"),
            "list_id": list_data.get("id"),
            "closed": list_data.get("closed", False),
            "cards": open_cards,
            "last_updated": dt_util.now(),
        }
