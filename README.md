# ComfyUI-GoogleFlow

A custom node extension for ComfyUI that integrates **Google Flow** (labs.google/fx/tools/flow) using browser automation (Playwright). 

This allows you to leverage your active Google AI subscription directly inside ComfyUI for image generation, editing, and Agent mode iterations, without requiring a public API.

## Features

* **Flow: Generate Image**: Text-to-image generation.
* **Flow: Edit Image**: Image-to-image editing based on text instructions and a strength slider.
* **Flow: Agent Step**: Connect conversational Agent interactions into your workflow, returning both the resulting image and the Agent's text response.
* **Headless Automation**: After the very first manual login, all browser interactions happen invisibly in the background.

## Installation

1. Navigate to your ComfyUI custom nodes directory:
   ```bash
   cd ComfyUI/custom_nodes/
   git clone <your-repo-url> ComfyUI-GoogleFlow
   cd ComfyUI-GoogleFlow
   ```
2. Install the required Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Install Playwright browser binaries:
   ```bash
   playwright install chromium
   ```

## First Setup (Authentication)

Because Google Flow requires an active subscription and Google Account, you need to manually log in once:
1. Start ComfyUI and add any `Flow:` node to your workspace.
2. Trigger a prompt (Queue Prompt).
3. The node will recognize that you aren't authenticated and will automatically launch a visible Google Chrome window.
4. Log into your Google Account in that window.
5. Once you are successfully logged in and the `labs.google/fx/tools/flow` page loads, the session is saved automatically.
6. The node will seamlessly switch to headless mode. All future generations will run completely hidden in the background!

## Disclaimer
* **Unofficial**: This is an unofficial integration. Google Flow's interface may change at any time, which might break the Playwright selectors.
* **Quotas**: Generating images via these nodes counts towards your personal Google AI subscription limits.
