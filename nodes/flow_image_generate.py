import torch
import numpy as np
from PIL import Image
from flow.flow_client import FlowClient

class FlowImageGenerate:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True}),
                "model": (["Nano Banana", "Gemini Omni", "Veo 3.1"], {"default": "Nano Banana"}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "generate"
    CATEGORY = "Google Flow"

    def generate(self, prompt, model):
        client = FlowClient()
        output_path = client.generate_image(prompt, model)
        
        # Convert saved image to ComfyUI tensor
        img = Image.open(output_path).convert("RGB")
        img_np = np.array(img).astype(np.float32) / 255.0
        img_tensor = torch.from_numpy(img_np)[None,]
        
        return (img_tensor,)
