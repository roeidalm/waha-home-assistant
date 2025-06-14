# WAHA Home Assistant Integration

A custom component for [Home Assistant](https://www.home-assistant.io/) that integrates with [WAHA (WhatsApp HTTP API)](https://github.com/username/waha) to send and receive WhatsApp messages, automate notifications, and handle WhatsApp events.

---

## Features
- Send WhatsApp notifications from Home Assistant automations and scripts
- Receive WhatsApp messages as Home Assistant events (webhook)
- Secure API key support
- Phone number validation and formatting
- Rate limiting and error handling
- HACS compatibility for easy updates
- Example automations for common use cases

---

## Requirements
- Home Assistant 2022.0 or newer
- Python 3.9+
- A running [WAHA](https://github.com/username/waha) instance (self-hosted WhatsApp HTTP API)
- Network connectivity between Home Assistant and WAHA

---

## Installation

### HACS (Recommended)
1. Go to **HACS > Integrations** in Home Assistant
2. Click the three dots (⋮) and select **Custom repositories**
3. Add this repository URL and select **Integration**
4. Search for "WAHA" and install
5. Restart Home Assistant

### Manual
1. Download or clone this repository
2. Copy the `custom_components/waha` folder to your Home Assistant `custom_components` directory
3. Restart Home Assistant

---

## Configuration

### UI Configuration (Recommended)
1. Go to **Settings > Devices & Services**
2. Click **Add Integration** and search for "WAHA"
3. Enter your WAHA instance URL (e.g., `http://192.168.1.100:3000`)
4. (Optional) Enter your API key and session name
5. (Optional) Set default recipients (phone numbers with country code, e.g., `+1234567890`)
6. Complete the setup

### YAML Configuration (Advanced)
YAML configuration is not required for most users. Use the UI for best results.

---

## Usage

### Sending WhatsApp Notifications
Use the `notify` service in automations or scripts:

```yaml
service: notify.waha_whatsapp
data:
  message: "Hello from Home Assistant!"
  target: "+1234567890"  # Optional, can be a list
```

- `message`: The text to send
- `target`: Phone number(s) (with country code, e.g., `+1234567890`). If omitted, uses default recipients.

### Handling Incoming WhatsApp Messages
Incoming messages trigger the `waha_message_received` event:

```yaml
automation:
  - alias: "Respond to WhatsApp Status Request"
    trigger:
      platform: event
      event_type: waha_message_received
    condition:
      - condition: template
        value_template: '{{ trigger.event.data.message | lower == "status" }}'
    action:
      - service: notify.waha_whatsapp
        data:
          target: "{{ trigger.event.data.sender }}"
          message: "Home status: All systems operational."
```

**Event data includes:**
- `sender`: Phone number of the sender
- `message`: Message text
- `timestamp`, `session`, `message_id`

---

## Example Automations
See the [`examples/`](./examples/) directory for ready-to-use YAML:
- `notifications.yaml`: Send notifications on events (e.g., door open, weather report)
- `message_handling.yaml`: Respond to WhatsApp messages, control devices via WhatsApp

---

## Troubleshooting
- See [`TROUBLESHOOTING.md`](./TROUBLESHOOTING.md) for solutions to common issues (connection, API key, webhook, etc.)
- Enable debug logging in `configuration.yaml`:
  ```yaml
  logger:
    default: info
    logs:
      custom_components.waha: debug
  ```
- Check Home Assistant and WAHA logs for errors

---

## HACS Compatibility
- Includes `manifest.json` and `hacs.json` for seamless HACS integration
- Updates and new versions will be available via HACS if installed that way

---

## Contributing & Support
- Pull requests and issues are welcome! See [GitHub Issues](https://github.com/username/waha-home-assistant/issues)
- For help, check the troubleshooting guide or open an issue with logs and details
- Please include Home Assistant version, WAHA version, and steps to reproduce any problems

---

## License
[MIT](./LICENSE) 