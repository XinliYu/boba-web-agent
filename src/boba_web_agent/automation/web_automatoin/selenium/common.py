from typing import List, Optional, Tuple

from bs4 import BeautifulSoup
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait


# region page loading & status
def get_ready_state(driver: WebDriver):
    return driver.execute_script("return document.readyState")


def wait_for_page_loading(driver: WebDriver, timeout: int = 20):
    """
    Wait for the page to be fully loaded.

    Args:
        timeout: The maximum time to wait for the page to load. Default is 30 seconds.
    """
    WebDriverWait(driver, timeout).until(
        lambda driver: get_ready_state(driver) == "complete"
    )


# endregion


# region get html & text
def get_element_html(element: WebElement) -> Optional[str]:
    if element is not None:
        return element.get_attribute("outerHTML")


def get_element_text(element: WebElement) -> Optional[str]:
    """
    Returns the visible text content of the given WebElement.

    Args:
        element (WebElement): The WebElement from which to retrieve the text.

    Returns:
        Optional[str]: The visible text content of the element, or None if the element is None.
    """
    if element is not None:
        return element.text
    return None


def get_body_html(driver: WebDriver, return_dynamic_contents: bool = True) -> str:
    return (
        driver.execute_script("return document.body.outerHTML")
        if return_dynamic_contents
        else driver.page_source
    )


def get_body_html_from_url(
        driver: WebDriver,
        url: str = None,
        initial_wait_after_opening_url: float = 0,
        timeout_for_page_loading: int = 20,
        return_dynamic_contents: bool = True
) -> str:
    from boba_web_agent.automation.web_automatoin.selenium.actions import open_url
    if url:
        open_url(
            driver=driver,
            url=url,
            wait_after_opening_url=initial_wait_after_opening_url
        )
        wait_for_page_loading(driver, timeout_for_page_loading)
    return get_body_html(
        driver=driver,
        return_dynamic_contents=return_dynamic_contents
    )


def get_text(
        driver,
        url: str,
        initial_wait: float = 0,
        timeout_for_page_loading: int = 20,
        id_class_keywords_match_to_remove: List[str] = None,
        id_class_keywords_match_to_keep: List[str] = None,
        return_dynamic_contents: bool = True
):
    html = get_body_html_from_url(
        driver=driver,
        url=url,
        initial_wait_after_opening_url=initial_wait,
        timeout_for_page_loading=timeout_for_page_loading,
        return_dynamic_contents=return_dynamic_contents
    )
    soup = BeautifulSoup(html, 'html.parser')

    def _filter(value):
        return (
                value
                and (
                        id_class_keywords_match_to_keep
                        and any(x in value for x in id_class_keywords_match_to_remove)
                )
                and not
                (
                        id_class_keywords_match_to_keep
                        and any(x in value for x in id_class_keywords_match_to_keep)
                )
        )

    for element in soup.find_all(id=_filter):
        element.decompose()
    for element in soup.find_all(class_=_filter):
        element.decompose()

    return soup.get_text()


# endregion

# region get sizes

def get_device_pixel_ratio(driver: WebDriver) -> int:
    return driver.execute_script("return window.devicePixelRatio")


def get_scroll_width(driver: WebDriver) -> int:
    return driver.execute_script("return document.body.parentNode.scrollWidth")


def get_scroll_height(driver: WebDriver) -> int:
    return driver.execute_script("return document.body.parentNode.scrollHeight")


def get_element_size(element: WebElement) -> Tuple[int, int]:
    """
    Gets the width and height of the given WebElement.

    Args:
        element (WebElement): The WebElement to measure.

    Returns:
        dict: A dictionary containing the width and height of the element.
    """
    size = element.size
    return size['width'], size['height']

# endregion
