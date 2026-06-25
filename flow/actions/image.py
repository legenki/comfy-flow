import time
from playwright.sync_api import Page

def _wait_for_generation(page: Page, initial_image_count: int) -> list:
    """
    Helper function to wait for the generation process to complete by checking
    if new images with 'getMediaUrlRedirect' have been added to the DOM.
    """
    print(f"[ComfyUI-GoogleFlow] Waiting for generation... (initial images: {initial_image_count})")
    start_time = time.time()
    while time.time() - start_time < 120:
        page.wait_for_timeout(2000)
        current_images = page.locator("img[src*='getMediaUrlRedirect']").all()
        current_count = len(current_images)
        if current_count > initial_image_count:
            print(f"[ComfyUI-GoogleFlow] Image count increased to {current_count}. Waiting for generation to finish settling...")
            
            # Let it settle to ensure all new images (e.g. 2 or 4) are fully loaded
            last_final_count = current_count
            for _ in range(10):
                page.wait_for_timeout(2000)
                new_final_count = len(page.locator("img[src*='getMediaUrlRedirect']").all())
                if new_final_count == last_final_count:
                    break
                last_final_count = new_final_count
                
            final_images = page.locator("img[src*='getMediaUrlRedirect']").all()
            print(f"[ComfyUI-GoogleFlow] Generation complete! Found {len(final_images) - initial_image_count} new images.")
            return final_images
            
    raise Exception("Timeout waiting for image generation to complete.")

def _ensure_project(page: Page):
    """
    Ensures we are inside a project (either the last one or a new one).
    """
    prompt_input = page.locator("[contenteditable='true']").first
    if prompt_input.is_visible(timeout=3000):
        return
        
    print("[ComfyUI-GoogleFlow] Not in a project, trying to find an existing one...")
    try:
        project_link = page.locator("a[href^='/fx/tools/flow/project/']").first
        if project_link.is_visible(timeout=2000):
            print("[ComfyUI-GoogleFlow] Found an existing project, opening it...")
            project_link.click()
            page.wait_for_timeout(3000)
            return
    except Exception:
        pass
        
    print("[ComfyUI-GoogleFlow] No existing project found, creating a new one...")
    try:
        new_project_btn = page.get_by_text("New project", exact=False).first
        if new_project_btn.is_visible(timeout=2000):
            new_project_btn.click()
            page.wait_for_timeout(2000)
        else:
            create_btn = page.get_by_role("button", name="Create").first
            if create_btn.is_visible(timeout=1000):
                create_btn.click()
                page.wait_for_timeout(2000)
    except Exception:
        pass
        
    if not page.locator("[contenteditable='true']").first.is_visible(timeout=5000):
        raise Exception("Could not find prompt input area. Are you in a project?")

def generate_image(page: Page, prompt: str, aspect_ratio: str) -> list[str]:
    """
    Automates the generation of an image in Google Flow.
    """
    print("[ComfyUI-GoogleFlow] Starting image generation process...")
    _ensure_project(page)
    
    prompt_input = page.locator("[contenteditable='true']").first

    # 1. Select Aspect Ratio
    try:
        # Find the main settings button
        menu_btn = page.get_by_text("🍌 Nano Banana", exact=False).first
        if menu_btn.is_visible(timeout=2000):
            menu_btn.click()
            page.wait_for_timeout(1500)
            
            # Click the tab corresponding to the aspect ratio
            print(f"[ComfyUI-GoogleFlow] Setting aspect ratio to {aspect_ratio}...")
            tab = page.get_by_role("tab").filter(has_text=aspect_ratio).first
            if tab.is_visible(timeout=2000):
                tab.click()
            page.wait_for_timeout(500)
            
            # Close the menu
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)
    except Exception as e:
        print(f"[ComfyUI-GoogleFlow] Warning: Could not set aspect ratio. Error: {e}")
            
    # Count existing images before generating
    print("[ComfyUI-GoogleFlow] Waiting for project images to settle...")
    last_count = -1
    for _ in range(10):
        current_count = len(page.locator("img[src*='getMediaUrlRedirect']").all())
        if current_count == last_count:
            break
        last_count = current_count
        page.wait_for_timeout(1000)
        
    existing_images = page.locator("img[src*='getMediaUrlRedirect']").all()
    initial_count = len(existing_images)
    print(f"[ComfyUI-GoogleFlow] Initial image count: {initial_count}")
    
    # 2. Enter prompt
    print(f"[ComfyUI-GoogleFlow] Entering prompt: {prompt}")
    prompt_input.fill(prompt)
    page.wait_for_timeout(500)
    prompt_input.press("Enter")
    
    # Try to click the Create button just in case Enter didn't work
    try:
        create_btn = page.locator("button", has_text="Create").last
        if create_btn.is_visible(timeout=1000):
            create_btn.click()
    except:
        pass
    
    # 3. Wait for generation to finish
    all_images = _wait_for_generation(page, initial_count)
    
    # 4. Extract generated images
    new_images = all_images[initial_count:]
    if new_images:
        output_paths = []
        print(f"[ComfyUI-GoogleFlow] Downloading {len(new_images)} high-res images...")
        for i, img_element in enumerate(new_images):
            src = img_element.get_attribute("src")
            url = "https://labs.google" + src if src.startswith("/") else src
            
            output_path = f"/tmp/flow_gen_{int(time.time())}_{i}.png"
            
            res = page.request.get(url)
            with open(output_path, "wb") as f:
                f.write(res.body())
                
            output_paths.append(output_path)
            
        return output_paths
        
    raise Exception("Failed to find generated images on the page.")

def edit_image(page: Page, image_path: str, instruction: str, strength: float, aspect_ratio: str) -> tuple[list[str], str]:
    """
    Automates the editing of an image in Google Flow.
    """
    print("[ComfyUI-GoogleFlow] Starting image edit process...")
    _ensure_project(page)
    
    # 1. Select Aspect Ratio
    try:
        # Find the main settings button
        menu_btn = page.get_by_text("🍌 Nano Banana", exact=False).first
        if menu_btn.is_visible(timeout=2000):
            menu_btn.click()
            page.wait_for_timeout(1500)
            
            # Click the tab corresponding to the aspect ratio
            print(f"[ComfyUI-GoogleFlow] Setting aspect ratio to {aspect_ratio}...")
            tab = page.get_by_role("tab").filter(has_text=aspect_ratio).first
            if tab.is_visible(timeout=2000):
                tab.click()
            page.wait_for_timeout(500)
            
            # Close the menu
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)
    except Exception as e:
        print(f"[ComfyUI-GoogleFlow] Warning: Could not set aspect ratio. Error: {e}")
        
    # 2. Enter instruction FIRST so we don't overwrite the image chip later
    prompt_input = page.locator("[contenteditable='true']").first
    print(f"[ComfyUI-GoogleFlow] Entering edit instruction: {instruction}")
    prompt_input.fill(instruction)
    page.wait_for_timeout(500)
    
    # 3. Upload reference image and add to prompt
    try:
        # Playwright can set files on hidden file inputs
        page.locator("input[type='file']").first.set_input_files(image_path, timeout=3000)
        print(f"[ComfyUI-GoogleFlow] Uploaded reference image: {image_path}")
        page.wait_for_timeout(3000)
        
        # We must explicitly click "Add to prompt" on the newly uploaded image!
        images = page.locator("img[src*='getMediaUrlRedirect']").all()
        if images:
            last_img = images[-1]
            last_img.hover()
            page.wait_for_timeout(1000)
            
            parent = last_img.locator("xpath=../..")
            more_btn = parent.locator("button", has_text="More").first
            if not more_btn.is_visible():
                more_btn = parent.locator("button[aria-label='More']").first
                
            if more_btn.is_visible():
                more_btn.click()
                page.wait_for_timeout(1000)
                
                add_to_prompt_btn = page.get_by_role("menuitem", name="Add to prompt").first
                if add_to_prompt_btn.is_visible():
                    add_to_prompt_btn.click()
                    print("[ComfyUI-GoogleFlow] Added uploaded image to prompt.")
                    page.wait_for_timeout(1000)
    except Exception as e:
        print(f"[ComfyUI-GoogleFlow] Warning: Could not upload file: {e}")
    
    # 4. Count existing images before generating
    print("[ComfyUI-GoogleFlow] Waiting for project images to settle...")
    last_count = -1
    for _ in range(10):
        current_count = len(page.locator("img[src*='getMediaUrlRedirect']").all())
        if current_count == last_count:
            break
        last_count = current_count
        page.wait_for_timeout(1000)
        
    existing_images = page.locator("img[src*='getMediaUrlRedirect']").all()
    initial_count = len(existing_images)
    print(f"[ComfyUI-GoogleFlow] Initial image count: {initial_count}")
    
    # 5. Press Enter to generate!
    prompt_input.focus()
    prompt_input.press("Enter")
    
    # Try to click the Create button just in case Enter didn't work
    try:
        create_btn = page.locator("button", has_text="Create").last
        if create_btn.is_visible(timeout=1000):
            create_btn.click()
    except:
        pass
    
    # 5. Wait for generation
    all_images = _wait_for_generation(page, initial_count)
    
    # 6. Extract edited images
    new_images = all_images[initial_count:]
    if new_images:
        output_paths = []
        print(f"[ComfyUI-GoogleFlow] Downloading {len(new_images)} high-res edited images...")
        for i, img_element in enumerate(new_images):
            src = img_element.get_attribute("src")
            url = "https://labs.google" + src if src.startswith("/") else src
            
            output_path = f"/tmp/flow_edit_{int(time.time())}_{i}.png"
            
            res = page.request.get(url)
            with open(output_path, "wb") as f:
                f.write(res.body())
                
            output_paths.append(output_path)
            
        return output_paths, "Edited successfully"
        
    raise Exception("Failed to find edited images on the page.")
