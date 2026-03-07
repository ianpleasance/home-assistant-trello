# Home Assistant Trello Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

Monitor your Trello boards, lists, and cards directly in Home Assistant.

## Features

- **Multiple Account Support** — Add multiple Trello accounts, each as a separate integration instance
- **Board Selection** — Choose which boards to monitor via the UI config flow
- **Configurable Refresh** — Update intervals from 1 to 1440 minutes (default: 5 minutes)
- **Rich Sensors** — One sensor per board and one per list, with full card detail attributes
- **Due Date Tracking** — Overdue and due-soon card counts per board
- **No Dependencies** — Uses Home Assistant's built-in aiohttp client; no external Python libraries required

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click **Integrations** → three dots (top right) → **Custom repositories**
3. Add `https://github.com/ianpleasance/home-assistant-trello` as an Integration
4. Search for "Trello" in HACS and click **Download**
5. Restart Home Assistant

### Manual

1. Copy the `custom_components/trello` directory into your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant

## Getting API Credentials

1. Go to [https://trello.com/app-key](https://trello.com/app-key)
2. Copy your **API Key**
3. Click the **Token** link on the same page, authorise the app, and copy the **Token**

Keep these credentials secure — anyone with them can access your Trello boards.

## Configuration

1. Go to **Settings** → **Devices & Services** → **+ Add Integration**
2. Search for "Trello" and enter your API Key and Token
3. Select the boards you want to monitor
4. Set your preferred update interval (optional, default 5 minutes)

To change the update interval later: **Settings** → **Devices & Services** → **Trello** → **Configure**.

### Multiple Accounts

Add the integration multiple times with different credentials. Each account gets its own device named `Trello (username)` so entities are namespaced and won't conflict even if board names are identical across accounts.

## Sensors

### Account Sensor

**Entity:** `sensor.<account_name>_account_boards`  
**State:** Number of open boards in the account

| Attribute | Description |
|-----------|-------------|
| `all_boards` | All boards (open and closed) with id, name, url, closed, monitored flags |
| `open_boards` | Open boards only |
| `closed_boards` | Archived boards |
| `total_boards` | Total board count |
| `total_open` | Open board count |
| `total_closed` | Closed board count |
| `total_monitored` | Boards being actively monitored |
| `total_unmonitored` | Boards not selected for monitoring |
| `last_updated` | Timestamp of last data fetch |

### Board Sensors

**Entity:** `sensor.<board_name>_board`  
**State:** Number of active lists in the board

| Attribute | Description |
|-----------|-------------|
| `board_id` | Trello board ID |
| `board_url` | Direct link to the board |
| `closed` | Whether the board is archived |
| `total_cards` | Total open cards across all lists |
| `overdue_cards` | Cards with past due dates (not marked complete) |
| `due_soon_cards` | Cards due within the next 7 days |
| `lists` | Array of lists — id, name, card_count |
| `last_updated` | Timestamp of last data fetch |

### List Sensors

**Entity:** `sensor.<board_name>_<list_name>`  
**State:** Number of open cards in the list

| Attribute | Description |
|-----------|-------------|
| `board_id` | Parent board ID |
| `board_name` | Parent board name |
| `list_id` | Trello list ID |
| `closed` | Whether the list is archived |
| `cards` | Array of card objects (see below) |
| `last_updated` | Timestamp of last data fetch |

### Card Data

Each entry in `cards` includes:

| Field | Description |
|-------|-------------|
| `id` | Trello card ID |
| `name` | Card title |
| `url` | Direct link to the card |
| `closed` | Whether the card is archived |
| `due` | Due date |
| `due_complete` | Whether the due date is marked complete |
| `description` | First 512 characters of the card description |
| `labels` | Array of label names |
| `members` | Array of assigned member names |
| `checklist_items` | Total checklist items |
| `checklist_items_checked` | Completed checklist items |
| `attachments` | Number of attachments |
| `comments` | Number of comments |

## Services

### `trello.refresh`

Force an immediate data refresh, bypassing the normal update interval.

**Refresh all Trello integrations:**
```yaml
service: trello.refresh
```

**Refresh a specific integration:**
```yaml
service: trello.refresh
data:
  config_entry_id: "abc123def456"
```

**Dashboard button:**
```yaml
type: button
name: Refresh Trello
icon: mdi:refresh
tap_action:
  action: call-service
  service: trello.refresh
```

Each refresh makes approximately `1 + boards + lists + lists` API requests. Trello allows 300 requests per 10 seconds, so even frequent manual refreshes are well within limits.

## Automations

### Notify on overdue cards

```yaml
automation:
  - alias: "Trello - Overdue Cards Alert"
    trigger:
      - platform: state
        entity_id: sensor.my_board
    condition:
      - condition: template
        value_template: "{{ state_attr('sensor.my_board', 'overdue_cards') | int > 0 }}"
    action:
      - service: notify.mobile_app_iphone
        data:
          title: "Overdue Trello Cards"
          message: "You have {{ state_attr('sensor.my_board', 'overdue_cards') }} overdue cards!"
```

### Morning task digest

```yaml
automation:
  - alias: "Trello - Morning Digest"
    trigger:
      - platform: time
        at: "08:00:00"
    action:
      - service: notify.mobile_app_iphone
        data:
          title: "Today's Tasks"
          message: >
            To Do: {{ states('sensor.my_board_to_do') }}
            In Progress: {{ states('sensor.my_board_in_progress') }}
            Overdue: {{ state_attr('sensor.my_board', 'overdue_cards') }}
```

### Alert when a card moves to Done

```yaml
automation:
  - alias: "Trello - Card Completed"
    trigger:
      - platform: state
        entity_id: sensor.my_board_done
    condition:
      - condition: template
        value_template: "{{ trigger.to_state.state | int > trigger.from_state.state | int }}"
    action:
      - service: notify.mobile_app_iphone
        data:
          message: "Task completed on {{ state_attr('sensor.my_board_done', 'board_name') }}!"
```

### Due-soon reminder

```yaml
automation:
  - alias: "Trello - Due Soon Reminder"
    trigger:
      - platform: time
        at: "09:00:00"
    condition:
      - condition: template
        value_template: "{{ state_attr('sensor.my_board', 'due_soon_cards') | int > 0 }}"
    action:
      - service: notify.mobile_app_iphone
        data:
          title: "Cards Due Soon"
          message: "{{ state_attr('sensor.my_board', 'due_soon_cards') }} card(s) due within 7 days."
```

### Alert when a list gets too full

```yaml
automation:
  - alias: "Trello - List Capacity Warning"
    trigger:
      - platform: numeric_state
        entity_id: sensor.my_board_to_do
        above: 20
    action:
      - service: notify.mobile_app_iphone
        data:
          message: "To Do list has {{ states('sensor.my_board_to_do') }} cards — consider prioritising."
```

### Weekly summary (Friday evening)

```yaml
automation:
  - alias: "Trello - Weekly Summary"
    trigger:
      - platform: time
        at: "18:00:00"
    condition:
      - condition: time
        weekday: fri
    action:
      - service: notify.mobile_app_iphone
        data:
          title: "Weekly Trello Summary"
          message: >
            Total cards: {{ state_attr('sensor.my_board', 'total_cards') }}
            Overdue: {{ state_attr('sensor.my_board', 'overdue_cards') }}
            Due soon: {{ state_attr('sensor.my_board', 'due_soon_cards') }}
```

## Template Sensors

### Sprint completion percentage

```yaml
template:
  - sensor:
      - name: "Sprint Completion"
        unit_of_measurement: "%"
        state: >
          {% set total = states('sensor.sprint_to_do') | int +
                         states('sensor.sprint_in_progress') | int +
                         states('sensor.sprint_done') | int %}
          {% set done = states('sensor.sprint_done') | int %}
          {{ ((done / total) * 100) | round(1) if total > 0 else 0 }}
```

### Count cards by label

```yaml
template:
  - sensor:
      - name: "Urgent Tasks"
        state: >
          {% set cards = state_attr('sensor.my_board_to_do', 'cards') %}
          {{ (cards | selectattr('labels', 'search', 'Urgent') | list | length) if cards else 0 }}
```

### Unmonitored board count

```yaml
template:
  - sensor:
      - name: "Unmonitored Trello Boards"
        state: >
          {% set all_boards = state_attr('sensor.trello_account_boards', 'all_boards') %}
          {{ (all_boards | selectattr('monitored', 'eq', false) | list | length) if all_boards else 0 }}
```

## Dashboards

### Kanban column counts

```yaml
type: horizontal-stack
cards:
  - type: entity
    entity: sensor.my_board_to_do
    name: To Do
    icon: mdi:clipboard-list-outline
  - type: entity
    entity: sensor.my_board_in_progress
    name: In Progress
    icon: mdi:progress-clock
  - type: entity
    entity: sensor.my_board_done
    name: Done
    icon: mdi:check-circle
```

### Board status overview

```yaml
type: entities
title: Board Status
entities:
  - entity: sensor.my_board
    name: Active Lists
  - type: attribute
    entity: sensor.my_board
    attribute: total_cards
    name: Total Cards
  - type: attribute
    entity: sensor.my_board
    attribute: overdue_cards
    name: Overdue
  - type: attribute
    entity: sensor.my_board
    attribute: due_soon_cards
    name: Due This Week
```

### All boards summary

```yaml
type: markdown
content: |
  {% set boards = state_attr('sensor.trello_account_boards', 'open_boards') %}
  {% for board in boards | sort(attribute='name') %}
  **[{{ board.name }}]({{ board.url }})** {% if board.monitored %}— {{ board.total_cards }} cards{% endif %}
  {% endfor %}
```

## Troubleshooting

**Integration not appearing** — Restart Home Assistant and clear browser cache. Verify files are in `config/custom_components/trello/`.

**Authentication failed** — Ensure you copied the full API key and token with no extra spaces. Regenerate the token at [https://trello.com/app-key](https://trello.com/app-key).

**No boards available** — Verify you have open (non-archived) boards in your Trello account and that the token has board access.

**Sensors not updating** — Check the update interval in **Configure**, look for errors in **Settings** → **System** → **Logs**, and verify Trello is accessible.

**Cards missing data** — Not all cards have all attributes set (e.g. no due date, no members). Empty values are normal.

## API Rate Limits

Trello allows 300 requests per 10 seconds per token. This integration makes requests only at the configured interval and is well within limits for any typical board setup.

## Contributing

Issues and pull requests welcome at [https://github.com/ianpleasance/home-assistant-trello](https://github.com/ianpleasance/home-assistant-trello).

## License

Apache 2.0 — see [LICENSE](LICENSE)
