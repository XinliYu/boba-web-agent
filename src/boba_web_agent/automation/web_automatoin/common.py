from enum import Enum
from typing import List, Union, Mapping, Any, Optional

import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.service import Service
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.remote.webelement import WebElement
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager

DEFAULT_USER_AGENT_STRING = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"


class WebAutomationDrivers(str, Enum):
    Firefox = 'firefox'
    Chrome = 'chrome'
    UndetectedChrome = 'undetected_chrome'
    Edge = 'edge'
    Safari = 'safari'


def get_driver(
        driver_type: WebAutomationDrivers = WebAutomationDrivers.Firefox,
        headless: bool = True,
        user_agent: str = None,
        timeout: int = 120,
        options: List[str] = None
) -> Union[
    webdriver.Firefox,
    webdriver.Chrome,
    webdriver.Edge,
    webdriver.Safari
]:
    """
    Initializes and returns a webdriver instance configured for the specified browser type with optional settings.

    Args:
        driver_type (WebAutomationDrivers, optional): Specifies the type of web driver to initialize. Default is WebAutomationDrivers.Firefox.
        headless (bool, optional): If True, the browser is run in headless mode, meaning it will not display any UI. Default is True.
        user_agent (bool, optional): If True, sets the browser's user-agent to a predefined default string. Default is True.
        timeout (int, optional): The time in seconds to wait for a page to be loaded before raising a timeout error. Default is 30 seconds.
        options (List[str], optional): Additional browser-specific options to be added to the browser on startup.

    Returns:
        webdriver: An instance of a Selenium WebDriver configured for the specified browser with the provided options.

    Raises:
        ValueError: If an unsupported driver type is specified.

    Examples:
        # Get a headless Firefox driver with default settings
        driver = get_driver()

        # Get a Chrome driver with custom options
        custom_options = ["--disable-extensions", "--disable-gpu"]
        driver = get_driver(driver_type=WebAutomationDrivers.Chrome, options=custom_options)
    """

    if driver_type == WebAutomationDrivers.Firefox:
        webdriver_service = FirefoxService(GeckoDriverManager().install())
        _options = FirefoxOptions()
        driver_class = webdriver.Firefox
    elif driver_type == WebAutomationDrivers.Chrome:
        webdriver_service = ChromeService(ChromeDriverManager(version='latest').install())
        _options = ChromeOptions()
        driver_class = webdriver.Chrome
    elif driver_type == WebAutomationDrivers.UndetectedChrome:
        webdriver_service = None
        _options = uc.ChromeOptions()
        driver_class = uc.Chrome
    elif driver_type == WebAutomationDrivers.Edge:
        webdriver_service = Service(EdgeChromiumDriverManager().install())
        _options = ChromeOptions()  # Edge uses Chrome options
        driver_class = webdriver.Edge
    elif driver_type == WebAutomationDrivers.Safari:
        webdriver_service = None  # Safari doesn't require a separate service
        _options = None  # Safari doesn't use options in the same way
        driver_class = webdriver.Safari
    else:
        raise ValueError(f"Unsupported driver: {driver_type}")

    if isinstance(_options, ChromeOptions):
        _options.add_experimental_option("excludeSwitches", ["enable-automation"])
        _options.add_experimental_option('useAutomationExtension', False)
        _options.add_argument("--disable-blink-features=AutomationControlled")

    if _options is not None:
        if headless:
            # Headless browsers consume fewer resources since they do not need to render graphics or manage user interface elements.
            _options.add_argument("--headless")
        if user_agent:
            # The Webdriver is best tested for this default user-agent string.
            _options.add_argument(DEFAULT_USER_AGENT_STRING if user_agent == 'default' else user_agent)
        if options:
            for option in options:
                _options.add_argument(option)

    driver = driver_class(service=webdriver_service, options=_options)
    driver.set_page_load_timeout(timeout)
    return driver


class WebDriver:
    """
    A class to manage the creation of WebDriver instances for different browsers with configurable options.
    """

    def __init__(self, driver_type: WebAutomationDrivers = WebAutomationDrivers.Firefox,
                 headless: bool = True, user_agent: str = None,
                 timeout: int = 120, options: List[str] = None):
        """
        Initializes a WebDriver instance with the specified configuration upon creation of the class instance.

        Args:
            driver_type (WebAutomationDrivers): The type of browser for the WebDriver. Default is Firefox.
            headless (bool): Whether to run the browser in headless mode. Default is True.
            user_agent (bool): Whether to use a default user-agent string. Default is True.
            timeout (int): The maximum time to wait for a page to load. Default is 30 seconds.
            options (List[str]): Additional browser-specific options to set. Default is None.
        """

        # Instantiate the driver using the provided configuration
        self.driver = get_driver(
            driver_type=driver_type,
            headless=headless,
            user_agent=user_agent,
            timeout=timeout,
            options=options
        )

    def open_url(self, url: str = None, wait_after_opening_url: float = 0):
        from boba_web_agent.automation.web_automatoin.selenium_web_driver_utils import open_url
        return open_url(
            driver=self.driver,
            url=url,
            wait_after_opening_url=wait_after_opening_url
        )

    def get_body_html_from_url(self, url: str = None, initial_wait: float = 0, timeout_for_page_loading: int = 20, return_dynamic_contents: bool = True):
        from boba_web_agent.automation.web_automatoin.selenium_web_driver_utils import get_body_html_from_url
        return get_body_html_from_url(
            driver=self.driver,
            url=url,
            initial_wait_after_opening_url=initial_wait,
            timeout_for_page_loading=timeout_for_page_loading,
            return_dynamic_contents=return_dynamic_contents
        )

    def get_body_html(self, return_dynamic_contents: bool = True) -> str:
        from boba_web_agent.automation.web_automatoin.selenium_web_driver_utils import get_body_html
        return get_body_html(
            driver=self.driver,
            return_dynamic_contents=return_dynamic_contents
        )

    def get_element_html(self, element) -> str:
        from boba_web_agent.automation.web_automatoin.selenium_web_driver_utils import get_element_html
        return get_element_html(element=element)

    def wait_for_page_loading(self, timeout: int = 30, extra_wait_min=1, extra_wait_max=5):
        from boba_web_agent.automation.web_automatoin.selenium_web_driver_utils import wait_for_page_loading
        wait_for_page_loading(self.driver, timeout=timeout)
        import random
        from time import sleep
        sleep(random.uniform(extra_wait_min, extra_wait_max))

    def find_element_by_xpath(
            self,
            tag_name: Optional[str] = '*',
            attributes: Mapping[str, Any] = None,
            text: str = None,
            immediate_text: str = None
    ):
        from boba_web_agent.automation.web_automatoin.selenium_web_driver_utils import find_element_by_xpath
        return find_element_by_xpath(
            driver=self.driver,
            tag_name=tag_name,
            attributes=attributes,
            text=text,
            immediate_text=immediate_text
        )

    def find_elements_by_xpath(
            self,
            tag_name: Optional[str] = '*',
            attributes: Mapping[str, Any] = None,
            text: str = None,
            immediate_text: str = None
    ):
        from boba_web_agent.automation.web_automatoin.selenium_web_driver_utils import find_elements_by_xpath
        return find_elements_by_xpath(
            driver=self.driver,
            tag_name=tag_name,
            attributes=attributes,
            text=text,
            immediate_text=immediate_text
        )

    def find_element_by_html(self, target_element_html, identifying_attributes=('id', 'aria-label', 'class'), always_return_single_element: bool = False):
        from boba_web_agent.automation.web_automatoin.selenium_web_driver_utils import find_element_by_html
        return find_element_by_html(
            driver=self.driver,
            target_element_html=target_element_html,
            identifying_attributes=identifying_attributes,
            always_return_single_element=always_return_single_element
        )

    def capture_full_page_screenshot(self, output_path):
        from boba_web_agent.automation.web_automatoin.selenium_web_driver_utils import capture_full_page_screenshot
        capture_full_page_screenshot(
            driver=self.driver,
            output_path=output_path
        )

    def execute_single_action(self, element: WebElement, action_name: str, action_args: Mapping = None):
        from boba_web_agent.automation.web_automatoin.selenium_web_driver_utils import execute_single_action
        execute_single_action(
            driver=self.driver,
            element=element,
            action_name=action_name,
            action_args=action_args
        )

    def execute_actions(self, actions: Mapping, output_path_action_records: str = None):
        from boba_web_agent.automation.web_automatoin.selenium_web_driver_utils import execute_actions
        execute_actions(
            driver=self.driver,
            actions=actions,
            output_path_action_records=output_path_action_records
        )
