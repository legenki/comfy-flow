import time
from playwright.sync_api import Page

def agent_step(page: Page, image_path: str, instruction: str, context: str, model: str) -> tuple[str, str]:
    """
    Automates a single step interaction in Google Flow's Agent mode.
    """
    # 1. Upload image if provided
    if image_path:
        file_input = page.locator("input[type='file']").first
        if file_input.is_visible():
            file_input.set_input_files(image_path)
            page.wait_for_timeout(1000)
            
    # 2. Enter instruction & context
    prompt_input = page.locator("textarea").first
    
    full_prompt = instruction
    if context:
        full_prompt = f"Previous context: {context}\nInstruction: {instruction}"
        
    prompt_input.fill(full_prompt)
    prompt_input.press("Enter")
    
    # 3. Wait for agent to process and respond
    page.wait_for_timeout(2000)
    try:
        page.wait_for_selector("progressbar", state="detached", timeout=120000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    
    # 4. Extract agent text response
    # This selector is a placeholder. It assumes responses are within elements like .agent-response
    responses = page.locator(".agent-response, .message-content, p").all()
    text_response = "No response text found"
    if responses:
        text_response = responses[-1].inner_text()
        
    # 5. Extract resulting image (if any)
    images = page.locator("img").all()
    output_path = None
    if images:
        img_element = images[-1]
        output_path = f"/tmp/flow_agent_{int(time.time())}.png"
        img_element.screenshot(path=output_path)
        
    return output_path, text_response
