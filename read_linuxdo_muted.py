import asyncio
import json
import os
import sys
import argparse
from camoufox.async_api import AsyncCamoufox
from playwright.async_api import async_playwright

# --- CONFIGURATION ---
COOKIE_FILE = 'cookies.json'
READ_TOPICS_FILE = 'read_topics.json'
BASE_URL = "https://linux.do"
# --- END CONFIGURATION ---

async def load_cookies(page, filename):
    """Loads cookies from a file."""
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            cookies = json.load(f)
        await page.context.add_cookies(cookies)
        print(f"Cookies loaded from {filename}")
    else:
        print(f"Cookie file {filename} not found.")
        sys.exit(1) # Exit if cookies are not found

async def save_cookies(page, filename):
    """Saves cookies to a file."""
    cookies = await page.context.cookies()
    with open(filename, 'w') as f:
        json.dump(cookies, f, indent=2)
    print(f"Cookies automatically updated to {filename}")

def load_read_topics():
    """Loads the list of previously read topic URLs."""
    if not os.path.exists(READ_TOPICS_FILE):
        return set()
    with open(READ_TOPICS_FILE, 'r') as f:
        try:
            return set(json.load(f))
        except json.JSONDecodeError:
            return set()

def save_read_topic(topic_url):
    """Saves a topic URL as read."""
    read_topics = load_read_topics()
    read_topics.add(topic_url)
    with open(READ_TOPICS_FILE, 'w') as f:
        json.dump(list(read_topics), f, indent=2)

async def read_topic(page, topic_url):
    """Reads a single topic and sends the timings request."""
    full_topic_url = f"{BASE_URL}{topic_url}"
    print(f"Reading topic: {full_topic_url}")
    try:
        await page.goto(full_topic_url)
        await page.wait_for_selector('div.topic-body', timeout=60000)
        
        # Extract topic_id from the URL
        import re
        match = re.search(r'/t/topic/(\d+)', topic_url)
        if match:
            topic_id = match.group(1)
            print(f"Successfully extracted topic ID from URL: {topic_id}")
        else:
            print(f"Could not extract topic ID from URL: {topic_url}")
            return

        print("All posts loaded.")

        # Wait for at least one post element to be present after scrolling
        try:
            await page.wait_for_selector('div.post-stream article', timeout=60000) # Increased timeout for post elements
        except Exception as e:
            print(f"Timeout waiting for post elements: {e}")
            print(f"Could not find post numbers (found: 0) or topic ID (found: {topic_id}).")
            return

        post_elements = await page.query_selector_all('div.post-stream article')
        post_numbers = []
        for p in post_elements:
            post_number = await p.get_attribute('data-post-number')
            if not post_number:
                # Fallback to id attribute if data-post-number is not present
                post_id = await p.get_attribute('id')
                if post_id and post_id.startswith('post_'):
                    post_number = post_id.replace('post_', '')
            if post_number:
                post_numbers.append(post_number)
            print(f"Debug: Post element found. data-post-number: {await p.get_attribute('data-post-number')}, id: {await p.get_attribute('id')}, Extracted post_number: {post_number}")

        print(f"Extracted topic_id: {topic_id}, Found {len(post_numbers)} post numbers.")

        if not post_numbers or not topic_id:
            print(f"Could not find post numbers (found: {len(post_numbers)}) or topic ID (found: {topic_id}).")
            return

        print(f"Preparing to send 'timings' request for {len(post_numbers)} posts...")
        js_script = f'''
            const topic_id = {topic_id};
            const post_numbers = {json.dumps(post_numbers)};
            const timings = {{}};
            post_numbers.forEach(num => {{
                timings[num] = Math.floor(Math.random() * 1000) + 2000;
            }});

            const formData = new FormData();
            formData.append('topic_id', topic_id);
            formData.append('topic_time', Object.values(timings).reduce((a, b) => a + b, 0));
            for (const [key, value] of Object.entries(timings)) {{
                formData.append(`timings[${{key}}]`, value);
            }}

            fetch(`/t/${{topic_id}}/timings`, {{
                method: 'POST',
                body: formData,
                headers: {{
                    'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]').content
                }}
            }}).then(response => {{
                console.log('Timings request sent. Status:', response.status);
            }});
        '''
        await page.evaluate(js_script)
        await asyncio.sleep(2)
        print("Timings request sent.")
        
        save_read_topic(full_topic_url)
        print(f"Topic {full_topic_url} marked as read.")

    except Exception as e:
        print(f"An error occurred while reading topic {topic_url}: {e}")

async def main():
    """Main function for automated reading."""
    parser = argparse.ArgumentParser(description="Automated Linux.do topic reader.")
    parser.add_argument("--headful", action="store_true", help="Run browser in headful mode (visible UI).")
    parser.add_argument("--cookie-file", default="cookies.json", help="Path to the cookie file.")
    args = parser.parse_args()

    try:
        async with async_playwright() as p:
            print("Setting up browser...")
            async with AsyncCamoufox(headless=not args.headful) as browser:
                page = await browser.new_page()
                await load_cookies(page, args.cookie_file)
                await page.goto(f"{BASE_URL}/c/muted/45/l/unseen", timeout=60000) # Visit again to apply cookies
            
                try:
                    await page.wait_for_selector('header .current-user', timeout=20000)
                    print("Successfully logged in using cookies.")
                except Exception:
                    print("Cookies might be expired or invalid. Please delete cookies.json and run login_linuxdo.py again to log in.")
                    sys.exit(1)

                read_topics = load_read_topics()
                print(f"Loaded {len(read_topics)} previously read topics: {read_topics}")

                await page.goto(f"{BASE_URL}/c/muted/45/l/unseen") # Ensure we are on the unseen topics page to get topic list
                await page.wait_for_selector('tbody .topic-list-item', timeout=30000)
                
                topic_elements = await page.query_selector_all('tbody .topic-list-item a.title.raw-link.raw-topic-link')
                topic_urls = [await elem.get_attribute('href') for elem in topic_elements]
                print(f"Found {len(topic_urls)} topic URLs on the page: {topic_urls}")
                
                new_topics = [url for url in topic_urls if url not in read_topics]
                print(f"Filtered {len(new_topics)} new topics: {new_topics}")
                print(f"Filtered {len(new_topics)} new topics: {new_topics}")

                if not new_topics:
                    print("No new topics found.")
                else:
                    print(f"Found {len(new_topics)} new topics. Starting to read...")
                    for url in new_topics:
                        await read_topic(page, url)
                        await asyncio.sleep(5)
                
                await save_cookies(page, args.cookie_file)

    except Exception as e:
        print(f"An error occurred during execution: {e}")
        print("Please ensure you have installed camoufox and playwright: pip install -U camoufox[geoip] playwright")
        print("Also, run 'playwright install' to download browser binaries.")


if __name__ == "__main__":
    asyncio.run(main())