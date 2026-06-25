import os
import time
from playwright.sync_api import sync_playwright, Playwright, BrowserContext, Page
import threading
import queue

FLOW_URL = "https://labs.google/fx/tools/flow"

class PlaywrightWorker:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PlaywrightWorker, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
        
    def __init__(self):
        if self._initialized:
            return
        self.task_queue = queue.Queue()
        self.thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.thread.start()
        self._initialized = True
        
    def _worker_loop(self):
        with sync_playwright() as p:
            self.playwright = p
            self.context = None
            self.page = None
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.user_data_dir = os.path.join(os.path.dirname(current_dir), "..", "user_data", "flow_context")
            
            while True:
                task = self.task_queue.get()
                if task is None:
                    break
                    
                func, args, kwargs, result_queue = task
                try:
                    res = func(self, *args, **kwargs)
                    result_queue.put(("success", res))
                except Exception as e:
                    result_queue.put(("error", e))
                finally:
                    self.task_queue.task_done()

    def execute(self, func, *args, **kwargs):
        res_queue = queue.Queue()
        self.task_queue.put((func, args, kwargs, res_queue))
        status, result = res_queue.get()
        if status == "error":
            raise result
        return result

def _ensure_session_task(worker: PlaywrightWorker):
    import time
    if worker.page and not worker.page.is_closed():
        try:
            if FLOW_URL in worker.page.url:
                # Still need to verify we aren't stuck on the landing page
                _navigate_past_landing_page(worker.page)
                if not ("accounts.google.com" in worker.page.url or "signin" in worker.page.url):
                    return True
        except Exception:
            pass

    if worker.context:
        try:
            worker.context.close()
            time.sleep(1)
        except:
            pass

    print("[ComfyUI-GoogleFlow] Starting Playwright in HEADLESS mode...")
    worker.context = worker.playwright.chromium.launch_persistent_context(
        user_data_dir=worker.user_data_dir,
        headless=True,
        args=["--disable-blink-features=AutomationControlled"]
    )
    worker.page = worker.context.new_page() if len(worker.context.pages) == 0 else worker.context.pages[0]
    
    is_logged_in = _check_login(worker.page)
    if is_logged_in:
        print("[ComfyUI-GoogleFlow] Successfully authenticated in headless mode.")
        return True
    
    print("[ComfyUI-GoogleFlow] Authentication required. Relaunching in HEADED mode for manual login.")
    worker.context.close()
    time.sleep(2) # Wait for file locks to release
    
    worker.context = worker.playwright.chromium.launch_persistent_context(
        user_data_dir=worker.user_data_dir,
        headless=False,
        args=["--disable-blink-features=AutomationControlled"]
    )
    worker.page = worker.context.new_page() if len(worker.context.pages) == 0 else worker.context.pages[0]
    
    print("[ComfyUI-GoogleFlow] Please log in to Google Flow in the opened browser window.")
    is_logged_in = _check_login(worker.page, wait_for_manual=True)
    
    if is_logged_in:
        print("[ComfyUI-GoogleFlow] Successfully authenticated manually.")
        worker.context.close()
        raise Exception("✅ Авторизация успешна! Пожалуйста, нажми 'Queue Prompt' еще раз для генерации изображения.")
    else:
        raise Exception("❌ Failed to authenticate to Google Flow.")

def _navigate_past_landing_page(page: Page):
    """
    Checks if we are on the landing page and clicks the enter button if so.
    """
    clicked = False
    try:
        # Check if the "Create with Google Flow" button is on screen
        create_btn = page.get_by_text("Create with Google Flow", exact=False).first
        if create_btn.is_visible(timeout=3000):
            print("[ComfyUI-GoogleFlow] Found landing page button, clicking it...")
            create_btn.click()
            clicked = True
    except Exception as e:
        print(f"[ComfyUI-GoogleFlow] Error interacting with landing page: {e}")
        
    if clicked:
        try:
            # Wait for redirect to accounts.google.com to begin/complete
            page.wait_for_timeout(3000)
        except Exception:
            pass

def _check_login(page: Page, wait_for_manual=False) -> bool:
    try:
        page.goto(FLOW_URL, timeout=60000)
        page.wait_for_load_state("networkidle")
        
        # We might be on the landing page, so we must click the button first to see if it redirects to login
        if not wait_for_manual:
            _navigate_past_landing_page(page)
            
        print(f"[ComfyUI-GoogleFlow] Checking login status on URL: {page.url}")
        
        if "accounts.google.com" in page.url or "signin" in page.url:
            if wait_for_manual:
                print("[ComfyUI-GoogleFlow] Waiting for manual login (timeout in 300s)...")
                try:
                    # Wait until the URL changes back to something else
                    page.wait_for_url(lambda url: "accounts.google.com" not in url and "signin" not in url, timeout=300000)
                    page.wait_for_load_state("networkidle")
                    _navigate_past_landing_page(page)
                    return True
                except Exception as e:
                    print(f"[ComfyUI-GoogleFlow] Login timeout or error: {e}")
                    return False
            else:
                return False
        
        return True
    except Exception as e:
        print(f"[ComfyUI-GoogleFlow] Error checking login status: {e}")
        return False
