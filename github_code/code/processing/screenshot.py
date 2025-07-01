import subprocess
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


def screenshot_map(html_path: Path, png_path: Path, timeout: int = 20) -> None:
    """
    Render a saved Folium map HTML to a PNG image using headless Chrome.

    Args:
        html_path: Path to the saved .html map file.
        png_path: Path where the screenshot .png will be saved.
        timeout: Seconds to wait for the map container to load.

    Raises:
        Exception if Chrome fails to capture the screenshot.
    """
    # Configure headless Chrome
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1200,800")

    # Install driver silently
    service = Service(
        ChromeDriverManager().install(),
        creationflags=subprocess.CREATE_NO_WINDOW  # hide console window on Windows
    )

    # Launch Chrome and capture screenshot
    with webdriver.Chrome(service=service, options=options) as driver:
        # Load the local HTML file
        driver.get(html_path.resolve().as_uri())

        # Wait for the Leaflet container
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.leaflet-container"))
        )

        # Additional small delay to ensure tiles render
        driver.execute_script("return new Promise(r => setTimeout(r, 500));")

        # Locate the map container and screenshot
        map_div = driver.find_element(By.CSS_SELECTOR, "div.leaflet-container")
        map_div.screenshot(str(png_path))
