import torch
import numpy as np
from PIL import Image
import os
import time
from flow.flow_client import FlowClient

class FlowAgentStep:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "instruction": ("STRING", {"multiline": True}),
                "model": (["Gemini Omni", "Nano Banana"], {"default": "Gemini Omni"}),
            },
            "optional": {
                "image": ("IMAGE",),
                "context": ("STRING", {"multiline": True}),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("image", "response")
    FUNCTION = "step"
    CATEGORY = "Google Flow/Agent"

    def step(self, instruction, model, image=None, context=None):
        client = FlowClient()
        
        input_path = None
        if image is not None:
            img_tensor = image[0]
            img_np = (img_tensor.cpu().numpy() * 255).astype(np.uint8)
            img_pil = Image.fromarray(img_np)
            input_path = f"/tmp/flow_agent_in_{int(time.time())}.png"
            img_pil.save(input_path)
            
        output_path, response = client.agent_step(input_path, instruction, context, model)
        
        res_tensor = None
        if output_path and os.path.exists(output_path):
            res_img = Image.open(output_path).convert("RGB")
            res_np = np.array(res_img).astype(np.float32) / 255.0
            res_tensor = torch.from_numpy(res_np)[None,]
        else:
            # If agent didn't return an image, return a dummy or original image
            if image is not None:
                res_tensor = image
            else:
                res_np = np.zeros((1, 1, 3), dtype=np.float32)
                res_tensor = torch.from_numpy(res_np)[None,]
            
        if input_path and os.path.exists(input_path):
            os.remove(input_path)
            
        return (res_tensor, response)
