# Cielo Wigle 

A Home Assistant Custom Component for Cielo Wigle (cloud)

## Functionality

This integration aims to use the same API as the app to enable control via Home Assistant.

Currently it provides a Climate entity and a temperature sensor as an initial release.

## Installation

### HACS

1. Install [HACS](https://hacs.xyz/)
2. Go to HACS "Integrations >" section
3. Click 3 dots in top right
4. Click "Custom repositories"
5. Add repository https://github.com/bodyscape/cielo_wigle with category `Integration`
6. In the lower right click "+ Explore & Download repositories"
7. Search for "Cielo Wigle (cloud)" and add it
8. In the Home Assistant (HA) UI go to "Configuration"
9. Click "Integrations"
10. Click "+ Add Integration"
11. Search for "Cielo Wigle (cloud)"

### Manual

1. Using the tool of choice open the directory (folder) for your [HA configuration](https://www.home-assistant.io/docs/configuration/) (where you find `configuration.yaml`).
2. If you do not have a `custom_components` directory (folder) there, you need to create it.
3. In the `custom_components` directory (folder) create a new folder called `maestro_mcz`.
4. Download _all_ the files from the `custom_components/cielo_wigle/` directory (folder) in this repository.
5. Place the files you downloaded in the new directory (folder) you created.
6. Restart Home Assistant
7. In the Home Assistant (HA) UI go to "Configuration"
8. Click "Integrations"
9. Click "+ Add Integration"
10. Search for "Cielo Wigle (cloud)"
