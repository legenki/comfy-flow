import time
from playwright.sync_api import Page

def _wait_for_generation(page: Page):
    """
    Helper function to wait for the generation process to complete.
    This is highly dependent on the Google Flow DOM structure.
    """
    page.wait_for_timeout(2000) # Give UI time to react
    try:
        # Assuming there is a progress bar or loading spinner that we wait to detach
        page.wait_for_selector("progressbar", state="detached", timeout=120000)
    except Exception:
        pass
    page.wait_for_timeout(2000) # Buffer after loading

def generate_image(page: Page, prompt: str, model: str) -> str:
    """
    Automates the generation of an image in Google Flow.
    """
    # 1. Select model if applicable (Placeholder for UI interaction)
    if model:
        try:
            page.get_by_text(model, exact=False).last.click(timeout=2000)
            page.wait_for_timeout(500)
        except Exception:
            pass
    # 2. Find prompt input
    prompt_input = page.get_by_placeholder("Describe what you want to see", exact=False).first
    if not prompt_input.is_visible():
        prompt_input = page.locator("textarea:visible, [contenteditable='true']:visible").first
    
    prompt_input.fill(prompt)
    prompt_input.press("Enter")
    
    # 3. Wait for generation to finish
    _wait_for_generation(page)
    
    # 4. Extract generated image
    # Assuming the most recently added image is the generated one
    images = page.locator("img[src^='blob:']").all() 
    if not images:
        images = page.locator("img").all()
        
    if images:
        img_element = images[-1]
        output_path = f"/tmp/flow_gen_{int(time.time())}.png"
        img_element.screenshot(path=output_path)
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
    
    # 3. Enter instruction
    prompt_input = page.get_by_placeholder("Instruction", exact=False).first
    if not prompt_input.is_visible():
        prompt_input = page.locator("textarea:visible, [contenteditable='true']:visible").first
        
    prompt_input.fill(instruction)
    prompt_input.press("Enter")
    
    # 4. Wait for generation
    _wait_for_generation(page)
    
    # 5. Extract edited image
    images = page.locator("img").all()
    if images:
        img_element = images[-1]
        output_path = f"/tmp/flow_edit_{int(time.time())}.png"
        img_element.screenshot(path=output_path)
        return output_path, "Edited successfully"
        
    raise Exception("Failed to find edited image on the page.")
