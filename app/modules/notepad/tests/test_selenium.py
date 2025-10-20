from selenium.common.exceptions import NoSuchElementException
import time

from core.environment.host import get_host_for_selenium_testing
from core.selenium.common import initialize_driver, close_driver

from selenium import webdriver
from selenium.webdriver.common.by import By


def test_notepad_index():

    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()

        # Open the index page
        driver.get(f'{host}/notepad')

        # Wait a little while to make sure the page has loaded completely
        time.sleep(4)

        try:

            pass

        except NoSuchElementException:
            raise AssertionError('Test failed!')

    finally:

        # Close the browser
        close_driver(driver)


def test_notepadcreate():
    driver = initialize_driver()
    host = get_host_for_selenium_testing()
    
    driver.get(f'{host}/login?next=%2Fnotepad')
    driver.set_window_size(706, 923)
    driver.find_element(By.ID, "email").click()
    driver.find_element(By.ID, "email").send_keys("user1@example.com")
    driver.find_element(By.ID, "password").click()
    driver.find_element(By.ID, "password").send_keys("1234")
    driver.find_element(By.ID, "submit").click()
    driver.get(f'{host}/notepad/create')
    driver.find_element(By.CSS_SELECTOR, "form > div:nth-child(3)").click()
    driver.find_element(By.ID, "title").click()
    driver.find_element(By.ID, "title").send_keys("Prueba")
    driver.find_element(By.ID, "body").click()
    driver.find_element(By.ID, "body").send_keys("Prueba")
    driver.find_element(By.CSS_SELECTOR, ".content").click()
    driver.find_element(By.ID, "submit").click()
    
    close_driver(driver)


# Call the test function
test_notepad_index()
test_notepadcreate()
