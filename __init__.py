from .nodes.flow_image_generate import FlowImageGenerate
from .nodes.flow_image_edit import FlowImageEdit
from .nodes.flow_agent_step import FlowAgentStep

NODE_CLASS_MAPPINGS = {
    "FlowImageGenerate": FlowImageGenerate,
    "FlowImageEdit": FlowImageEdit,
    "FlowAgentStep": FlowAgentStep
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "FlowImageGenerate": "Flow: Generate Image",
    "FlowImageEdit": "Flow: Edit Image",
    "FlowAgentStep": "Flow: Agent Step"
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
