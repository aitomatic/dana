import asyncio
import subprocess
import sys

import requests


def _ensure_playwright_installed():
    """Ensure Playwright and its dependencies are installed."""
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch()
            browser.close()  # Properly close the browser to avoid resource leaks
    except Exception:
        # print("Installing Playwright browsers...")
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
        # print("Playwright browsers installed successfully.")


async def fetch_web_content(url: str, enable_print: bool = False) -> str:
    """Fetch web content using Playwright with enhanced stealth and retry logic."""
    max_retries = 3

    for attempt in range(max_retries):
        try:
            _ensure_playwright_installed()
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                # Enhanced browser configuration with better stealth
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--disable-features=VizDisplayCompositor",
                        "--disable-background-timer-throttling",
                        "--disable-backgrounding-occluded-windows",
                        "--disable-renderer-backgrounding",
                        "--disable-field-trial-config",
                        "--disable-hang-monitor",
                        "--disable-ipc-flooding-protection",
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-accelerated-2d-canvas",
                        "--no-first-run",
                        "--no-zygote",
                        "--disable-gpu",
                        "--window-size=1920,1080",
                        "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                    ],
                )

                # Create a new context with enhanced stealth settings
                context = await browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                    java_script_enabled=True,
                    has_touch=True,
                    locale="en-US",
                    timezone_id="America/New_York",
                    geolocation={"latitude": 40.7128, "longitude": -74.0060},
                    permissions=["geolocation"],
                    extra_http_headers={
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
                        "Accept-Language": "en-US,en;q=0.9",
                        "Accept-Encoding": "gzip, deflate, br",
                        "DNT": "1",
                        "Connection": "keep-alive",
                        "Upgrade-Insecure-Requests": "1",
                        "Sec-Fetch-Dest": "document",
                        "Sec-Fetch-Mode": "navigate",
                        "Sec-Fetch-Site": "none",
                        "Sec-Fetch-User": "?1",
                        "Cache-Control": "max-age=0",
                    },
                )

                # Create a new page
                page = await context.new_page()

                # Add enhanced stealth script
                await page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined,
                    });
                    
                    window.chrome = {
                        runtime: {},
                    };
                    
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['en-US', 'en'],
                    });
                    
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5],
                    });
                    
                    // Override the permissions API
                    const originalQuery = window.navigator.permissions.query;
                    window.navigator.permissions.query = (parameters) => (
                        parameters.name === 'notifications' ?
                            Promise.resolve({ state: Notification.permission }) :
                            originalQuery.call(window.navigator.permissions, parameters)
                    );
                    
                    // Mock plugins
                    Object.defineProperty(navigator, 'mimeTypes', {
                        get: () => [1, 2, 3, 4],
                    });
                """)

                if enable_print:
                    print(f"Attempt {attempt + 1}: Navigating to: {url}")

                # Navigate with domcontentloaded instead of networkidle for faster loading
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)

                # Wait for body to have substantial content
                await page.wait_for_function("document.body && document.body.innerText.length > 100", timeout=30000)

                # Enhanced Cloudflare challenge detection and handling
                try:
                    # Wait for Cloudflare challenges to complete with better detection
                    await page.wait_for_function(
                        """() => {
                            // Check for various Cloudflare challenge indicators
                            const cfSelectors = [
                                '[data-ray]',
                                '.cf-browser-verification',
                                '.cf-checking-browser',
                                'div[class*="challenge"]',
                                'div[id*="challenge"]'
                            ];
                            
                            const hasChallenge = cfSelectors.some(selector => {
                                const element = document.querySelector(selector);
                                return element && element.offsetParent !== null;
                            });
                            
                            // Also check for "Just a moment" text
                            const bodyText = document.body.innerText.toLowerCase();
                            const hasJustAMoment = bodyText.includes('just a moment') || 
                                                 bodyText.includes('checking your browser') ||
                                                 bodyText.includes('enable javascript and cookies');
                            
                            // Return true if no challenge is detected
                            return !hasChallenge && !hasJustAMoment;
                        }""",
                        timeout=45000,
                    )

                    if enable_print:
                        print("Cloudflare challenge completed successfully")

                except Exception as e:
                    if enable_print:
                        print(f"Warning: Cloudflare challenge wait timed out: {e}")
                    # Add additional wait time for challenge to complete
                    await page.wait_for_timeout(10000)

                if enable_print:
                    print(f"Page loaded: {url}")
                    print("Fetching content...")

                # Wait a bit more to ensure all dynamic content is loaded
                await page.wait_for_timeout(3000)

                # Check if we're still on a Cloudflare challenge page
                page_content = await page.content()
                if "just a moment" in page_content.lower() or "checking your browser" in page_content.lower():
                    if enable_print:
                        print("Still on Cloudflare challenge page, waiting longer...")
                    await page.wait_for_timeout(15000)

                # Extract text content using enhanced JavaScript
                content = await page.evaluate("""() => {
                    // Remove unwanted elements
                    const elementsToRemove = document.querySelectorAll(
                        'script, style, nav, footer, header, iframe, noscript, .advertisement, .ads, [class*="ad-"], [id*="ad-"]'
                    );
                    elementsToRemove.forEach(el => el.remove());
                    
                    // Get main content areas first
                    const mainSelectors = ['main', '[role="main"]', '.main-content', '#main', '.content'];
                    let mainContent = '';
                    
                    for (const selector of mainSelectors) {
                        const element = document.querySelector(selector);
                        if (element) {
                            mainContent = element.innerText;
                            break;
                        }
                    }
                    
                    // Fallback to body if no main content found
                    const text = mainContent || document.body.innerText;
                    
                    // Enhanced text cleaning
                    return text
                        .replace(/\\s+/g, ' ')  // Replace multiple spaces with single space
                        .replace(/\\n\\s*\\n/g, '\\n')  // Replace multiple newlines with single newline
                        .replace(/[\\u00A0\\u2000-\\u200B\\u2028\\u2029\\u202F\\u205F\\u3000]/g, ' ')  // Replace various unicode spaces
                        .trim();  // Remove leading/trailing whitespace
                }""")

                if enable_print:
                    print(f"Content fetched successfully: {len(content)} characters")

                await context.close()
                await browser.close()

                # Verify we got meaningful content
                if len(content.strip()) < 50:
                    raise Exception("Content too short, likely still on challenge page")

                return content

        except Exception as e:
            if enable_print:
                print(f"Attempt {attempt + 1} failed with error: {e}")

            if attempt == max_retries - 1:
                # Final fallback to requests
                if enable_print:
                    print("All Playwright attempts failed, falling back to requests...")
                try:
                    response = requests.get(
                        url,
                        headers={
                            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
                        },
                        timeout=30,
                    )
                    return response.text
                except Exception as req_error:
                    if enable_print:
                        print(f"Requests fallback also failed: {req_error}")
                    return f"Error: Unable to fetch content from {url}"
            else:
                # Wait before retrying
                await asyncio.sleep(5)

    return f"Error: All attempts to fetch content from {url} failed"


if __name__ == "__main__":
    import asyncio

    result = asyncio.run(fetch_web_content("https://pr.tsmc.com/english/latest-news", enable_print=True))
    print("=" * 50)
    print("FINAL RESULT:")
    print("=" * 50)
    print(result[:1000] + "..." if len(result) > 1000 else result)
