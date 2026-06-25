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
                "aspect_ratio": (["16:9", "4:3", "1:1", "3:4", "9:16"], {"default": "1:1"}),
                "max_images": ("INT", {"default": 4, "min": 1, "max": 4, "step": 1}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "generate"
    CATEGORY = "Google Flow"

    def generate(self, prompt, aspect_ratio, max_images):
        client = FlowClient()
        output_paths = client.generate_image(prompt, aspect_ratio)
        
        output_paths = output_paths[:max_images]
        
        # Convert all saved images to ComfyUI tensors and stack them into a batch
        tensors = []
        for path in output_paths:
            img = Image.open(path).convert("RGB")
            img_np = np.array(img).astype(np.float32) / 255.0
            img_tensor = torch.from_numpy(img_np)[None,]
            tensors.append(img_tensor)
            
        batch_tensor = torch.cat(tensors, dim=0)
        
        return (batch_tensor,)
