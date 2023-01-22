from __future__ import annotations

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import ElementClickInterceptedException

from collections.abc import Callable
from datetime import datetime, timedelta
import logging
from typing import Any

from aiohttp import ClientError
from homeassistant import config_entries, core
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_ADDRESS,
    ATTR_NAME,
    CONF_NAME,
    CONF_PATH,
    CONF_URL,
)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.typing import (
    ConfigType,
    DiscoveryInfoType,
    HomeAssistantType,
)
import voluptuous as vol

from .const import (
    URL,
    DOMAIN,
    ATTR_ADDR,
    ATTR_LAST_UPDATE,
    ATTR_NEXT_PICKUP,
    ATTR_TRASH_DATES,
)

_LOGGER = logging.getLogger(__name__)
# Time between updating data
# Additionally, the sensor should update from itself every night just past midnight to remove past dates.
SCAN_INTERVAL = timedelta(days=30)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_URL): cv.url,
    }
)


async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities,
) -> None:
    """Setup sensors from a config entry created in the integrations UI."""
    config = hass.data[DOMAIN][config_entry.entry_id]
    # Update our config to include new repos and remove those that have been removed.
    if config_entry.options:
        config.update(config_entry.options)
    session = async_get_clientsession(hass)
    sensors = [HvidovreTrashCalendarSensor()]
    async_add_entities(sensors, update_before_add=True)
    global ADDRESS
    ADDRESS = config[CONF_ADDRESS]


async def async_setup_platform(
    hass: HomeAssistantType,
    config: ConfigType,
    async_add_entities: Callable,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the sensor platform."""
    session = async_get_clientsession(hass)
    sensors = [HvidovreTrashCalendarSensor()]
    async_add_entities(sensors, update_before_add=True)


class HvidovreTrashCalendarSensor(Entity):

    def __init__(self):
        super().__init__()
        self._ADDRESS = ADDRESS
        self.unique_id = "trash_" + ADDRESS.lower().replace(", ", "_").replace(" ", "_")
        self.attrs: dict[str, Any] = {ATTR_ADDR: self._ADDRESS}
        self._name = "trash_pickup_schedule"
        self._state = None
        self._available = True
        self._URL = URL
        options = Options()
        options.page_load_strategy = 'normal'
        options.headless = True
        self._driver = webdriver.Chrome(options=options)
        self.trash_dictionary = dict()

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self.repo

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._available

    @property
    def state(self) -> str | None:
        return self._state

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return self.attrs

    async def async_update(self) -> None:

        # Only do this once every SCAN_INTERVAL,
        trash_dictionary = self.poll_website()
        last_updated = datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S%z")

        # Do this every day
        next_pickup: dict[str, list[str]] = self.next_pickup(trash_dictionary)
        self.attrs[ATTR_LAST_UPDATE] = last_updated
        self.attrs[ATTR_NEXT_PICKUP] = [trash_type for trash_type in next_pickup.values()]
        self.attrs[ATTR_TRASH_DATES] = {key: val for key, val in trash_dictionary.items()}
        self._state = [date for date in next_pickup.keys()][0]
        self.attrs[ATTR_NAME] = self._name

    def poll_website(self) -> dict[str,list[str]]:
        # Use for setting some options:
        options = Options()

        # Default loading strategy <- does this interfere with the "element = " method below?
        options.page_load_strategy = 'normal'

        # Don't open browser, run in headless mode
        options.headless = True

        self.open_website()
        self.input_address()
        self.expand_trash_types()
        trash_dictionary = self.get_calendars()
        return trash_dictionary

    def open_website(self, options):

        self._driver.get(self._URL)

    def input_address(self):
        # Find the text input box and submit button
        text_box = self._driver.find_element(By.XPATH, '//*[@id="address"]')
        submit_button = self._driver.find_element(By.XPATH, "/html/body/div[1]/div[2]/div[2]/div[1]/div[2]/div[6]/div/a")

        # Explicitly wait for the text input box to become available to verify webpage has loaded
        WebDriverWait(self._driver, timeout=3).until(lambda d: d.find_element(By.XPATH, '//*[@id="address"]'))

        # input ADDRESS into text box
        text_box.send_keys(self._ADDRESS)

        # Wait until the autocomplete suggestion appears (there's got to be a better way!), then navigate with arrow down
        time.sleep(0.5)
        text_box.send_keys(Keys.ARROW_DOWN)

        # Wait until arrow down highlights suggestion (there's got to be a better way!), then press enter to select
        time.sleep(0.5)
        text_box.send_keys(Keys.ENTER)

        # Wait until selection is accepted (there's got to be a better way!), then click the submit button.
        time.sleep(0.6)
        submit_button.click()

        # Wait until an element on the next page loads.
        WebDriverWait(self._driver, timeout=3).until(lambda d: d.find_element(By.XPATH, "/html/body/div[1]/div[2]/div[3]/div[1]/div[2]/div[18]/div[1]/div/div/div/div/div[2]/div/table/tbody/tr[1]/td[1]"))

    def expand_trash_types(self) -> None:
        # Get a list of all odd numbers from 1 to 27
        drop_down_xpaths = [(number * 2 + 1) for number in range(14)]

        # Create the XPATH for each drop-down menu
        # Each time a menu is clicked, the index indicated by integers in drop_down_xpaths will skip one
        # as one new of corresponding XPATH will appear just after the one clicked.
        # This means the first is [1], the second would be [2], but as soon as [1] is clicked, the second changes to [3].
        # With each XPATH, click each drop-down to expand all.
        # Also wait for an additional to appear before next loop.
        for i in range(len(drop_down_xpaths)):
            prescript = "/html/body/div[1]/div[2]/div[3]/div[1]/div[2]/div[18]/div[1]/div/div/div/div/div[2]/div/table/tbody/tr["
            postscript = "]/td[1]"
            element = prescript + str(drop_down_xpaths[i]) + postscript
            wait_for_element = prescript + str(drop_down_xpaths[i] + 14 - i) + postscript
            drop_down = self._driver.find_element(By.XPATH, element)
            drop_down.click()
            WebDriverWait(self._driver, timeout=3).until(lambda d: d.find_element(By.XPATH, wait_for_element))

    def get_calendars(self) -> dict[str, list[str]]:

        # Get a list of all the calendar buttons
        calendars = self._driver.find_elements(By.CLASS_NAME, "glyphicon-calendar")

        # Initiate the count
        modal_body_count = 1

        trash_dictionary: dict = dict()

        # Loop over clicking calendar buttons to pop up calendars
        for i in range(len(calendars)):
            if calendars[i].is_displayed():
                calendars[i].click()

                # A wait that loops until the calendar appears.
                # This works for subsequent calendars because once they appear, their code does not disappear again
                # once dismissed.
                while len(self._driver.find_elements(By.CLASS_NAME, "modal-body")) < modal_body_count:
                    pass

                # Increase count
                modal_body_count += 1

                header, danish_date_list = self.get_headers_and_dates()
                iso_date_list = self.get_dates_iso_8601(danish_date_list)
                trash_dictionary[header] = iso_date_list
                self.close_calendar()

        return trash_dictionary

    def get_headers_and_dates(self):
        # Get list of all headers and dates from the calendar
        headers = self._driver.find_elements(By.ID, "modalHeader")
        dates = self._driver.find_elements(By.CLASS_NAME, "modal-body")

        # Initiate header and danish_date_list so the script won't terminate in case no "real" values are found
        header = "None"
        danish_date_list = []

        # As more and more calendars are opened, most `headers` and `dates` will be empty.
        # This will find the relevant ones
        for j in range(len(headers)):
            try:

                # If it is not empty
                if len(dates[j].text) > 1:

                    # If date(s) are set, they have the format "Mandag den 23-01-2023". This check for that.
                    # Some calendars may show "Ingen planlagte tømninger", these would not be added.
                    if dates[j].text.split(" ")[1] == "den":
                        # Get header from header_substitution by passing the full header from calendar.
                        header = self.header_substitution(headers[j].text)

                        # Get a list of the days and dates, and strip away days to only have DD-MM-YYYY
                        all_dates = dates[j].text.split("\n")
                        danish_date_list = [all_dates[k].split(" ")[-1] for k in range(len(all_dates))]
            except IndexError:
                print("IndexError, please ensure the correct calendar can be opened")

        return header, danish_date_list

    def get_dates_iso_8601(self, danish_date_list):

        # Initiate iso_date_list so the script won't terminate in case no "real" values are found
        iso_date_list = []

        # Rewrite the danish format dates (DD-MM-YYYY) to ISO-8601 format (YYYY-MM-DD)
        try:
            iso_date_list = [
                danish_date_list[l].split("-")[-1] + "-" +
                danish_date_list[l].split("-")[-2] + "-" +
                danish_date_list[l].split("-")[-3]
                for l in range(len(danish_date_list))
            ]
        except IndexError:
            print("ERROR ON DANISH_DATE_LIST")

        return iso_date_list

    def close_calendar(self):
        # Find the button, incl. the one that closes the calendar
        close_buttons = self._driver.find_elements(By.CLASS_NAME, "btn-sm")

        # Close the calendar again (click button), in order to be able to access the next.
        # Many buttons will be in close_buttons, but only the one to close the open calendar `is_displayed`
        for close_button in close_buttons:
            if close_button.is_displayed():
                try:
                    close_button.click()
                except ElementClickInterceptedException:
                    pass

        # Wait for a button that is obscured by the open calendar to become clickable before looping.
        WebDriverWait(self._driver, timeout=3).until(expected_conditions.element_to_be_clickable(
            (By.XPATH, "/html/body/div[1]/div[2]/div[3]/div[1]/div[2]/div[14]/div/div/div/button")))

    def header_substitution(self, header) -> str:
        """
        This creates the header, which is a string identifying the type of trash in question
        by ether parsing or simply substituting based on the presence of a sbu-string in the input string.
        """

        header_1 = header.split(': "')[1]
        header_2 = ""
        if ", " in header_1:
            header_2 = header_1.split(", ")[0]
        elif "240" in header_1:
            header_2 = header_1.split(" 240")[0]
        elif " (" in header_1:
            header_2 = header_1.split(" (")[0]
        if "Meco" in header_2:
            header_2 = header_2.split(" ")[0]
        if "Pap" in header_2:
            header_2 = "Pap"
    
        return header_2

    def next_pickup(self, trash_dictionary) -> dict[str, list[str]]:

        time_format = "%Y-%m-%d"
        next_pickup: dict = {}
        for key, val in trash_dictionary.items():
            if next_pickup == {}:
                next_pickup[val[0]] = [key]
            for i in val:  # iso_date_list
                for date, types in next_pickup.items():
                    if date == i:
                        next_pickup[date].append(key)
                    elif datetime.strptime(date, time_format) > datetime.strptime(i, time_format):
                        del next_pickup[date]
                        next_pickup[i] = [key]
        return next_pickup

    @unique_id.setter
    def unique_id(self, value):
        self._unique_id = value
