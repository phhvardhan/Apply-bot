'''
Auto Job Applier for LinkedIn - Clickers and finders
License: GNU AGPL-3.0
'''

from config.settings import click_gap, smooth_scroll
from modules.helpers import buffer, print_lg, sleep
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.action_chains import ActionChains

# Click Functions
def wait_span_click(driver: WebDriver, text: str, time: float=5.0, click: bool=True, scroll: bool=True, scrollTop: bool=False, scope: WebElement = None) -> WebElement | bool:
    '''
    Finds the span element with the given `text`.
    - Returns `WebElement` if found, else `False` if not found.
    - Clicks on it if `click = True`.
    - Will spend a max of `time` seconds in searching for each element.
    - Will scroll to the element if `scroll = True`.
    - Will scroll to the top if `scrollTop = True`.
    - If `scope` is provided, searches only within that element (e.g. filter panel).
    '''
    if text:
        try:
            xpath = './/span[normalize-space(.)="'+text+'"]'
            if scope is not None:
                import time as time_module
                deadline = time_module.time() + time
                button = None
                while time_module.time() < deadline:
                    try:
                        button = scope.find_element(By.XPATH, xpath)
                        break
                    except Exception:
                        sleep(0.2)
                if button is None:
                    raise Exception("Not found in scope")
            else:
                button = WebDriverWait(driver, time).until(EC.presence_of_element_located((By.XPATH, xpath)))
            if scroll:  scroll_to_view(driver, button, scrollTop)
            if click:
                button.click()
                buffer(click_gap)
            return button
        except Exception as e:
            print_lg("Click Failed! Didn't find '"+text+"'")
            # print_lg(e)
            return False

def multi_sel(driver: WebDriver, texts: list, time: float=5.0) -> None:
    '''
    - For each text in the `texts`, tries to find and click `span` element with that text.
    - Will spend a max of `time` seconds in searching for each element.
    '''
    for text in texts:
        ##> ------ Dheeraj Deshwal : dheeraj20194@iiitd.ac.in/dheerajdeshwal9811@gmail.com - Bug fix ------
        wait_span_click(driver, text, time, False)
        ##<
        try:
            button = WebDriverWait(driver,time).until(EC.presence_of_element_located((By.XPATH, './/span[normalize-space(.)="'+text+'"]')))
            scroll_to_view(driver, button)
            button.click()
            buffer(click_gap)
        except Exception as e:
            print_lg("Click Failed! Didn't find '"+text+"'")
            # print_lg(e)

def multi_sel_noWait(driver: WebDriver, texts: list, actions: ActionChains = None, scope: WebElement = None) -> None:
    '''
    - For each text in the `texts`, tries to find and click `span` element with that text.
    - If `actions` is provided, bot tries to search and Add the `text` to this filters list section.
    - Won't wait to search for each element, assumes that element is rendered.
    - If `scope` is provided, searches only within that element (e.g. filter panel).
    '''
    if not texts:
        return
    root = scope if scope is not None else driver
    for text in texts:
        try:
            button = root.find_element(By.XPATH, './/span[normalize-space(.)="'+text+'"]')
            scroll_to_view(driver, button)
            button.click()
            buffer(click_gap)
        except Exception as e:
            if actions: company_search_click(driver, actions, text)
            else:   print_lg("Click Failed! Didn't find '"+text+"'")
            # print_lg(e)

def boolean_button_click(driver: WebDriver, actions: ActionChains, text: str, scope: WebElement = None) -> None:
    '''
    Tries to click on the boolean button with the given `text` text.
    - If `scope` is provided, searches only within that element (e.g. filter panel).
    '''
    root = scope if scope is not None else driver
    try:
        list_container = root.find_element(By.XPATH, './/h3[normalize-space()="'+text+'"]/ancestor::fieldset')
        button = list_container.find_element(By.XPATH, './/input[@role="switch"]')
        scroll_to_view(driver, button)
        actions.move_to_element(button).click().perform()
        buffer(click_gap)
    except Exception as e:
        print_lg("Click Failed! Didn't find '"+text+"'")
        # print_lg(e)


def expand_filter_section(driver: WebDriver, section_title: str, scope: WebElement = None) -> bool:
    '''
    Tries to expand a filter section (e.g. "Date posted", "Experience level", "Job type")
    by clicking its header. Returns True if a click was performed.
    '''
    root = scope if scope is not None else driver
    for xpath in [
        './/button[contains(., "' + section_title + '")]',
        './/*[@role="button" and contains(., "' + section_title + '")]',
        './/h3[contains(., "' + section_title + '")]',
        './/legend[contains(., "' + section_title + '")]',
        './/div[contains(@class, "filter") and contains(., "' + section_title + '")]//button',
        './/fieldset[.//*[contains(., "' + section_title + '")]]//button[1]',
        './/*[@aria-label and contains(., "' + section_title + '")]',
    ]:
        try:
            elem = root.find_element(By.XPATH, xpath)
            scroll_to_view(driver, elem)
            elem.click()
            buffer(click_gap)
            sleep(0.3)
            return True
        except Exception:
            continue
    return False


def click_filter_option(driver: WebDriver, option_text: str, scope: WebElement = None) -> bool:
    '''
    Tries multiple strategies to click a filter option (e.g. "Past 24 hours", "Full-time", "Associate").
    Works when the option is in a span, label, div, or button. Returns True if clicked.
    '''
    if not option_text:
        return False
    root = scope if scope is not None else driver
    # Escape quotes in option_text for XPath (replace " with ')
    safe_text = option_text.replace('"', "'")
    xpaths = [
        './/span[normalize-space(.)="' + safe_text + '"]',
        './/label[normalize-space(.)="' + safe_text + '"]',
        './/*[normalize-space(.)="' + safe_text + '" and (self::span or self::label or self::div or self::button or self::a or self::li)]',
        './/span[contains(normalize-space(.), "' + safe_text + '")]',
        './/label[contains(normalize-space(.), "' + safe_text + '")]',
        './/*[@role="option" and (normalize-space(.)="' + safe_text + '" or contains(., "' + safe_text + '"))]',
        './/*[@role="menuitem" and (normalize-space(.)="' + safe_text + '" or contains(., "' + safe_text + '"))]',
        './/label[contains(., "' + safe_text + '")]',
        './/li[contains(., "' + safe_text + '")]',
    ]
    for xpath in xpaths:
        try:
            elem = root.find_element(By.XPATH, xpath)
            scroll_to_view(driver, elem)
            elem.click()
            buffer(click_gap)
            return True
        except Exception:
            continue
    print_lg("Click Failed! Didn't find filter option '" + option_text + "'")
    return False


def multi_sel_filter_options(driver: WebDriver, texts: list, actions: ActionChains = None, scope: WebElement = None) -> None:
    '''
    For each text in texts, clicks the filter option using flexible matching (span/label/div/etc).
    If actions is provided and click fails, falls back to company_search_click for company filter.
    '''
    if not texts:
        return
    for text in texts:
        if click_filter_option(driver, text, scope):
            continue
        if actions and scope is not None:
            company_search_click(driver, actions, text)
        else:
            print_lg("Click Failed! Didn't find '" + text + "'")

# Find functions
def find_by_class(driver: WebDriver, class_name: str, time: float=5.0) -> WebElement | Exception:
    '''
    Waits for a max of `time` seconds for element to be found, and returns `WebElement` if found, else `Exception` if not found.
    '''
    return WebDriverWait(driver, time).until(EC.presence_of_element_located((By.CLASS_NAME, class_name)))

# Scroll functions
def scroll_to_view(driver: WebDriver, element: WebElement, top: bool = False, smooth_scroll: bool = smooth_scroll) -> None:
    '''
    Scrolls the `element` to view.
    - `smooth_scroll` will scroll with smooth behavior.
    - `top` will scroll to the `element` to top of the view.
    '''
    if top:
        return driver.execute_script('arguments[0].scrollIntoView();', element)
    behavior = "smooth" if smooth_scroll else "instant"
    return driver.execute_script('arguments[0].scrollIntoView({block: "center", behavior: "'+behavior+'" });', element)

# Enter input text functions
def text_input_by_ID(driver: WebDriver, id: str, value: str, time: float=5.0) -> None | Exception:
    '''
    Enters `value` into the input field with the given `id` if found, else throws NotFoundException.
    - `time` is the max time to wait for the element to be found.
    '''
    username_field = WebDriverWait(driver, time).until(EC.presence_of_element_located((By.ID, id)))
    username_field.send_keys(Keys.CONTROL + "a")
    username_field.send_keys(value)

def try_xp(driver: WebDriver, xpath: str, click: bool=True) -> WebElement | bool:
    try:
        if click:
            driver.find_element(By.XPATH, xpath).click()
            return True
        else:
            return driver.find_element(By.XPATH, xpath)
    except: return False

def try_linkText(driver: WebDriver, linkText: str) -> WebElement | bool:
    try:    return driver.find_element(By.LINK_TEXT, linkText)
    except:  return False

def try_find_by_classes(driver: WebDriver, classes: list[str]) -> WebElement | ValueError:
    for cla in classes:
        try:    return driver.find_element(By.CLASS_NAME, cla)
        except: pass
    raise ValueError("Failed to find an element with given classes")

def company_search_click(driver: WebDriver, actions: ActionChains, companyName: str) -> None:
    '''
    Tries to search and Add the company to company filters list.
    '''
    wait_span_click(driver,"Add a company",1)
    search = driver.find_element(By.XPATH,"(.//input[@placeholder='Add a company'])[1]")
    search.send_keys(Keys.CONTROL + "a")
    search.send_keys(companyName)
    buffer(3)
    actions.send_keys(Keys.DOWN).perform()
    actions.send_keys(Keys.ENTER).perform()
    print_lg(f'Tried searching and adding "{companyName}"')

def text_input(actions: ActionChains, textInputEle: WebElement | bool, value: str, textFieldName: str = "Text") -> None | Exception:
    if textInputEle:
        sleep(1)
        # actions.key_down(Keys.CONTROL).send_keys("a").key_up(Keys.CONTROL).perform()
        textInputEle.clear()
        textInputEle.send_keys(value.strip())
        sleep(2)
        actions.send_keys(Keys.ENTER).perform()
    else:
        print_lg(f'{textFieldName} input was not given!')