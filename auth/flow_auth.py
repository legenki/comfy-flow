import os
import time
from playwright.sync_api import sync_playwright, Playwright, BrowserContext, Page

FLOW_URL = "https://labs.google/fx/tools/flow"

class FlowAuthManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(FlowAuthManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        
        # Determine the user_data directory relative to this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.user_data_dir = os.path.join(os.path.dirname(current_dir), "user_data", "flow_context")
        
        self.playwright: Playwright = None
        self.context: BrowserContext = None
        self.page: Page = None
        self._initialized = True

    def ensure_session(self):
        """
        Ensures that an authenticated session exists.
        First tries headless. If not authenticated, closes and reopens headed for manual login.
        """
        if self.page and not self.page.is_closed():
            # If already running and page is open, verify we are on flow
            try:
                if FLOW_URL in self.page.url:
                    return self.page
            except Exception:
                pass

        # Cleanup existing if any
        self.close()

        print("[ComfyUI-GoogleFlow] Starting Playwright in HEADLESS mode...")
        self.playwright = sync_playwright().start()
        
        # Try headless first
        self.context = self.playwright.chromium.launch_persistent_context(
            user_data_dir=self.user_data_dir,
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        self.page = self.context.new_page() if len(self.context.pages) == 0 else self.context.pages[0]
        
        is_logged_in = self._check_login(self.page)
        
        if is_logged_in:
            print("[ComfyUI-GoogleFlow] Successfully authenticated in headless mode.")
            return self.page
        
        print("[ComfyUI-GoogleFlow] Authentication required. Relaunching in HEADED mode for manual login.")
        # Not logged in. Close headless and reopen headed.
        self.close()
        
        self.playwright = sync_playwright().start()
        self.context = self.playwright.chromium.launch_persistent_context(
            user_data_dir=self.user_data_dir,
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )
        self.page = self.context.new_page() if len(self.context.pages) == 0 else self.context.pages[0]
        
        print("[ComfyUI-GoogleFlow] Please log in to Google Flow in the opened browser window.")
        is_logged_in = self._check_login(self.page, wait_for_manual=True)
        
        if is_logged_in:
            print("[ComfyUI-GoogleFlow] Successfully authenticated manually. Session saved.")
            self.close()
            
            print("[ComfyUI-GoogleFlow] Switching back to HEADLESS mode...")
            self.playwright = sync_playwright().start()
            self.context = self.playwright.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                headless=True,
                args=["--disable-blink-features=AutomationControlled"]
            )
            self.page = self.context.new_page() if len(self.context.pages) == 0 else self.context.pages[0]
            self.page.goto(FLOW_URL)
            self.page.wait_for_load_state("networkidle")
            return self.page
        else:
            raise Exception("Failed to authenticate to Google Flow. Please restart and try again.")

    def _check_login(self, page: Page, wait_for_manual=False) -> bool:
        """
        Navigates to Flow and checks if we are logged in.
        If wait_for_manual is True, it gives the user time to log in.
        """
        try:
            page.goto(FLOW_URL, timeout=60000)
            page.wait_for_load_state("networkidle")
            
            # Check for login redirect or login buttons
            if "accounts.google.com" in page.url or "signin" in page.url:
                if wait_for_manual:
                    print("[ComfyUI-GoogleFlow] Waiting for manual login (timeout in 300s)...")
                    try:
                        # Wait until the URL changes back to labs.google
                        page.wait_for_url(f"**{FLOW_URL}**", timeout=300000)
                        page.wait_for_load_state("networkidle")
                        return True
                    except Exception as e:
                        print(f"[ComfyUI-GoogleFlow] Login timeout or error: {e}")
                        return False
                else:
                    return False
            
            if FLOW_URL in page.url:
                return True
                
            return False
        except Exception as e:
            print(f"[ComfyUI-GoogleFlow] Error checking login status: {e}")
            return False

    def get_page(self) -> Page:
        if not self.page or self.page.is_closed():
            return self.ensure_session()
        return self.page

    def close(self):
        if self.context:
            try:
                self.context.close()
            except:
                pass
            self.context = None
        if self.playwright:
            try:
                self.playwright.stop()
            except:
                pass
            self.playwright = None
        self.page = None
