from selenium.common.exceptions import NoSuchElementException
import time

from core.environment.host import get_host_for_selenium_testing
from core.selenium.common import initialize_driver, close_driver

from selenium.webdriver.common.by import By


def test_componentes_check_index():

    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()

        # Request a file id that (very likely) does not exist in the test DB
        driver.get(f'{host}/componentes_check/check_comp/999999')

        # Small wait to ensure response loads
        time.sleep(2)

        try:
            # The route returns JSON; when the file is not found it returns an errors array
            page = driver.page_source
            assert "El archivo no existe." in page or '"errors"' in page, 'Expected not-found message or errors key in response'

        except NoSuchElementException:
            raise AssertionError('Test failed!')

    finally:

        # Close the browser
        close_driver(driver)


def test_componentes_check_errors_key():
    """Checks response contains the JSON 'errors' key when file is missing."""

    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()

        driver.get(f'{host}/componentes_check/check_comp/999999')
        time.sleep(2)

        page = driver.page_source
        # Check that JSON structure is present (page_source will show the raw JSON)
        assert '"errors"' in page or 'errors' in page, 'Response does not contain errors key'

    finally:
        close_driver(driver)


if __name__ == "__main__":
    # When executed as a module (how `rosemary selenium` runs it), execute tests
    try:
        test_componentes_check_index()
        test_componentes_check_errors_key()
    except Exception:
        import traceback
        import sys

        traceback.print_exc()
        sys.exit(1)
