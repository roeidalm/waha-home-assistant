#!/bin/bash

# Create a development Home Assistant configuration
CONFIG_DIR="./config"
CUSTOM_COMPONENTS_DIR="$CONFIG_DIR/custom_components"

# Create necessary directories
mkdir -p "$CONFIG_DIR"
mkdir -p "$CUSTOM_COMPONENTS_DIR"

# Create symbolic link to our custom component
if [ ! -L "$CUSTOM_COMPONENTS_DIR/waha" ]; then
    ln -s "$(pwd)/custom_components/waha" "$CUSTOM_COMPONENTS_DIR/waha"
fi

# Create a basic configuration.yaml if it doesn't exist
if [ ! -f "$CONFIG_DIR/configuration.yaml" ]; then
    cat > "$CONFIG_DIR/configuration.yaml" << 'EOF'
default_config:

logger:
  default: info
  logs:
    custom_components.waha: debug

# Uncomment and update these values to test your integration
# waha:
#   base_url: "http://localhost:3000"
#   api_key: "your_api_key"
#   default_recipients: "1234567890"
#   session_name: "dev_session"
EOF
fi

# Install development dependencies if not in virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
fi

# Install Home Assistant and development dependencies
pip install homeassistant
pip install -r requirements.txt

# Run Home Assistant
hass -c "$CONFIG_DIR" --debug 