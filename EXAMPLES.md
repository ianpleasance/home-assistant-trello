# Example Trello Automations

This file contains example automations to help you get started with the Trello integration.

## Account-Level Examples

### 1. Display All Available Boards

```yaml
type: markdown
title: My Trello Boards
content: |
  {% set all_boards = state_attr('sensor.trello_account_boards', 'all_boards') %}
  {% if all_boards %}
  **Total Boards:** {{ all_boards | length }}
  **Open:** {{ all_boards | selectattr('closed', 'eq', false) | list | length }}
  **Monitored:** {{ all_boards | selectattr('monitored', 'eq', true) | list | length }}
  
  ### Open Boards:
  {% for board in all_boards | selectattr('closed', 'eq', false) | sort(attribute='name') %}
  - [{{ board.name }}]({{ board.url }}) {% if board.monitored %}✓{% endif %}
  {% endfor %}
  {% endif %}
```

### 2. Track Unmonitored Boards

```yaml
automation:
  - alias: "Trello - New Board Created"
    description: "Notify when a new board appears in the account"
    trigger:
      - platform: state
        entity_id: sensor.trello_account_boards
    condition:
      - condition: template
        value_template: >
          {{ trigger.to_state.state | int > trigger.from_state.state | int }}
    action:
      - service: notify.mobile_app
        data:
          title: "📋 New Trello Board Detected"
          message: >
            You now have {{ states('sensor.trello_account_boards') }} boards in your Trello account!
```

### 3. List Board Status

```yaml
template:
  - sensor:
      - name: "Trello Board Summary"
        state: "{{ state_attr('sensor.trello_account_boards', 'total_open') }}"
        unit_of_measurement: "boards"
        attributes:
          monitored: "{{ state_attr('sensor.trello_account_boards', 'total_monitored') }}"
          unmonitored: "{{ state_attr('sensor.trello_account_boards', 'total_unmonitored') }}"
          closed: "{{ state_attr('sensor.trello_account_boards', 'total_closed') }}"
          board_names: >
            {% set boards = state_attr('sensor.trello_account_boards', 'open_boards') %}
            {{ boards | map(attribute='name') | list if boards else [] }}
```

## Basic Examples

### 1. Notification When Cards Become Overdue

```yaml
automation:
  - alias: "Trello - Overdue Cards Alert"
    description: "Send notification when cards become overdue"
    trigger:
      - platform: state
        entity_id: sensor.work_projects_board
    condition:
      - condition: template
        value_template: "{{ state_attr('sensor.work_projects_board', 'overdue_cards') | int > 0 }}"
    action:
      - service: notify.mobile_app_iphone
        data:
          title: "⚠️ Overdue Trello Cards"
          message: >
            You have {{ state_attr('sensor.work_projects_board', 'overdue_cards') }} 
            overdue card(s) on {{ state_attr('sensor.work_projects_board', 'board_name') }}
```

### 2. Celebrate Completed Tasks

```yaml
automation:
  - alias: "Trello - Task Completed Celebration"
    description: "Celebrate when a card moves to Done"
    trigger:
      - platform: state
        entity_id: sensor.personal_tasks_done
    condition:
      - condition: template
        value_template: >
          {{ trigger.to_state.state | int > trigger.from_state.state | int }}
    action:
      - service: script.celebrate_completion
      - service: notify.family
        data:
          message: "🎉 Task completed! You're making progress!"
```

### 3. Daily Digest of Pending Tasks

```yaml
automation:
  - alias: "Trello - Morning Task Digest"
    description: "Send a summary of pending tasks each morning"
    trigger:
      - platform: time
        at: "08:00:00"
    action:
      - service: notify.mobile_app_iphone
        data:
          title: "📋 Today's Tasks"
          message: >
            To Do: {{ states('sensor.my_board_to_do') }} cards
            In Progress: {{ states('sensor.my_board_in_progress') }} cards
            Overdue: {{ state_attr('sensor.my_board', 'overdue_cards') }} cards
```

### 4. Alert When List Gets Too Full

```yaml
automation:
  - alias: "Trello - List Capacity Warning"
    description: "Warn when a list has too many cards"
    trigger:
      - platform: numeric_state
        entity_id: sensor.sprint_backlog_to_do
        above: 20
    action:
      - service: notify.team_slack
        data:
          message: >
            ⚠️ The "To Do" list has {{ states('sensor.sprint_backlog_to_do') }} cards.
            Consider prioritizing or moving items to the backlog!
```

### 5. Due Date Reminders (7 Days Before)

```yaml
automation:
  - alias: "Trello - Due Soon Reminder"
    description: "Remind about cards due within a week"
    trigger:
      - platform: time
        at: "09:00:00"
    condition:
      - condition: template
        value_template: "{{ state_attr('sensor.project_alpha', 'due_soon_cards') | int > 0 }}"
    action:
      - service: notify.mobile_app_iphone
        data:
          title: "⏰ Cards Due Soon"
          message: >
            {{ state_attr('sensor.project_alpha', 'due_soon_cards') }} card(s) 
            due within the next 7 days on Project Alpha
```

## Advanced Examples

### 6. Log Card Movements to Spreadsheet

```yaml
automation:
  - alias: "Trello - Log Card Movements"
    description: "Track when cards move between lists"
    trigger:
      - platform: state
        entity_id: 
          - sensor.my_board_to_do
          - sensor.my_board_in_progress
          - sensor.my_board_done
    action:
      - service: google_sheets.append_sheet
        data:
          spreadsheet_id: "your_spreadsheet_id"
          worksheet_id: "Sheet1"
          data:
            - - "{{ now().strftime('%Y-%m-%d %H:%M:%S') }}"
              - "{{ trigger.to_state.attributes.list_name }}"
              - "{{ trigger.to_state.state }}"
```

### 7. Weekly Board Summary Report

```yaml
automation:
  - alias: "Trello - Weekly Board Summary"
    description: "Send detailed weekly summary of all boards"
    trigger:
      - platform: time
        at: "18:00:00"
    condition:
      - condition: time
        weekday: fri
    action:
      - service: notify.email
        data:
          title: "📊 Weekly Trello Summary"
          message: >
            # Board Status Report
            
            ## Work Projects
            - Total Cards: {{ state_attr('sensor.work_projects_board', 'total_cards') }}
            - Overdue: {{ state_attr('sensor.work_projects_board', 'overdue_cards') }}
            - Due Soon: {{ state_attr('sensor.work_projects_board', 'due_soon_cards') }}
            
            ## Personal Tasks
            - Total Cards: {{ state_attr('sensor.personal_tasks', 'total_cards') }}
            - Overdue: {{ state_attr('sensor.personal_tasks', 'overdue_cards') }}
```

### 8. Smart Lights Based on Overdue Tasks

```yaml
automation:
  - alias: "Trello - Overdue Task Indicator Light"
    description: "Change office light color based on overdue tasks"
    trigger:
      - platform: state
        entity_id: sensor.work_board
      - platform: time_pattern
        hours: "/1"  # Check hourly
    action:
      - choose:
          - conditions:
              - condition: template
                value_template: "{{ state_attr('sensor.work_board', 'overdue_cards') | int > 5 }}"
            sequence:
              - service: light.turn_on
                target:
                  entity_id: light.office_lamp
                data:
                  color_name: red
                  brightness: 255
          - conditions:
              - condition: template
                value_template: "{{ state_attr('sensor.work_board', 'overdue_cards') | int > 0 }}"
            sequence:
              - service: light.turn_on
                target:
                  entity_id: light.office_lamp
                data:
                  color_name: orange
                  brightness: 200
        default:
          - service: light.turn_on
            target:
              entity_id: light.office_lamp
            data:
              color_name: green
              brightness: 150
```

### 9. Create Counter for Cards Completed This Month

```yaml
counter:
  trello_cards_completed_this_month:
    name: Cards Completed This Month
    icon: mdi:checkbox-marked-circle-outline

automation:
  - alias: "Trello - Count Completed Cards"
    description: "Increment counter when cards are marked done"
    trigger:
      - platform: state
        entity_id: sensor.my_board_done
    condition:
      - condition: template
        value_template: >
          {{ trigger.to_state.state | int > trigger.from_state.state | int }}
    action:
      - service: counter.increment
        target:
          entity_id: counter.trello_cards_completed_this_month
  
  - alias: "Trello - Reset Monthly Counter"
    description: "Reset the counter on the first of each month"
    trigger:
      - platform: time
        at: "00:00:00"
    condition:
      - condition: template
        value_template: "{{ now().day == 1 }}"
    action:
      - service: counter.reset
        target:
          entity_id: counter.trello_cards_completed_this_month
```

### 10. Notify When Specific Label is Added

```yaml
automation:
  - alias: "Trello - High Priority Label Alert"
    description: "Alert when a card gets the 'urgent' label"
    trigger:
      - platform: state
        entity_id: sensor.my_board_to_do
    condition:
      - condition: template
        value_template: >
          {% set cards = state_attr('sensor.my_board_to_do', 'cards') %}
          {% if cards %}
            {{ cards | selectattr('labels', 'search', 'urgent') | list | length > 0 }}
          {% else %}
            false
          {% endif %}
    action:
      - service: notify.priority_alert
        data:
          title: "🚨 Urgent Task Added"
          message: "A new urgent task has been added to your Trello board!"
```

## Dashboard Examples

### Simple Card Count Cards

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

### Board Overview Card

```yaml
type: entities
title: Project Board Status
entities:
  - entity: sensor.project_alpha
    name: Total Lists
  - type: attribute
    entity: sensor.project_alpha
    attribute: total_cards
    name: Total Cards
  - type: attribute
    entity: sensor.project_alpha
    attribute: overdue_cards
    name: Overdue
  - type: attribute
    entity: sensor.project_alpha
    attribute: due_soon_cards
    name: Due This Week
```

### Progress Bar Using Bar Card (requires custom card)

```yaml
type: custom:bar-card
entities:
  - entity: sensor.sprint_to_do
    name: To Do
  - entity: sensor.sprint_in_progress
    name: In Progress
  - entity: sensor.sprint_done
    name: Done
title: Sprint Progress
max: 50
height: 40px
```

## Script Examples

### Script to Log Specific Card Details

```yaml
script:
  log_trello_card_details:
    alias: "Log Trello Card Details"
    sequence:
      - service: logbook.log
        data:
          name: Trello
          message: >
            {% set cards = state_attr('sensor.my_board_to_do', 'cards') %}
            {% if cards %}
              {% for card in cards %}
                Card: {{ card.name }}
                Due: {{ card.due | default('No due date') }}
                Members: {{ card.members | join(', ') | default('Unassigned') }}
                ---
              {% endfor %}
            {% endif %}
```

## Template Sensor Examples

### Calculate Completion Percentage

```yaml
template:
  - sensor:
      - name: "Sprint Completion Percentage"
        unit_of_measurement: "%"
        state: >
          {% set total = states('sensor.sprint_to_do') | int + 
                        states('sensor.sprint_in_progress') | int + 
                        states('sensor.sprint_done') | int %}
          {% set done = states('sensor.sprint_done') | int %}
          {% if total > 0 %}
            {{ ((done / total) * 100) | round(1) }}
          {% else %}
            0
          {% endif %}
```

### Count Cards by Label

```yaml
template:
  - sensor:
      - name: "Urgent Tasks Count"
        state: >
          {% set cards = state_attr('sensor.work_board_to_do', 'cards') %}
          {% if cards %}
            {{ cards | selectattr('labels', 'search', 'urgent') | list | length }}
          {% else %}
            0
          {% endif %}
```

## Tips

1. Use `trigger.from_state` and `trigger.to_state` to detect changes
2. Access card details via `state_attr('sensor.board_list', 'cards')`
3. Filter cards by label: `cards | selectattr('labels', 'search', 'label_name')`
4. Check for overdue: `card.due and not card.due_complete`
5. Use templates to process card arrays for complex logic

For more examples and documentation, visit:
https://github.com/ianpleasance/home-assistant-trello
