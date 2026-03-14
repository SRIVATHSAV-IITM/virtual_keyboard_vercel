# Gaze-Controlled Virtual Keyboard (Vercel Ready)

This is a standalone, browser-based version of the NODTEXT Virtual Keyboard, optimized for deployment on Vercel or any other static site hosting service.

## Features
- **Client-Side Eye Tracking:** Uses MediaPipe Face Mesh directly in the browser.
- **Smart Compose:** Suggests common phrases and sentence completions based on context.
- **Text-to-Speech:** Uses the native Web Speech API.
- **File Saving:** Saves typed text as a `.txt` file using browser downloads.
- **Word Suggestions:** Uses a built-in JavaScript word list.
- **Dwell Activation:** Hover over keys to type.

## How to Deploy to Vercel
1. Install the Vercel CLI: `npm i -g vercel`
2. Navigate to this directory: `cd virtual_keyboard_vercel`
3. Run `vercel` and follow the prompts.

Alternatively, you can push this directory to a GitHub repository and connect it to your Vercel account.

## Requirements
- A modern web browser (Chrome, Edge, or Safari recommended).
- A webcam for eye tracking.
- HTTPS is required for camera access in most browsers (Vercel provides this automatically).
