import time
from typing import Union, Tuple

from selenium.common import TimeoutException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from boba_python_utils.general_utils.console_util import hprint_message
from boba_python_utils.time_utils.common import random_sleep
from boba_web_agent.automation.web_automatoin.selenium.common import wait_for_page_loading


def send_keys_with_random_delay(element, text, min_delay=0.1, max_delay=1):
    """Send keys to an element, character by character, with a random delay between each key.

    Args:
        element: The WebElement where text will be sent.
        text: The string to send to the element.
        min_delay (float): Minimum delay between key presses in seconds.
        max_delay (float): Maximum delay between key presses in seconds.
    """
    element.click()
    random_sleep(min_delay, max_delay)
    for char in text:
        element.send_keys(char)
        random_sleep(min_delay, max_delay)


def center_element_in_view(driver: WebDriver, element: WebElement) -> None:
    """
    Scrolls the given WebElement into the center of the view.

    Args:
        driver (WebDriver): The Selenium WebDriver instance.
        element (WebElement): The WebElement to bring to the center of the view.
    """
    driver.execute_script("""
        var element = arguments[0];
        element.scrollIntoView({block: 'center', inline: 'center', behavior: 'smooth'});
    """, element)


def set_zoom(driver: WebDriver, percentage: Union[int, float]) -> None:
    """
    Sets the zoom level of the webpage to the specified percentage.

    Args:
        driver (WebDriver): The Selenium WebDriver instance.
        percentage (int): The zoom level percentage (e.g., 100 for 100%).
    """
    if isinstance(percentage, float):
        if percentage <= 1:
            percentage = int(percentage * 100)
        else:
            percentage = int(percentage)
    zoom_script = f"document.body.style.zoom='{percentage}%'"
    driver.execute_script(zoom_script)


def get_zoom(driver: WebDriver) -> float:
    zoom = driver.execute_script("return document.body.style.zoom || '100%'").rstrip('%')
    return float(zoom) / 100


def get_viewport_size(driver: WebDriver) -> Tuple[int, int]:
    """
    Gets the viewport width and height of the current window.

    Args:
        driver (WebDriver): The Selenium WebDriver instance.

    Returns:
        tuple: A tuple containing the viewport width and height.
    """
    viewport_size = driver.execute_script("""
        return {
            width: window.innerWidth,
            height: window.innerHeight
        };
    """)
    return viewport_size['width'], viewport_size['height']


def zoom_out_to_fit_element(driver: WebDriver, element: WebElement, buffer: float = 0.05) -> None:
    """
    Zooms out the page until the given WebElement is entirely within the viewport,
    considering a buffer to zoom out more and taking into account the current zoom level.

    Args:
        driver (WebDriver): The Selenium WebDriver instance.
        element (WebElement): The WebElement to fit within the viewport.
        buffer (float): The additional zoom out factor. Defaults to 0.05 (5% more).
    """
    current_zoom = get_zoom(driver)

    driver.execute_script("""
        var element = arguments[0];
        var buffer = arguments[1];
        var currentZoom = arguments[2];
        var rect = element.getBoundingClientRect();
        var elementHeight = rect.height / currentZoom;
        var elementWidth = rect.width / currentZoom;
        var viewportHeight = window.innerHeight;
        var viewportWidth = window.innerWidth;
        var zoomFactor = Math.min(viewportHeight / elementHeight, viewportWidth / elementWidth);
        document.body.style.zoom = zoomFactor - buffer;
    """, element, buffer, current_zoom)


def capture_full_page_screenshot(
        driver,
        output_path,
        center_element: WebElement = None,
        restore_window_size: bool = False,
        reset_zoom: bool = True
):
    original_size = driver.get_window_size()
    total_width = driver.execute_script('return document.body.parentNode.scrollWidth')
    total_height = driver.execute_script('return document.body.parentNode.scrollHeight')
    driver.set_window_size(total_width, total_height)
    time.sleep(3)
    page_zoomed = False
    if center_element is not None:
        zoom_out_to_fit_element(driver, center_element)
        center_element_in_view(driver, center_element)
        page_zoomed = True
    wait_for_page_loading(driver)

    screenshot = driver.get_screenshot_as_png()
    with open(output_path, "wb") as file:
        file.write(screenshot)

    if page_zoomed and reset_zoom:
        set_zoom(driver, 100)
        time.sleep(2)
        wait_for_page_loading(driver)
    if restore_window_size:
        driver.set_window_size(original_size['width'], original_size['height'])
        time.sleep(2)
        wait_for_page_loading(driver)


def open_url(
        driver: WebDriver,
        url: str = None,
        wait_after_opening_url: float = 0
):
    if url:
        try:
            driver.get(url)
            if wait_after_opening_url:
                from time import sleep
                sleep(wait_after_opening_url)
        except TimeoutException:
            hprint_message('timeout', url)
            driver.execute_script('window.stop();')
