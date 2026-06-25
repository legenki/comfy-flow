from auth.flow_auth import PlaywrightWorker, _ensure_session_task
from flow.actions.image import generate_image, edit_image
from flow.actions.agent import agent_step

class FlowClient:
    def __init__(self):
        self.worker = PlaywrightWorker()
        self.worker.execute(_ensure_session_task)

    def generate_image(self, prompt: str, model: str):
        def _task(worker):
            return generate_image(worker.page, prompt, model)
        return self.worker.execute(_task)

    def edit_image(self, image_path: str, instruction: str, strength: float, model: str):
        def _task(worker):
            return edit_image(worker.page, image_path, instruction, strength, model)
        return self.worker.execute(_task)

    def agent_step(self, image_path: str, instruction: str, context: str, model: str):
        def _task(worker):
            return agent_step(worker.page, image_path, instruction, context, model)
        return self.worker.execute(_task)
