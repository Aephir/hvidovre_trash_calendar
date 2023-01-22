# Hvidovre Trash Calendar for Home Assistant
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

This is an integration that navigates through the [website](https://hvidovre.renoweb.dk/Legacy/selvbetjening/mit_affald.aspx) that can provide a calendar for trash pickup dates in Hvidovre municipality (Denmark), and adds this information to a sensor in Home Assistant.

Unfortunately, this information is only available by navigating through a website inputting an address, and scraping the data from the website. I have requested an API, and will update the integration if this can be provided.    

## Installation

### HACS

- Ensure that [HACS](https://hacs.xyz/) is installed. 
- Add `Aephir/hvidovre_trash_calendar` in "Custom Repositories"
- Search for and install the "Hvidovre Trash Calendar" integration. 
- Restart Home Assistant.

### Manual installation

- Download the latest release. 
- Unpack the release and copy the custom_components/trash directory into the custom_components directory of your Home Assistant installation. 
- Restart Home Assistant.


