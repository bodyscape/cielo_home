# Cielo Home devices integration for HomeAssistant

[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)
[![cielo_home](https://img.shields.io/github/release/bodyscape/cielo_home/all.svg?style=for-the-badge)](https://github.com/bodyscape/cielo_home/releases)
![Maintenance](https://img.shields.io/maintenance/yes/2023.svg?style=for-the-badge)
[![](https://img.shields.io/badge/MAINTAINER-bodyscape-red?style=for-the-badge)](https://github.com/bodyscape)

[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/donate/?hosted_button_id=BKQL5JUGZBZXU)
[![Buy me a coffee](https://img.shields.io/static/v1.svg?label=Buy%20me%20a%20coffee&message=🥨&color=black&logo=buy%20me%20a%20coffee&logoColor=white&labelColor=6f4e37)](https://www.buymeacoffee.com/bodyscape)

A HomeAssistant custom integration to control Cielo Home devices.

## Functionality

![image](https://user-images.githubusercontent.com/30115568/217594793-e3009fee-bd3d-47aa-8638-dfc5af8b4e92.png)

A exemple of thermostat card i use : https://github.com/nervetattoo/simple-thermostat

![image](https://user-images.githubusercontent.com/30115568/218138232-3249b15e-ce08-4eee-bbeb-178d7e150caa.png)

``` yaml
# YAML
- type: custom:simple-thermostat
        entity: climate.basement
        step_size: 1
        layout:
          step: row
          mode:
            names: true
            headings: false
        header: true
        control:
          hvac:
            _name: Mode
          fan:
            _name: Fan Mode
          swing:
            _name: Swing Mode
          preset:
            _name: Preset Mode
```

## Installation

### HACS

1. Install [HACS](https://hacs.xyz/)
2. Go to HACS "Integrations >" section
3. Click 3 dots in top right
4. Click "Custom repositories"
5. Add repository https://github.com/bodyscape/cielo_home with category `Integration`
6. In the lower right click "+ Explore & Download repositories"
7. Search for "Cielo Home" and add it
8. In the Home Assistant (HA) UI go to "Configuration"
9. Click "Integrations"
10. Click "+ Add Integration"
11. Search for "Cielo Home"

### Manual

1. Using the tool of choice open the directory (folder) for your [HA configuration](https://www.home-assistant.io/docs/configuration/) (where you find `configuration.yaml`).
2. If you do not have a `custom_components` directory (folder) there, you need to create it.
3. In the `custom_components` directory (folder) create a new folder called `cielo_home`.
4. Download _all_ the files from the `custom_components/cielo_home/` directory (folder) in this repository.
5. Place the files you downloaded in the new directory (folder) you created.
6. Restart Home Assistant
7. In the Home Assistant (HA) UI go to "Configuration"
8. Click "Integrations"
9. Click "+ Add Integration"
10. Search for "Cielo Home"
