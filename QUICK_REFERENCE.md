# Trello Integration - Quick Reference Card

## Installation
```bash
# Via HACS: Add custom repo
https://github.com/ianpleasance/home-assistant-trello

# Manual: Copy to
config/custom_components/trello/
```

## Setup
1. Get API key: https://trello.com/app-key
2. Generate token (same page)
3. Add integration in HA
4. Select boards & set interval (1-1440 min)

## Sensor Entities

### Board Sensor
`sensor.<board_name>_board`
- State: Number of lists
- Attributes: board_id, board_url, total_cards, overdue_cards, due_soon_cards, lists

### List Sensor
`sensor.<board_name>_<list_name>`
- State: Number of cards
- Attributes: board_id, board_name, list_id, cards[]

## Card Data
Each card includes:
- id, name, url, closed
- due, due_complete
- description (512 chars)
- labels[], members[]
- checklist_items, checklist_items_checked
- attachments, comments

## Common Templates

### Get card count
```yaml
{{ states('sensor.my_board_to_do') }}
```

### Access cards
```yaml
{% set cards = state_attr('sensor.my_board_to_do', 'cards') %}
```

### Filter by label
```yaml
{{ cards | selectattr('labels', 'search', 'Urgent') | list }}
```

### Count overdue
```yaml
{{ state_attr('sensor.my_board', 'overdue_cards') }}
```

## Quick Automations

### Overdue alert
```yaml
trigger:
  - platform: state
    entity_id: sensor.my_board
condition:
  - "{{ state_attr('sensor.my_board', 'overdue_cards') | int > 0 }}"
action:
  - service: notify.mobile_app
    data:
      message: "You have overdue tasks!"
```

### Card completed
```yaml
trigger:
  - platform: state
    entity_id: sensor.my_board_done
condition:
  - "{{ trigger.to_state.state | int > trigger.from_state.state | int }}"
action:
  - service: notify.mobile_app
    data:
      message: "Task completed! 🎉"
```

### Daily digest
```yaml
trigger:
  - platform: time
    at: "08:00:00"
action:
  - service: notify.mobile_app
    data:
      message: >
        To Do: {{ states('sensor.board_to_do') }}
        In Progress: {{ states('sensor.board_in_progress') }}
        Done: {{ states('sensor.board_done') }}
```

## Dashboard Cards

### Simple entity
```yaml
type: entity
entity: sensor.my_board_to_do
```

### Kanban view
```yaml
type: horizontal-stack
cards:
  - type: entity
    entity: sensor.board_to_do
  - type: entity
    entity: sensor.board_in_progress
  - type: entity
    entity: sensor.board_done
```

### Board overview
```yaml
type: entities
title: Board Status
entities:
  - entity: sensor.my_board
  - type: attribute
    entity: sensor.my_board
    attribute: total_cards
  - type: attribute
    entity: sensor.my_board
    attribute: overdue_cards
```

## Configuration

### Update interval
Settings → Devices & Services → Trello → Configure

### Multiple accounts
Add integration multiple times with different credentials

### Add more boards
Add integration again, can use same credentials

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Can't find integration | Restart HA, clear cache |
| Auth failed | Check API key/token, regenerate |
| No boards | Check boards exist and aren't archived |
| Not updating | Check interval, logs, API status |

## Limits
- Update interval: 1-1440 minutes
- API rate limit: 300 req/10 sec (generous)
- Description truncated: 512 chars
- Multiple accounts: Unlimited

## Links
- Docs: github.com/ianpleasance/home-assistant-trello
- Trello API: trello.com/app-key
- Issues: github.com/ianpleasance/home-assistant-trello/issues
- Examples: See EXAMPLES.md

## Entity ID Format
- Board: `sensor.<normalized_board_name>_board`
- List: `sensor.<normalized_board_name>_<normalized_list_name>`

Example:
- "My Project Board" → `sensor.my_project_board_board`
- "To Do" list → `sensor.my_project_board_to_do`
