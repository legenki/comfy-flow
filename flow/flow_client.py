from auth.flow_auth import FlowAuthManager
from flow.actions.image import generate_image, edit_image
from flow.actions.agent import agent_step

class FlowClient:
    def __init__(self):
        self.auth_manager = FlowAuthManager()
        self.page = self.auth_manager.get_page()

    def generate_image(self, prompt: str, model: str):
        return generate_image(self.page, prompt, model)

    def edit_image(self, image_path: str, instruction: str, strength: float, model: str):
        return edit_image(self.page, image_path, instruction, strength, model)

    def agent_step(self, image_path: str, instruction: str, context: str, model: str):
        return agent_step(self.page, image_path, instruction, context, model)
