import time
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from core.selenium.common import initialize_driver, close_driver
from core.environment.host import get_host_for_selenium_testing


def test_view_user_profile_visual():

    driver = initialize_driver()
    host = get_host_for_selenium_testing()

    try:
        driver.get(f"{host}/")
        driver.set_window_size(602, 857)

        # Pausas opcionales para ver cada acción
        driver.find_element(By.LINK_TEXT, "Sample dataset 4").click()
        time.sleep(1)

        driver.find_element(By.LINK_TEXT, "Doe, Jane").click()
        time.sleep(1)

        driver.find_element(By.LINK_TEXT, "Sample dataset 2").click()
        time.sleep(1)

        driver.find_element(By.LINK_TEXT, "Author 2").click()
        time.sleep(1)

        driver.find_element(By.LINK_TEXT, "Sample dataset 2").click()
        time.sleep(1)

        print("Test passed!")

    except NoSuchElementException as e:
        raise AssertionError(f"Elemento no encontrado: {e}")

    finally:
        close_driver(driver)


# Call the test function
test_view_user_profile_visual()
