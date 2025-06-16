# WAHA Home Assistant Integration Troubleshooting Guide

This guide provides solutions to common issues you may encounter when using the WAHA WhatsApp integration for Home Assistant.

## Common Issues & Solutions

### 1. Cannot Connect to WAHA Instance
- **Symptoms:**
  - Error: "Failed to connect to WAHA server. Please check the URL and API key."
  - Integration setup fails or times out.
- **Solutions:**
  - Ensure your WAHA instance is running and accessible from your Home Assistant server.
  - Double-check the WAHA server URL (should be like `http://your-waha-instance:3000`).
  - If using an API key, verify it is correct and has the necessary permissions.
  - Check for network/firewall issues between Home Assistant and WAHA.

### 2. Messages Not Being Sent
- **Symptoms:**
  - No WhatsApp messages are delivered.
  - Errors in Home Assistant logs about message delivery failures.
- **Solutions:**
  - Verify the phone number format (must include country code and start with `+`).
  - Check that the recipient's WhatsApp account is active.
  - Review Home Assistant logs for API errors or rate limiting messages.
  - Ensure your WAHA instance is not rate-limited or blocked by WhatsApp.
  - Make sure your WhatsApp session is authenticated in WAHA.

### 3. Invalid Phone Number Format
- **Symptoms:**
  - Error: "Invalid phone number format" in Home Assistant logs.
- **Solutions:**
  - Use international format for all phone numbers (e.g., `+1234567890`).
  - Remove spaces, dashes, or other non-numeric characters.
  - Ensure phone numbers start with `+` followed by country code.

### 4. API Key Issues
- **Symptoms:**
  - Error: "Invalid authentication. Please check your API key."
- **Solutions:**
  - Double-check the API key in your integration configuration.
  - Ensure the API key is active and has not expired or been revoked.
  - Store the API key securely and do not expose it in logs or public repositories.

### 5. WhatsApp Session Not Authenticated
- **Symptoms:**
  - Warning: "WhatsApp session is not authenticated" in logs.
  - Messages fail to send with authentication errors.
- **Solutions:**
  - Access your WAHA instance web interface and scan the QR code with your phone.
  - Ensure the WhatsApp session is properly authenticated before sending messages.
  - Check WAHA logs for session-related errors.

### 6. Rate Limiting Issues
- **Symptoms:**
  - Messages are delayed or fail to send.
  - "Rate limit exceeded" errors in logs.
- **Solutions:**
  - Reduce the frequency of message sending in your automations.
  - Adjust the rate limit settings in the integration configuration.
  - Spread out message sending over time to avoid hitting WhatsApp limits.

## Debugging Tips

- Enable debug logging for the integration by adding the following to your `configuration.yaml`:
  ```yaml
  logger:
    default: info
    logs:
      custom_components.waha: debug
  ```
- Check the Home Assistant logs for detailed error messages and stack traces.
- Test your WAHA instance independently using tools like `curl` or Postman to verify connectivity.
- Use the Services tab in Home Assistant Developer Tools to test sending messages manually.

## Getting Help

If you are unable to resolve your issue, please:
- Review the [README](README.md) for setup and usage instructions.
- Search for similar issues or open a new issue on the [GitHub repository](https://github.com/roeidalm/waha-home-assistant/issues).
- Provide detailed logs and configuration snippets when seeking support.
- Include your Home Assistant version, WAHA version, and steps to reproduce the issue. 