# Cielo Home / Mr Cool devices integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)
[![cielo_home](https://img.shields.io/github/release/bodyscape/cielo_home/all.svg?style=for-the-badge)](https://github.com/bodyscape/cielo_home/releases)
![Maintenance](https://img.shields.io/maintenance/yes/2023.svg?style=for-the-badge)
[![](https://img.shields.io/badge/MAINTAINER-bodyscape-red?style=for-the-badge)](https://github.com/bodyscape)

<a href="https://www.buymeacoffee.com/bodyscape"><img src="https://img.buymeacoffee.com/button-api/?text=Buy me a coffee&emoji=&slug=bodyscape&button_colour=FFDD00&font_colour=000000&font_family=Cookie&outline_colour=000000&coffee_colour=ffffff"></a>

A Home Assistant custom integration to control Cielo Home devices.

## Configuration

If you have installed a version prior 1.6.0 you need to uninstall the integration and install it again.
You need to restart HA after the uninstall and after the install.

For find the field in the initial configuration setup follow this.

1. Open a new chrome to https://home.cielowigle.com/.
2. Open the console tool with F12.
3. Click on the 'Network' tab.
4. Check the option 'Disable cache' and 'Preserve log'
5. Fill your login, password and complete the recaptcha.
6. Click 'Sign in'.

![image](https://github.com/bodyscape/cielo_home/assets/30115568/3d1878e3-031e-4ab7-86ab-464c15b11eeb)

7. Click on the new row on network who have the 'login' on it.
8. Click on the new subtab 'Response'
9. Copy all the Response in a text file and close Chrome (Don't sign out, close the whole Chrome not just the tab. Really important)
10. Search within text file to find and copy/paste the values in configuration dialog (without quotes).
11. Also Keep in mind if your HA or this integration don't run for more than 1 hour you must uninstall it and reinstall it.

![image](https://github.com/bodyscape/cielo_home/assets/30115568/96702e55-d4e0-4815-8316-a9a6cfbbab74)


## Functionality

![image](https://user-images.githubusercontent.com/30115568/229196023-6d2923fa-a09d-4e03-8615-78060a2003d6.png)


You can call the Cielo Sync AC State as a HA service.

![image](https://user-images.githubusercontent.com/30115568/229198720-c6cbd225-8929-4593-8a49-b015f05f3761.png)


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

# Installation

## With HACS

Click on the button below to automatically navigate to the repository within HACS:

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=bodyscape&repository=cielo_home&category=integration)

Alternatively, follow the steps below:

1. Go to HACS "Integrations >" section
2. Click 3 dots in top right
3. Click "Custom repositories"
4. Add repository https://github.com/bodyscape/cielo_home with category Integration
5. In the lower right click "+ Explore & Download repositories"
6. Search for "Cielo Home" and add it

## Manual
Copy the `cielo_home` directory, from `custom_components` in this repository,
and place it inside your Home Assistant Core installation's `custom_components` directory.

`Note`: If installing manually, in order to be alerted about new releases, you will need to subscribe to releases from this repository. 

## Setup

Click on the button below to add the integration:

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=cielo_home)

Alternatively, follow the steps below:

1. Install this integration.
2. Navigate to the Home Assistant Integrations page (Settings --> Devices & Services)
3. Click the `+ ADD INTEGRATION` button in the lower right-hand corner
4. Search for `Cielo`
