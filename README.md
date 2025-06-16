# WAHA Home Assistant Integration

A simple custom component for [Home Assistant](https://www.home-assistant.io/) that integrates with [WAHA (WhatsApp HTTP API)](https://github.com/devlikeapro/waha) to send WhatsApp messages from your Home Assistant automations and scripts.

---

## Features
- Send WhatsApp notifications from Home Assistant automations and scripts
- Secure API key support
- Phone number validation and formatting
- Rate limiting and error handling
- HACS compatibility for easy updates
- Simple and lightweight - focused on sending messages only

---

## Requirements
- Home Assistant 2022.0 or newer
- Python 3.9+
- A running [WAHA](https://github.com/devlikeapro/waha) instance (self-hosted WhatsApp HTTP API)
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

### Service Call Example
You can also use the direct service call:

```yaml
service: waha.send_message
data:
  phone: "+1234567890"
  message: "Hello from Home Assistant!"
```

---

## Example Automations

### Door Open Notification
```yaml
automation:
  - alias: "Notify when door opens"
    trigger:
      platform: state
      entity_id: binary_sensor.front_door
      to: "on"
    action:
      - service: notify.waha_whatsapp
        data:
          message: "🚪 Front door has been opened!"
          target: "+1234567890"
```

### Daily Weather Report
```yaml
automation:
  - alias: "Daily weather report"
    trigger:
      platform: time
      at: "08:00:00"
    action:
      - service: notify.waha_whatsapp
        data:
          message: >
            🌤️ Good morning! Today's weather:
            {{ states('weather.home') }}
            High: {{ state_attr('weather.home', 'temperature') }}°
            {{ state_attr('weather.home', 'forecast')[0].condition }}
```

---

## Troubleshooting
- See [`TROUBLESHOOTING.md`](./TROUBLESHOOTING.md) for solutions to common issues
- Enable debug logging in `configuration.yaml`:
  ```yaml
  logger:
    default: info
    logs:
      custom_components.waha: debug
  ```
- Check Home Assistant and WAHA logs for errors
- Ensure your WAHA instance is running and accessible
- Verify phone numbers include country code (e.g., `+1234567890`)

---

## HACS Compatibility
- Includes `manifest.json` and `hacs.json` for seamless HACS integration
- Updates and new versions will be available via HACS if installed that way

---

## Contributing & Support
- Pull requests and issues are welcome! See [GitHub Issues](https://github.com/roeidalm/waha-home-assistant/issues)
- For help, check the troubleshooting guide or open an issue with logs and details
- Please include Home Assistant version, WAHA version, and steps to reproduce any problems

---

## License
[MIT](./LICENSE) 