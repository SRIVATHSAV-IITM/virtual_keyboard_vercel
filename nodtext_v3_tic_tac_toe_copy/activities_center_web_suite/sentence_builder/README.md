# Gaze-Controlled Activities Center (Vercel Ready)

This is a standalone, browser-based version of the NODTEXT Activities Center (Eye-Gaze Sentence Builder), optimized for deployment on Vercel or any other static site hosting service.

## Features
- **Client-Side Eye Tracking:** Uses MediaPipe Face Mesh directly in the browser. No Python backend required.
- **Multiple Levels:** Three levels of difficulty for sentence building (4, 6, and 9 words).
- **Dwell Activation:** Hover over buttons or word boxes to select them.
- **Immediate Feedback:** Visual feedback on correct/incorrect word selections.

## How to Deploy to Vercel
1. Install the Vercel CLI: `npm i -g vercel`
2. Navigate to this directory: `cd activities_center_vercel`
3. Run `vercel` and follow the prompts.

Alternatively, you can push this directory to a GitHub repository and connect it to your Vercel account.

## Requirements
- A modern web browser (Chrome, Edge, or Safari recommended).
- A webcam for eye tracking.
- HTTPS is required for camera access in most browsers (Vercel provides this automatically).
