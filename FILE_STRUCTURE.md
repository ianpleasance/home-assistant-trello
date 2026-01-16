# Repository File Structure

Complete listing of all files in the home-assistant-trello repository.

## Root Files

- **README.md** - Main documentation with features, installation, configuration, and examples
- **SETUP_GUIDE.md** - Detailed step-by-step setup instructions
- **EXAMPLES.md** - Comprehensive automation and dashboard examples
- **QUICK_REFERENCE.md** - Quick reference card for common tasks
- **LICENSE** - MIT License
- **hacs.json** - HACS integration configuration
- **info.md** - Short description for HACS store
- **ICON_README.md** - Instructions for adding custom icon
- **.gitignore** - Git ignore patterns
- **FILE_STRUCTURE.md** - This file

## Integration Files

### `custom_components/trello/`

Core integration files:

- **manifest.json** - Integration metadata and requirements
- **__init__.py** - Main integration setup and coordinator
- **const.py** - Constants and configuration keys
- **config_flow.py** - UI configuration flow (setup & options)
- **sensor.py** - Sensor platform (board and list sensors)
- **strings.json** - UI strings for config flow

### `custom_components/trello/translations/`

- **en.json** - English translations (mirrors strings.json)

## File Purposes

### manifest.json
Defines integration metadata:
- Domain: `trello`
- Dependencies: `py-trello==0.19.0`
- Integration type: service
- IoT class: cloud_polling
- Config flow enabled

### __init__.py
Main integration logic:
- `async_setup_entry()` - Sets up integration instance
- `async_unload_entry()` - Cleans up on removal
- `TrelloDataUpdateCoordinator` - Manages data fetching
- Handles authentication and API communication

### const.py
Configuration constants:
- `DOMAIN = "trello"`
- `CONF_API_KEY`, `CONF_API_TOKEN`, `CONF_BOARDS`
- `DEFAULT_UPDATE_INTERVAL = 5` minutes
- Min/max update intervals

### config_flow.py
User interface flows:
- `TrelloConfigFlow` - Initial setup wizard
  - Step 1: API credentials
  - Step 2: Board selection
- `TrelloOptionsFlow` - Options configuration
  - Update interval adjustment

### sensor.py
Sensor entities:
- `TrelloBoardSensor` - One per board
  - State: List count
  - Attributes: Board metadata, card counts
- `TrelloListSensor` - One per list
  - State: Card count
  - Attributes: Card details array

### strings.json / en.json
UI text for:
- Setup flow steps
- Error messages
- Configuration field labels
- Option descriptions

## Documentation Files

### README.md
Primary documentation covering:
- Feature overview
- Installation methods (HACS & manual)
- Configuration steps
- Sensor descriptions
- API details
- Example automations
- Troubleshooting

### SETUP_GUIDE.md
Step-by-step guide:
- Getting Trello API credentials
- HACS installation
- Manual installation
- Configuration walkthrough
- Understanding sensors
- Advanced usage
- Troubleshooting

### EXAMPLES.md
Automation examples:
- Basic notifications
- Task tracking
- Dashboard configurations
- Advanced automations
- Template sensors
- Scripts

### QUICK_REFERENCE.md
Quick lookup for:
- Installation commands
- Sensor formats
- Common templates
- Quick automations
- Dashboard snippets
- Troubleshooting table

## License & Metadata

### LICENSE
MIT License - Full open source permissions

### hacs.json
HACS integration configuration:
- Display name
- Repository structure
- HA version requirement
- IoT classification

### info.md
Short description for HACS store with:
- Key features
- Quick start
- What you get
- Use cases

## Repository Structure Diagram

```
home-assistant-trello/
├── README.md
├── SETUP_GUIDE.md
├── EXAMPLES.md
├── QUICK_REFERENCE.md
├── FILE_STRUCTURE.md
├── LICENSE
├── hacs.json
├── info.md
├── ICON_README.md
├── .gitignore
└── custom_components/
    └── trello/
        ├── __init__.py
        ├── manifest.json
        ├── const.py
        ├── config_flow.py
        ├── sensor.py
        ├── strings.json
        └── translations/
            └── en.json
```

## File Counts

- **Total Files:** 16
- **Python Files:** 4
- **JSON Files:** 4
- **Markdown Files:** 7
- **Other:** 1 (.gitignore)

## Integration Size

- **Lines of Python Code:** ~700 lines
- **Documentation:** ~2,000 lines
- **Total Repository:** ~2,700+ lines

## Dependencies

### Python Requirements
- `py-trello==0.19.0` (specified in manifest.json)
  - Provides Trello API client
  - Handles authentication
  - Wraps REST API calls

### Home Assistant Requirements
- Minimum version: 2024.1.0
- Platforms: sensor
- Config flow: Required
- Authentication: API key + token

## Key Features Per File

### __init__.py
- Multi-account support
- Configurable polling intervals
- Automatic authentication
- Error handling
- Data coordinator pattern

### config_flow.py
- Two-step setup wizard
- Board multi-select UI
- Credential validation
- Options flow for updates
- Unique ID handling

### sensor.py
- Dynamic entity creation
- Board-level sensors
- List-level sensors
- Rich attribute data
- Due date tracking
- Label/member parsing

## Next Steps After Download

1. **Review README.md** for overview
2. **Follow SETUP_GUIDE.md** for installation
3. **Check EXAMPLES.md** for automation ideas
4. **Use QUICK_REFERENCE.md** for quick lookups
5. **Upload to GitHub** at ianpleasance/home-assistant-trello
6. **Test locally** in Home Assistant
7. **Submit to HACS** (if desired)

## Development Notes

### To Modify
- Update version in `manifest.json`
- Update CHANGELOG (if created)
- Test all changes locally
- Update documentation as needed

### To Test
1. Copy to `config/custom_components/trello/`
2. Restart Home Assistant
3. Add integration via UI
4. Verify sensors appear
5. Check data updates
6. Test automations

### To Publish
1. Tag release on GitHub
2. Update HACS (if registered)
3. Users can update via HACS

---

**Repository Ready!** All files are complete and ready for use.
