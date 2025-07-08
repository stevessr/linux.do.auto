import asyncio
import json
import os
import sys
import argparse
from camoufox.async_api import AsyncNewBrowser
from playwright.async_api import async_playwright

# --- CONFIGURATION ---
BASE_URL = "https://linux.do/login"
# --- END CONFIGURATION ---

async def save_cookies(page, filename):
    """Saves cookies to a file."""
    cookies = await page.context.cookies()
    with open(filename, 'w') as f:
        json.dump(cookies, f)
    print(f"Cookies saved to {filename}")

async def login_and_get_cookies(page, cookie_filename):
    """Guides the user to log in manually and saves the cookies."""
    try:
        await page.goto(BASE_URL)
    except Exception as e:
        print(f"Error navigating to {BASE_URL}: {e}")
        return

    print("Please log in manually in the browser window...")
    print("After successful login, the script will automatically detect it, save your session, and continue.")
    
    try:
        await page.wait_for_selector('header .current-user', timeout=300000) # 5 minutes timeout
        print("Login successful!")
        await save_cookies(page, cookie_filename)
    except Exception:
        print("Waited 5 minutes for login, but it was not detected. Saving cookies anyway...")
        await save_cookies(page, cookie_filename)

async def main():
    """Main function for login."""
    parser = argparse.ArgumentParser(description="Manual login script for Linux.do.")
    parser.add_argument("--cookie-file", default="cookies.json", help="Path to save the cookie file.")
    args = parser.parse_args()

    browser = None
    try:
        async with async_playwright() as p:
            print("Launching browser for you to log in.")
            browser = await AsyncNewBrowser(p, headless=False) # Always run headful for manual login
            page = await browser.new_page()
            await login_and_get_cookies(page, args.cookie_file)
            print("\nInitial setup complete. You can now run read_linuxdo.py to start reading topics automatically.")

    except Exception as e:
        print(f"An error occurred during execution: {e}")
        print("Please ensure you have installed camoufox and playwright: pip install -U camoufox[geoip] playwright")
        print("Also, run 'playwright install' to download browser binaries.")

    finally:
        if browser:
            await browser.close()
            print("Task finished, browser closed.")

if __name__ == "__main__":
    asyncio.run(main())