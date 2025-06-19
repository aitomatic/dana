import subprocess
import sys
import requests

def _ensure_playwright_installed():
    """Ensure Playwright and its dependencies are installed."""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            # This will fail if browsers are not installed
            p.chromium.launch()
    except Exception:
        # print("Installing Playwright browsers...")
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
        # print("Playwright browsers installed successfully.")

async def fetch_web_content(url: str, enable_print: bool = False) -> str:
    """Fetch web content using Playwright."""
    try:
        _ensure_playwright_installed()
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            # Configure browser with additional arguments to appear more like a real browser
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--disable-site-isolation-trials',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu',
                    '--window-size=1920,1080',
                ]
            )
            
            # Create a new context with specific viewport and user agent
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                java_script_enabled=True,
                has_touch=True,
                locale='en-US',
                timezone_id='America/New_York',
                geolocation={'latitude': 40.7128, 'longitude': -74.0060},
                permissions=['geolocation'],
            )
            
            # Create a new page
            page = await context.new_page()
            
            # Add additional headers
            await page.set_extra_http_headers({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
            })
            
            if enable_print:
                print(f"Navigating to: {url}")
            # Navigate to the page and wait for network to be idle
            await page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Wait for Cloudflare challenge to complete
            try:
                # Wait for either the challenge to complete or timeout
                await page.wait_for_function(
                    '!document.querySelector("#challenge-running") && !document.querySelector("#challenge-stage")',
                    timeout=30000
                )
            except Exception as e:
                if enable_print:
                    print(f"Warning: Cloudflare challenge wait timed out: {e}")
            
            if enable_print:
                print(f"Page loaded: {url}")
                print("Fetching content ...")
            
            # Wait a bit more to ensure all content is loaded
            await page.wait_for_timeout(2000)
            
            # Extract text content using JavaScript
            content = await page.evaluate('''() => {
                // Remove script and style elements
                const elementsToRemove = document.querySelectorAll('script, style, nav, footer, header, iframe, noscript');
                elementsToRemove.forEach(el => el.remove());
                
                // Get text content
                const text = document.body.innerText;
                
                // Clean up the text
                return text
                    .replace(/\\s+/g, ' ')  // Replace multiple spaces with single space
                    .replace(/\\n\\s*\\n/g, '\\n')  // Replace multiple newlines with single newline
                    .trim();  // Remove leading/trailing whitespace
            }''')
            
            if enable_print:
                print(f"Content fetched: {url}")
            
            await context.close()
            await browser.close()
            return content
    except Exception as e:
        if enable_print:
            print(f"Error fetching web content: {e}")
        response = requests.get(url)
        return response.text