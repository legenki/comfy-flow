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
        if len(current_images) > initial_image_count:
            print(f"[ComfyUI-GoogleFlow] Generation complete! Found {len(current_images) - initial_image_count} new images.")
            # Give it a few seconds to fully render on the server side
            page.wait_for_timeout(4000)
            return current_images
    raise Exception("Timeout waiting for image generation to complete.")

def generate_image(page: Page, prompt: str, model: str) -> str:
    """
    Automates the generation of an image in Google Flow.
    """
    print("[ComfyUI-GoogleFlow] Starting image generation process...")
    # 0. Check if we are already in a project (contenteditable div exists)
    prompt_input = page.locator("[contenteditable='true']").first
    
    if not prompt_input.is_visible(timeout=3000):
        print("[ComfyUI-GoogleFlow] Not in a project, trying to create one...")
        # Try to find a 'New project' or 'Create new' button
        new_project_btn = page.get_by_text("New project", exact=False).first
        if new_project_btn.is_visible(timeout=3000):
            new_project_btn.click()
            page.wait_for_timeout(2000)
        else:
            # Maybe it's just "Create"
            create_btn = page.get_by_role("button", name="Create").first
            if create_btn.is_visible(timeout=1000):
                create_btn.click()
                page.wait_for_timeout(2000)
                
    # Re-locate prompt input
    prompt_input = page.locator("[contenteditable='true']").first
    if not prompt_input.is_visible(timeout=5000):
        raise Exception("Could not find prompt input area. Are you in a project?")

    # 1. Select model if applicable (Placeholder for UI interaction)
    if model:
        try:
            page.get_by_text(model, exact=False).last.click(timeout=2000)
            page.wait_for_timeout(500)
        except Exception:
            pass
            
    # Count existing images before generating
    existing_images = page.locator("img[src*='getMediaUrlRedirect']").all()
    initial_count = len(existing_images)
    
    # 2. Enter prompt
    print(f"[ComfyUI-GoogleFlow] Entering prompt: {prompt}")
    prompt_input.fill(prompt)
    page.wait_for_timeout(500)
    prompt_input.press("Enter")
    
    # 3. Wait for generation to finish
    all_images = _wait_for_generation(page, initial_count)
    
    # 4. Extract generated image
    if all_images:
        img_element = all_images[-1] # Get the latest one
        src = img_element.get_attribute("src")
        url = "https://labs.google" + src if src.startswith("/") else src
        
        output_path = f"/tmp/flow_gen_{int(time.time())}.png"
        print(f"[ComfyUI-GoogleFlow] Downloading high-res image to {output_path}...")
        
        res = page.request.get(url)
        with open(output_path, "wb") as f:
            f.write(res.body())
            
        return output_path
        
    raise Exception("Failed to find generated image on the page.")

def edit_image(page: Page, image_path: str, instruction: str, strength: float, model: str) -> tuple[str, str]:
    """
    Automates the editing of an image in Google Flow.
    """
    # 1. Upload reference image
    file_input = page.locator("input[type='file']").first
    if file_input.is_visible():
        file_input.set_input_files(image_path)
        page.wait_for_timeout(1000)
    else:
        print("[ComfyUI-GoogleFlow] Warning: Could not find file upload input.")
    
    # 2. Set strength slider if applicable (Placeholder)
    
    # Count existing images before generating
    existing_images = page.locator("img[src*='getMediaUrlRedirect']").all()
    initial_count = len(existing_images)
    
    # 3. Enter instruction
    prompt_input = page.locator("[contenteditable='true']").first
    if not prompt_input.is_visible(timeout=5000):
        raise Exception("Could not find prompt input area.")
        
    prompt_input.fill(instruction)
    page.wait_for_timeout(500)
    prompt_input.press("Enter")
    
    # 4. Wait for generation
    all_images = _wait_for_generation(page, initial_count)
    
    # 5. Extract edited image
    if all_images:
        img_element = all_images[-1]
        src = img_element.get_attribute("src")
        url = "https://labs.google" + src if src.startswith("/") else src
        
        output_path = f"/tmp/flow_edit_{int(time.time())}.png"
        print(f"[ComfyUI-GoogleFlow] Downloading high-res edited image to {output_path}...")
        
        res = page.request.get(url)
        with open(output_path, "wb") as f:
            f.write(res.body())
            
        return output_path, "Edited successfully"
        
    raise Exception("Failed to find edited image on the page.")
