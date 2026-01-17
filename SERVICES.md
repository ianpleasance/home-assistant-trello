# Trello Services

The Trello integration provides a service to manually refresh data from Trello.

## `trello.refresh`

Force an immediate refresh of Trello data for all monitored boards, bypassing the normal update interval.

### Usage

**Refresh all Trello integrations:**
```yaml
service: trello.refresh
```

**Refresh specific integration:**
```yaml
service: trello.refresh
data:
  config_entry_id: "abc123def456"
```

### When to Use

- **Immediate updates**: You just updated a card in Trello and want to see it in Home Assistant right away
- **Testing**: Verify the integration is working correctly
- **Automation triggers**: Refresh data after creating/updating cards via API
- **Manual control**: Button/script to refresh on demand

### Examples

#### Dashboard Button to Refresh

```yaml
type: button
name: Refresh Trello
icon: mdi:refresh
tap_action:
  action: call-service
  service: trello.refresh
```

#### Automation to Refresh After Webhook

```yaml
automation:
  - alias: "Refresh Trello After Webhook"
    trigger:
      - platform: webhook
        webhook_id: trello_webhook
    action:
      - service: trello.refresh
      - delay: 
          seconds: 2
      - service: notify.mobile_app
        data:
          message: "Trello data refreshed!"
```

#### Script with Manual Refresh

```yaml
script:
  update_trello_now:
    alias: "Update Trello Now"
    sequence:
      - service: trello.refresh
      - service: persistent_notification.create
        data:
          title: "Trello Refreshed"
          message: "Data updated at {{ now().strftime('%H:%M:%S') }}"
```

#### Refresh on Home Assistant Start

```yaml
automation:
  - alias: "Refresh Trello on Startup"
    trigger:
      - platform: homeassistant
        event: start
    action:
      - delay:
          seconds: 30
      - service: trello.refresh
```

### Parameters

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| `config_entry_id` | No | Specific config entry to refresh. If omitted, all Trello integrations are refreshed. | `"abc123def456"` |

### Finding Your Config Entry ID

**Method 1: Developer Tools → States**
1. Go to Developer Tools → States
2. Find any Trello sensor (e.g., `sensor.trello_planetbuilders_account_boards`)
3. The config entry ID is not directly visible, but you can refresh all integrations without it

**Method 2: Home Assistant Logs**
Enable debug logging:
```yaml
logger:
  logs:
    custom_components.trello: debug
```

Restart HA and check logs for:
```
Refreshing Trello data for config entry: abc123def456
```

**Method 3: Just Omit It**
The easiest approach - omit `config_entry_id` to refresh all Trello integrations:
```yaml
service: trello.refresh
```

### Notes

- The service calls `async_refresh()` on the coordinator, which fetches fresh data immediately
- Data refresh happens in the background and updates all sensors
- The `last_updated` attribute will reflect the new refresh time
- Normal automatic updates continue on their schedule
- Calling this frequently may hit Trello API rate limits (300 requests per 10 seconds)

### Rate Limiting

Trello allows 300 requests per 10 seconds. Each refresh makes requests equal to:
- 1 request for all boards list
- 1 request per monitored board
- 1 request per list in each board
- 1 request for cards in each list

**Example**: 2 boards with 5 lists each = 1 + 2 + 10 + 10 = 23 requests

If you refresh too frequently, you may encounter rate limiting. The default 5-minute interval is well within safe limits.

### Troubleshooting

**Service not showing up:**
- Restart Home Assistant after installing the integration
- Check that the integration is properly configured
- Look for "Registered Trello refresh service" in logs

**Service call fails:**
- Check Home Assistant logs for errors
- Verify integration is loaded (check for sensors in States)
- Ensure you're using `trello.refresh` (not `trello_refresh`)

**Data not updating:**
- Check `last_updated` attribute before and after
- Allow 2-3 seconds for the refresh to complete
- Verify Trello API credentials are still valid

