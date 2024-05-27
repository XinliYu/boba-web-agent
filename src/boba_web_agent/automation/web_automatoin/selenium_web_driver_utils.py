import time
from typing import List, Optional, Mapping, Any

from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait

from boba_python_utils.io_utils.text_io import write_all_text
from boba_web_agent.automation.web_automatoin.html_utils import get_xpath, get_tag_text_and_attributes_from_element_html
from boba_python_utils.common_utils.map_helper import promote_keys
from boba_python_utils.general_utils.console_util import hprint_message
from boba_python_utils.io_utils.json_io import write_json_objs
from boba_python_utils.path_utils.common import ensure_dir_existence
from boba_python_utils.time_utils.common import random_sleep
from os import path


# region page loading & status
def get_ready_state(driver: WebDriver):
    return driver.execute_script("return document.readyState")


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
def get_element_html(element: WebElement) -> str:
    return element.get_attribute("outerHTML")


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


def find_element_by_xpath(
        driver,
        tag_name: Optional[str] = '*',
        attributes: Mapping[str, Any] = None,
        text: str = None,
        immediate_text: str = None
):
    xpath = get_xpath(
        tag_name=tag_name,
        attributes=attributes,
        text=text,
        immediate_text=immediate_text
    )
    return driver.find_element(By.XPATH, xpath)


def find_elements_by_xpath(
        driver,
        tag_name: Optional[str] = '*',
        attributes: Mapping[str, Any] = None,
        text: str = None,
        immediate_text: str = None
):
    xpath = get_xpath(
        tag_name=tag_name,
        attributes=attributes,
        text=text,
        immediate_text=immediate_text
    )
    return driver.find_elements(By.XPATH, xpath)


# region html locating
def find_element_by_html(driver, target_element_html: str, identifying_attributes=('id', 'aria-label', 'class'), always_return_single_element: bool = False):
    """
    Finds an element by an HTML snippet, using a combination of tag name, text content, and attributes.
    The function first tries to find elements by tag name and text. If multiple elements are found,
    it progressively filters these elements by their attributes until one unique element remains or
    no elements match the criteria.

    This approach is useful when an element's identification requires more than a simple selector,
    and when precision is needed to single out an element among many with similar attributes.

    Args:
        driver: A Selenium WebDriver instance used to interact with the web page.
        target_element_html: A string representing an HTML snippet of the target element.

    Returns:
        The first web element that uniquely matches the generated criteria or None if no such element is found.
    """
    tag_name, text, attributes = get_tag_text_and_attributes_from_element_html(target_element_html)
    elements = find_elements_by_xpath(driver=driver, tag_name=tag_name, text=text)

    if len(elements) == 1:
        return elements[0]
    elif not elements:
        elements = find_elements_by_xpath(driver=driver, tag_name=tag_name)
        if len(elements) == 1:
            return elements[0]
        elif not elements:
            return None

    attributes = promote_keys(attributes, keys_to_promote=identifying_attributes)

    for attr, target_attr_values in attributes.items():
        if isinstance(target_attr_values, str):
            target_attr_values = target_attr_values.split()
        elem_attr_values = []
        for elem in elements:
            values = elem.get_attribute(attr)
            if values is not None:
                elem_attr_values.append((elem, values.split()))

        if len(elem_attr_values) == 1:
            return elem_attr_values[0][0]
        elif len(elem_attr_values) == 0:
            return None

        _elem_attr_values = elem_attr_values
        for single_target_attr_value in target_attr_values:
            _elem_attr_values = [
                (elem, attr_values) for elem, attr_values in _elem_attr_values
                if single_target_attr_value in attr_values
            ]
            if len(_elem_attr_values) == 1:
                return _elem_attr_values[0][0]
            elif len(_elem_attr_values) == 0:
                if attr in identifying_attributes:
                    return None
                else:
                    break
        if _elem_attr_values:
            elem_attr_values = _elem_attr_values

        elements = [elem for elem, attr_values in elem_attr_values]

    if always_return_single_element:
        return elements[0]
    else:
        return elements


# endregion


# region action execution
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


def capture_full_page_screenshot(driver, output_path):
    original_size = driver.get_window_size()
    total_width = driver.execute_script('return document.body.parentNode.scrollWidth')
    total_height = driver.execute_script('return document.body.parentNode.scrollHeight')
    driver.set_window_size(total_width, total_height)
    time.sleep(2)
    screenshot = driver.get_screenshot_as_png()
    with open(output_path, "wb") as file:
        file.write(screenshot)
    driver.set_window_size(original_size['width'], original_size['height'])
    time.sleep(2)


def execute_single_action(driver: WebDriver, element: WebElement, action_name: str, action_args: Mapping = None):
    if action_name == 'click':
        element.click()
    elif action_name == 'input_text':
        send_keys_with_random_delay(element, **action_args)
    elif action_name == 'open_url':
        driver.open_url(**action_args)
    driver.wait_for_page_loading()


def execute_actions(driver: WebDriver, actions: Mapping, output_path_action_records: str = None):
    if output_path_action_records:
        action_target_found_records = []

    for action_index, action in enumerate(actions):
        if output_path_action_records:
            output_path_action_root = ensure_dir_existence(
                path.join(output_path_action_records, f'action_{action_index}')
            )
            action_records_jobj = {'action_index': action_index}

        action_name = action['name']
        action_target = action.get('target', None)
        action_args = action.get('args', None)
        action_repeat = action.get('repeat', 1)

        for action_repeat_index in range(action_repeat):
            if output_path_action_records:
                output_path_html_before_action = path.join(output_path_action_root, f'html_before_action-{action_repeat_index}.html')
                write_all_text(output_path_html_before_action, driver.get_body_html(return_dynamic_contents=True))
                output_path_screenshot_before_action = path.join(output_path_action_root, f'screenshot_before_action-{action_repeat_index}.png')
                driver.capture_full_page_screenshot(output_path_screenshot_before_action)

            if action_target:
                for each_action_target in action_target:
                    elem = driver.find_element_by_html(each_action_target, always_return_single_element=True)
                    if elem is not None and output_path_action_records:
                        _action_records_jobj = action_records_jobj.copy()
                        _action_records_jobj['action_repeat_index'] = action_repeat_index
                        _action_records_jobj['action_target_found'] = driver.get_element_html(elem)
                        action_target_found_records.append(_action_records_jobj)
                    execute_single_action(driver, elem, action_name, action_args)
            else:
                execute_single_action(driver, None, action_name, action_args)
            random_sleep(0.3, 2)

    if output_path_action_records:
        write_json_objs(action_target_found_records, path.join(output_path_action_root, 'action_target_found_records.jsonl'))
# endregion
