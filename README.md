# Home Assistant Trello Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

A Home Assistant custom integration for monitoring Trello boards, lists, and cards.

## Features

- **Multiple Account Support**: Add multiple Trello accounts, each as a separate integration instance
- **Configurable Refresh**: Set update intervals from 1 to 1440 minutes (default: 5 minutes)
- **Board Selection**: Choose which boards to monitor via the UI
- **Comprehensive Data**: Track boards, lists, cards, due dates, labels, members, checklists, and more
- **Rich Sensors**: One sensor per board and one per list, with detailed attributes

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add `https://github.com/ianpleasance/home-assistant-trello` as an Integration
6. Click "Install"
7. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/trello` directory to your Home Assistant `custom_components` directory
2. Restart Home Assistant

## Configuration

### Getting Trello API Credentials

1. Go to https://trello.com/app-key
2. Copy your **API Key**
3. Click the "Token" link (or generate manually)
4. Authorize the application and copy your **Token**

### Adding the Integration

1. In Home Assistant, go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "Trello"
4. Enter your API Key and Token
5. Select the boards you want to monitor
6. Set your preferred update interval (optional, defaults to 5 minutes)

### Multiple Accounts

To add multiple Trello accounts, simply add the integration again with different credentials. Each account will be a separate instance.

**Important:** The integration automatically handles board name conflicts between accounts. Each account instance:
- Gets a unique device in Home Assistant named "Trello (username)"
- Has its own namespace for entities
- Won't conflict with boards of the same name in other accounts

For example, if both Account A and Account B have a board named "Work Projects":
- Account A: `sensor.trello_username_a_work_projects_board`
- Account B: `sensor.trello_username_b_work_projects_board`

All entities are grouped under their respective account device for easy management.

## Sensors

### Account Sensor

Each Trello account integration creates one account-level sensor:

**Entity:** `sensor.<account_name>_account_boards`

- **State**: Number of open boards in the account
- **Attributes**:
  - `all_boards`: Complete list of all boards (open and closed)
  - `open_boards`: List of open boards only
  - `closed_boards`: List of closed/archived boards
  - `total_boards`: Total count of all boards
  - `total_open`: Count of open boards
  - `total_closed`: Count of closed boards
  - `total_monitored`: Count of boards being actively monitored
  - `total_unmonitored`: Count of boards not selected for monitoring

Each board in the lists includes:
- `id`: Trello board ID
- `name`: Board name
- `url`: Direct link to board
- `closed`: Whether board is archived
- `monitored`: Whether this integration is monitoring this board
- `lists`: Number of lists (only for monitored boards)
- `total_cards`: Total card count (only for monitored boards)

### Board Sensors

Each board creates a sensor with:
- **State**: Number of active lists
- **Attributes**:
  - `board_id`: Trello board ID
  - `board_url`: Direct link to the board
  - `closed`: Whether the board is archived
  - `total_cards`: Total number of cards across all lists
  - `overdue_cards`: Number of cards with overdue dates
  - `due_soon_cards`: Number of cards due within 7 days
  - `lists`: Array of lists with ID, name, and card count

### List Sensors

Each list creates a sensor with:
- **State**: Number of cards in the list
- **Attributes**:
  - `board_id`: Parent board ID
  - `board_name`: Parent board name
  - `list_id`: Trello list ID
  - `closed`: Whether the list is archived
  - `cards`: Array of card objects (see below)

### Card Data

Each card in the `cards` array includes:
- `id`: Trello card ID
- `name`: Card title
- `url`: Direct link to the card
- `closed`: Whether the card is archived
- `due`: Due date (ISO format)
- `due_complete`: Whether the due date is marked complete
- `description`: First 512 characters of the card description
- `labels`: Array of label names
- `members`: Array of member names assigned to the card
- `checklist_items`: Total number of checklist items
- `checklist_items_checked`: Number of completed checklist items
- `attachments`: Number of attachments
- `comments`: Number of comments

## Example Automations

### Show All Available Boards

```yaml
automation:
  - alias: "Trello - List All Boards"
    trigger:
      - platform: state
        entity_id: sensor.trello_john_doe_account_boards
    action:
      - service: notify.mobile_app
        data:
          title: "Trello Boards Summary"
          message: >
            You have {{ states('sensor.trello_john_doe_account_boards') }} open boards.
            Monitored: {{ state_attr('sensor.trello_john_doe_account_boards', 'total_monitored') }}
            Unmonitored: {{ state_attr('sensor.trello_john_doe_account_boards', 'total_unmonitored') }}
```

### List Unmonitored Boards

```yaml
template:
  - sensor:
      - name: "Unmonitored Trello Boards"
        state: >
          {% set all_boards = state_attr('sensor.trello_john_doe_account_boards', 'all_boards') %}
          {% if all_boards %}
            {{ all_boards | selectattr('monitored', 'eq', false) | list | length }}
          {% else %}
            0
          {% endif %}
        attributes:
          board_names: >
            {% set all_boards = state_attr('sensor.trello_john_doe_account_boards', 'all_boards') %}
            {% if all_boards %}
              {{ all_boards | selectattr('monitored', 'eq', false) | map(attribute='name') | list }}
            {% else %}
              []
            {% endif %}
```

### Notify on Overdue Cards

```yaml
automation:
  - alias: "Trello Overdue Cards Alert"
    trigger:
      - platform: state
        entity_id: sensor.my_board
    condition:
      - condition: template
        value_template: "{{ state_attr('sensor.my_board', 'overdue_cards') | int > 0 }}"
    action:
      - service: notify.mobile_app
        data:
          title: "Overdue Trello Cards"
          message: "You have {{ state_attr('sensor.my_board', 'overdue_cards') }} overdue cards!"
```

### Dashboard Card Count

```yaml
type: entity
entity: sensor.my_board_to_do
name: Tasks To Do
icon: mdi:format-list-checks
```

### Track List Movement

```yaml
automation:
  - alias: "Trello Card Moved to Done"
    trigger:
      - platform: state
        entity_id: sensor.my_board_done
    condition:
      - condition: template
        value_template: "{{ trigger.to_state.state | int > trigger.from_state.state | int }}"
    action:
      - service: notify.mobile_app
        data:
          message: "New card completed in {{ state_attr('sensor.my_board_done', 'board_name') }}!"
```

## Options

After installation, you can modify the update interval:

1. Go to **Settings** → **Devices & Services**
2. Find the Trello integration
3. Click **Configure**
4. Adjust the update interval

## API Rate Limits

Trello's API allows 300 requests per 10 seconds per token. This integration makes API calls directly to Trello's REST API using Home Assistant's built-in aiohttp client (no external dependencies). With one request per board per refresh cycle, even aggressive polling is well within rate limits for typical usage.

## Troubleshooting

### Authentication Errors

- Verify your API key and token are correct
- Ensure the token hasn't expired
- Try regenerating the token at https://trello.com/app-key

### No Boards Available

- Check that you have boards in your Trello account
- Ensure the boards aren't archived
- Verify the API credentials have access to your boards

### Sensors Not Updating

- Check the update interval in the integration options
- Look for errors in Home Assistant logs: **Settings** → **System** → **Logs**
- Verify your Trello account is accessible

## Contributing

Issues and pull requests are welcome at https://github.com/ianpleasance/home-assistant-trello

## License

MIT License

## Author

Ian Pleasance ([@ianpleasance](https://github.com/ianpleasance))

## Technical Notes

This integration uses Home Assistant's built-in aiohttp client to communicate directly with the Trello REST API. No external Python libraries are required.
