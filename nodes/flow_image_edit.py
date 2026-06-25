import torch
import numpy as np
from PIL import Image
import os
import time
from flow.flow_client import FlowClient

class FlowImageEdit:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "instruction": ("STRING", {"multiline": True}),
                "strength": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0, "step": 0.01}),
                "aspect_ratio": (["16:9", "4:3", "1:1", "3:4", "9:16"], {"default": "1:1"}),
                "max_images": ("INT", {"default": 4, "min": 1, "max": 4, "step": 1}),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("image", "info")
    FUNCTION = "edit"
    CATEGORY = "Google Flow"

    def edit(self, image, instruction, strength, aspect_ratio, max_images):
        client = FlowClient()
        
        # Convert ComfyUI tensor to PIL Image and save to a temp file
        img_tensor = image[0]
        img_np = (img_tensor.cpu().numpy() * 255).astype(np.uint8)
        img_pil = Image.fromarray(img_np)
        
        input_path = f"/tmp/flow_input_{int(time.time())}.png"
        img_pil.save(input_path)
        
        output_paths, info = client.edit_image(input_path, instruction, strength, aspect_ratio)
        output_paths = output_paths[:max_images]
        
        # Convert all returned images back to a batch tensor
        tensors = []
        for path in output_paths:
            res_img = Image.open(path).convert("RGB")
            res_np = np.array(res_img).astype(np.float32) / 255.0
            res_tensor = torch.from_numpy(res_np)[None,]
            tensors.append(res_tensor)
            
        batch_tensor = torch.cat(tensors, dim=0)
        
        # Cleanup input
        if os.path.exists(input_path):
            os.remove(input_path)
            
        return (batch_tensor, info)
