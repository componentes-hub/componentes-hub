import time
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from core.selenium.common import initialize_driver, close_driver
from core.environment.host import get_host_for_selenium_testing


def test_communitiestest():
    driver = initialize_driver()
    host = get_host_for_selenium_testing()

    try:
        driver.get(f"{host}/")
        driver.set_window_size(942, 933)
        
        # Login
        driver.find_element(By.LINK_TEXT, "Login").click()
        time.sleep(2)
        driver.find_element(By.ID, "email").click()
        driver.find_element(By.ID, "email").send_keys("user1@example.com")
        driver.find_element(By.ID, "password").send_keys("1234")
        driver.find_element(By.ID, "submit").click()
        time.sleep(2)
        
        # Navigate to communities
        driver.find_element(By.CSS_SELECTOR, ".hamburger").click()
        time.sleep(1)
        driver.find_element(By.CSS_SELECTOR, ".sidebar-item:nth-child(5) .align-middle:nth-child(2)").click()
        time.sleep(2)
        
        # Create community
        driver.find_element(By.LINK_TEXT, "Create Community").click()
        time.sleep(2)
        driver.find_element(By.ID, "name").click()
        driver.find_element(By.ID, "name").send_keys("comunidad de prueba")
        driver.find_element(By.ID, "description").send_keys("esta comunidad es una prueba")
        driver.find_element(By.ID, "code").send_keys("1234")
        driver.find_element(By.CSS_SELECTOR, "button:nth-child(5)").click()
        time.sleep(2)
        
        # Edit community
        driver.find_element(By.LINK_TEXT, "Edit").click()
        time.sleep(2)
        driver.find_element(By.ID, "name").click()
        driver.find_element(By.ID, "name").send_keys("comunidad actualizada")
        driver.find_element(By.ID, "description").send_keys("esta comunidad esta actualizada")
        driver.find_element(By.ID, "code").send_keys("4321")
        driver.find_element(By.CSS_SELECTOR, "button:nth-child(5)").click()
        time.sleep(2)
        
        # Delete community
        driver.find_element(By.CSS_SELECTOR, ".btn-danger").click()
        time.sleep(2)
        
        # Navigate through community sections
        driver.find_element(By.CSS_SELECTOR, ".container > div:nth-child(1)").click()
        time.sleep(1)
        driver.find_element(By.LINK_TEXT, "My Communities").click()
        time.sleep(1)
        driver.find_element(By.LINK_TEXT, "All Communities").click()
        time.sleep(1)
        driver.find_element(By.LINK_TEXT, "Doe, John").click()
        time.sleep(1)
        driver.find_element(By.LINK_TEXT, "Log out").click()
        time.sleep(1)
        
        print("Test passed!")

    except NoSuchElementException as e:
        raise AssertionError(f"Elemento no encontrado: {e}")

    finally:
        close_driver(driver)


# Call the test function
test_communitiestest()
