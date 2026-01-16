# Trello Integration Setup Guide

Complete guide to installing and configuring the Home Assistant Trello integration.

## Prerequisites

- Home Assistant (version 2024.1.0 or later)
- HACS (Home Assistant Community Store) installed (recommended)
- Trello account with API access

## Step 1: Get Trello API Credentials

### 1.1 Get Your API Key

1. Log in to your Trello account
2. Navigate to https://trello.com/app-key
3. You'll see your API Key displayed at the top
4. **Copy and save this key** - you'll need it during setup

### 1.2 Generate an API Token

1. On the same page (https://trello.com/app-key), find the "Token" section
2. Click the "Token" link or the "generate a Token" link
3. You'll be asked to authorize the application
4. Click "Allow" to grant access
5. **Copy and save the token** - this is only shown once!

**Important:** Keep your API key and token secure. Anyone with these credentials can access your Trello boards.

## Step 2: Installation

### Option A: Install via HACS (Recommended)

1. Open Home Assistant
2. Go to **HACS** → **Integrations**
3. Click the **three dots** in the top right corner
4. Select **Custom repositories**
5. Add the repository:
   - **URL:** `https://github.com/ianpleasance/home-assistant-trello`
   - **Category:** Integration
6. Click **Add**
7. Search for "Trello" in HACS
8. Click **Download**
9. **Restart Home Assistant**

### Option B: Manual Installation

1. Download the latest release from GitHub
2. Extract the `custom_components/trello` folder
3. Copy it to your Home Assistant `config/custom_components/` directory
   ```
   config/
   └── custom_components/
       └── trello/
           ├── __init__.py
           ├── config_flow.py
           ├── const.py
           ├── manifest.json
           ├── sensor.py
           ├── strings.json
           └── translations/
               └── en.json
   ```
4. **Restart Home Assistant**

## Step 3: Configure the Integration

### 3.1 Add the Integration

1. In Home Assistant, go to **Settings** → **Devices & Services**
2. Click **+ Add Integration** (bottom right)
3. Search for "Trello"
4. Click on "Trello" when it appears

### 3.2 Enter Credentials

You'll see a form asking for:

- **API Key:** Paste the API key you copied from Trello
- **API Token:** Paste the token you generated

Click **Submit**

### 3.3 Select Boards

After authentication, you'll see a list of all your Trello boards:

1. **Select the boards** you want to monitor (you can select multiple)
2. **Set the Update Interval** (in minutes):
   - Minimum: 1 minute
   - Maximum: 1440 minutes (24 hours)
   - Default: 5 minutes
   - Recommended: 5-15 minutes for most use cases

Click **Submit**

### 3.4 Integration Complete!

The integration will now:
- Create sensors for each selected board
- Create sensors for each list within those boards
- Start polling Trello at your specified interval
- Create a device named "Trello (your_username)" to group all sensors

**Note:** The integration fetches your Trello username to properly name the integration instance. This ensures that if you add multiple accounts, each will be clearly identified and won't conflict even if they have boards with the same names.

## Step 4: Understanding Your Sensors

### Board Sensors

Format: `sensor.<board_name>_board`

Example: `sensor.work_projects_board`

**State:** Number of active lists in the board

**Attributes:**
- `board_id`: Unique Trello board ID
- `board_url`: Direct link to the board
- `closed`: Whether the board is archived
- `total_cards`: Total cards across all lists
- `overdue_cards`: Cards with past due dates
- `due_soon_cards`: Cards due within 7 days
- `lists`: Array of all lists with basic info

### List Sensors

Format: `sensor.<board_name>_<list_name>`

Example: `sensor.work_projects_to_do`

**State:** Number of cards in the list

**Attributes:**
- `board_id`: Parent board ID
- `board_name`: Parent board name
- `list_id`: Unique Trello list ID
- `closed`: Whether the list is archived
- `cards`: Full array of card objects (see below)

### Card Objects

Each card in the `cards` attribute includes:

```yaml
id: "abc123"                          # Unique card ID
name: "Fix login bug"                 # Card title
url: "https://trello.com/c/..."       # Direct link to card
closed: false                         # Archived status
due: "2025-01-20T12:00:00.000Z"      # Due date (ISO format)
due_complete: false                   # Due date marked complete
description: "Description text..."    # First 512 characters
labels: ["Bug", "High Priority"]      # Label names
members: ["John Doe", "Jane Smith"]   # Assigned members
checklist_items: 5                    # Total checklist items
checklist_items_checked: 2            # Completed items
attachments: 3                        # Number of attachments
comments: 7                           # Number of comments
```

## Step 5: Using the Integration

### In the UI

1. Go to **Settings** → **Devices & Services**
2. Find "Trello" in the list
3. Click to see all your boards as devices
4. Click any device to see its sensors

### In Dashboards

Add entity cards for your sensors:

```yaml
type: entity
entity: sensor.my_board_to_do
name: Tasks To Do
```

### In Automations

Access sensor data in automations:

```yaml
automation:
  - trigger:
      - platform: state
        entity_id: sensor.my_board_done
    action:
      - service: notify.mobile_app
        data:
          message: "Task completed!"
```

### In Templates

Query card data in templates:

```yaml
{% set cards = state_attr('sensor.my_board_to_do', 'cards') %}
{% if cards %}
  You have {{ cards | length }} cards to do
{% endif %}
```

## Step 6: Adjust Settings (Optional)

### Change Update Interval

1. Go to **Settings** → **Devices & Services**
2. Find the Trello integration
3. Click **Configure**
4. Adjust the update interval
5. Click **Submit**

### Add More Boards

You can't add boards to an existing integration instance. Instead:

1. Add the Trello integration again
2. Use the same API credentials
3. Select different boards

Each integration instance operates independently.

### Add Multiple Accounts

To monitor multiple Trello accounts:

1. Get API credentials for each account
2. Add the Trello integration multiple times
3. Use different credentials each time

**Each integration instance will:**
- Be named "Trello (username)" based on the Trello account
- Have its own device grouping all sensors
- Not conflict with other accounts, even if board names are identical
- Operate independently with its own update schedule

**Example with two accounts:**
- Account 1: "Trello (john_doe)" with Work Projects board → `sensor.trello_john_doe_work_projects_board`
- Account 2: "Trello (jane_smith)" with Work Projects board → `sensor.trello_jane_smith_work_projects_board`

No collisions, clear identification!

## Troubleshooting

### Integration Not Appearing

**Symptom:** Can't find "Trello" when adding integration

**Solutions:**
1. Clear browser cache and refresh
2. Restart Home Assistant
3. Check that files are in `config/custom_components/trello/`
4. Check Home Assistant logs for errors

### Authentication Failed

**Symptom:** "Invalid API key or token" error

**Solutions:**
1. Verify you copied the entire API key and token
2. Ensure no extra spaces before/after credentials
3. Generate a new token at https://trello.com/app-key
4. Check that your Trello account is active

### No Boards Available

**Symptom:** "No boards found" error

**Solutions:**
1. Verify you have boards in your Trello account
2. Check that boards aren't archived
3. Ensure the API token has board access permissions
4. Try logging out and back into Trello

### Sensors Not Updating

**Symptom:** Sensor values never change

**Solutions:**
1. Check the update interval isn't too long
2. Look for errors in **Settings** → **System** → **Logs**
3. Verify Trello API is accessible (check status.atlassian.com)
4. Try reloading the integration
5. Check your internet connection

### Cards Missing Data

**Symptom:** Some card attributes are empty or null

**Possible Causes:**
- Card doesn't have that attribute set (e.g., no due date)
- Card description is empty
- No checklists attached
- No members assigned

This is normal - not all cards have all attributes.

### API Rate Limiting

**Symptom:** Errors about rate limits

**Solutions:**
1. Increase update interval (use 10-15 minutes instead of 1)
2. Reduce number of monitored boards
3. Trello allows 300 requests per 10 seconds, which is generous

**Note:** Rate limiting is rare unless polling extremely aggressively.

## Advanced Usage

### Access Individual Cards in Automations

```yaml
automation:
  - trigger:
      - platform: state
        entity_id: sensor.my_board_to_do
    action:
      - service: notify.mobile_app
        data:
          message: >
            {% set cards = trigger.to_state.attributes.cards %}
            {% set urgent = cards | selectattr('labels', 'search', 'Urgent') | list %}
            You have {{ urgent | length }} urgent tasks!
```

### Monitor Specific Card Changes

Create a template sensor to track a specific card:

```yaml
template:
  - sensor:
      - name: "Bug Fix Card Status"
        state: >
          {% set cards = state_attr('sensor.dev_board_in_progress', 'cards') %}
          {% set card = cards | selectattr('name', 'eq', 'Fix login bug') | list | first %}
          {{ card.name if card else 'Not found' }}
        attributes:
          members: >
            {% set cards = state_attr('sensor.dev_board_in_progress', 'cards') %}
            {% set card = cards | selectattr('name', 'eq', 'Fix login bug') | list | first %}
            {{ card.members if card else [] }}
```

### Create a Kanban-style Dashboard

```yaml
type: vertical-stack
cards:
  - type: markdown
    content: |
      # Sprint Board
      **Total Cards:** {{ state_attr('sensor.sprint_board', 'total_cards') }}
      **Overdue:** {{ state_attr('sensor.sprint_board', 'overdue_cards') }}
  - type: horizontal-stack
    cards:
      - type: entity
        entity: sensor.sprint_board_backlog
        name: Backlog
      - type: entity
        entity: sensor.sprint_board_to_do
        name: To Do
      - type: entity
        entity: sensor.sprint_board_in_progress
        name: In Progress
      - type: entity
        entity: sensor.sprint_board_done
        name: Done
```

## Security Best Practices

1. **Never share** your API key or token
2. **Never commit** credentials to version control
3. **Regenerate tokens** if compromised
4. **Use secrets.yaml** for automation credentials if needed
5. **Revoke access** at https://trello.com/my/account if needed

## Getting Help

- **Documentation:** https://github.com/ianpleasance/home-assistant-trello
- **Issues:** https://github.com/ianpleasance/home-assistant-trello/issues
- **Examples:** See EXAMPLES.md in the repository
- **Home Assistant Forum:** Tag posts with `custom-integration` and `trello`

## Next Steps

1. Check out **EXAMPLES.md** for automation ideas
2. Create your first dashboard card
3. Set up notifications for overdue cards
4. Explore template sensors for custom metrics
5. Share your automations with the community!

## Updating the Integration

### Via HACS

1. HACS will notify you of updates
2. Click **Update** in HACS
3. Restart Home Assistant

### Manual Update

1. Download the latest release
2. Replace files in `custom_components/trello/`
3. Restart Home Assistant

## Uninstalling

1. Remove the integration from **Settings** → **Devices & Services**
2. Delete the `custom_components/trello/` folder
3. Restart Home Assistant

---

**Happy Automating!** 🎉

If you find this integration useful, consider starring the repository on GitHub!
