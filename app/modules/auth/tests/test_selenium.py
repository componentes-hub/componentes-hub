import time
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from core.selenium.common import initialize_driver, close_driver
from core.environment.host import get_host_for_selenium_testing


def test_login_and_check_active_sessions():
    """Inicia sesión y comprueba las sesiones activas"""
    driver = initialize_driver()
    host = get_host_for_selenium_testing()

    try:
        # Open main page
        driver.get(f"{host}/")
        driver.set_window_size(942, 971)
        time.sleep(2)
        
        # Perform login
        driver.find_element(By.LINK_TEXT, "Login").click()
        time.sleep(2)
        driver.find_element(By.ID, "email").send_keys("user1@example.com")
        driver.find_element(By.ID, "password").send_keys("1234")
        driver.find_element(By.ID, "submit").click()
        time.sleep(2)
        
        # Navigate to sessions
        driver.find_element(By.CSS_SELECTOR, ".hamburger").click()
        time.sleep(1)
        driver.find_element(By.LINK_TEXT, "Sessions").click()
        time.sleep(2)
        
        # Verify that it is possible to navigate through the sessions
        driver.find_element(By.LINK_TEXT, "Doe, John").click()
        time.sleep(1)
        
        # Close session
        driver.find_element(By.LINK_TEXT, "Log out").click()
        time.sleep(1)
        
        print("Test passed!")

    except NoSuchElementException as e:
        raise AssertionError(f"Elemento no encontrado: {e}")

    finally:
        close_driver(driver)


# Call the test function
test_login_and_check_active_sessions()
