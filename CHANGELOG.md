# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2025-01-15

### Added
- Initial release of the Trello integration for Home Assistant
- Support for multiple Trello accounts
- Configurable update intervals (1-1440 minutes, default 5)
- Board selection via UI configuration flow
- Board sensors showing list counts and card statistics
- List sensors showing card counts with detailed card information
- Rich card data including:
  - Basic info: ID, name, URL, closed status
  - Due dates: Due date and completion status
  - Content: Description (512 chars), labels, members
  - Metadata: Checklist progress, attachments, comments
- Automatic overdue and due-soon card tracking
- Device grouping per account for organization
- Username-based integration naming to prevent conflicts

### Features

#### Multi-Account Support with Collision Prevention
The integration properly handles multiple Trello accounts with boards of the same name:
- Each account gets a unique device named "Trello (username)"
- All sensors are namespaced under their account device
- Entity IDs include username to prevent collisions
- Example: Two accounts with "Work Projects" board:
  - Account 1: `sensor.trello_john_work_projects_board`
  - Account 2: `sensor.trello_jane_work_projects_board`

#### Smart Entity Naming
- Fetches Trello username/full name during setup
- Uses this for integration title: "Trello (username)"
- Provides clear identification when managing multiple accounts
- Falls back to "Trello Account" if username fetch fails

#### Device Grouping
- All sensors for an account are grouped under one device
- Device name matches integration title for consistency
- Easy to find and manage all sensors for a specific account
- Proper manufacturer and model attribution

### Technical Implementation
- Uses `entry.entry_id` for unique sensor IDs
- Implements `device_info` on all entities for grouping
- Fetches member info via Trello API during config flow
- API key serves as unique_id for preventing duplicate accounts

### Documentation
- Complete README with features and examples
- Detailed SETUP_GUIDE with step-by-step instructions
- EXAMPLES.md with 10+ automation examples
- QUICK_REFERENCE.md for fast lookups
- FILE_STRUCTURE.md for developers

### Dependencies
- py-trello==0.19.0
- Home Assistant 2024.1.0 or later

### Known Limitations
- Card descriptions truncated to 512 characters
- Comments count may not be available on all cards (API limitation)
- No write capabilities (read-only integration)

---

## Future Considerations

### Potential Future Enhancements
- Service to create/update/move cards
- Service to add comments to cards
- Webhook support for real-time updates
- Configurable description truncation length
- Card attachment content retrieval
- Custom card filters in config flow
- Board/list/card binary sensors for automation triggers
- Card activity feed tracking

### Not Planned
- OAuth authentication (Trello recommends API key/token for integrations)
- Card editing UI (out of scope for Home Assistant sensor platform)
- Full Trello client functionality (use Trello app for management)

---

## Version History

### [1.0.0] - 2025-01-15
- Initial release
- Complete feature set for read-only board/list/card monitoring
- Multi-account support with collision prevention
- Comprehensive documentation and examples
