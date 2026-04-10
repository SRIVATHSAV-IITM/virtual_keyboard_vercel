# Virtual Keyboard Vercel - System Overview

This document provides a technical breakdown of the **NODTEXT Virtual Keyboard (Vercel Edition)**, covering its architecture, data flow, and file interactions.

## 1. Core Architecture (Serverless & Client-Side)
The application is built as a **Static Web App**. It is designed to run entirely in the user's browser without requiring a backend server or a traditional database.

*   **Database:** None. The application uses **Volatile State**. All typed text is stored in a JavaScript variable (`typedText`).
*   **Data Persistence:** To "save" work, the app uses the **Browser File System API**. It generates a `Blob` (Binary Large Object) and triggers a download of a `.txt` file directly to the user's local machine.
*   **Infrastructure:** Optimized for **Vercel**, relying on its global CDN to serve static assets over HTTPS (required for webcam access).

## 2. API Strategy
The project replaces external cloud APIs with **Native Browser APIs** and **Client-Side Libraries** to ensure low latency and zero cost.

| Feature | Technology Used | Type |
| :--- | :--- | :--- |
| **Eye Tracking** | [MediaPipe Face Mesh](https://google.github.io/mediapipe/solutions/face_mesh) | Client-Side AI (WASM) |
| **Speech (TTS)** | [Web Speech API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API) | Native Browser API |
| **Autocomplete** | JavaScript Array Filtering | Local Logic |
| **Video Capture** | MediaPipe Camera Utils | Native Browser (getUserMedia) |

## 3. File Interlinking & Dependencies
The `index.html` acts as the orchestrator, loading files in a specific order to manage dependencies.

### A. The Data Link (`wordlist.js` → `script.js`)
`wordlist.js` is loaded before the main logic. It populates a global constant `commonWords`. Because of the loading order, `script.js` can access this array directly for autocomplete suggestions without needing complex imports.

### B. The Visual Link (`style.css` ↔ `script.js`)
Communication happens via **CSS Custom Properties**:
1.  **Script Logic:** `script.js` calculates the "dwell progress" (how long a user has looked at a key).
2.  **Handoff:** It updates a CSS variable: `element.style.setProperty('--dwell-progress', '65%')`.
3.  **Styling:** The `style.css` uses `width: var(--dwell-progress)` on a pseudo-element (`::before`) to create the visual "fill" animation.

### C. The Cursor Link (`index.html` ↔ `script.js`)
Because the main textarea is `readonly` (to prevent mobile keyboards from popping up), the standard cursor is invisible. 
*   **The Mirror:** `script.js` creates a hidden `<div>` (the Mirror) that copies the textarea's styles (font, width, padding).
*   **Calculation:** By placing a invisible marker in the Mirror, the script calculates the exact X/Y pixel coordinates of the end of the text.
*   **Feedback:** It then moves the `#custom-cursor` div to those coordinates and triggers the blink animation.

## 4. The Interaction Pipeline
The system operates in a continuous loop roughly every 16ms (60fps):

1.  **Capture:** The webcam feed is captured by `camera_utils.js`.
2.  **Process:** Each frame is sent to **MediaPipe**. It identifies 468+ facial landmarks.
3.  **Calculate:** `script.js` extracts the **Iris Landmarks**, averages them, and maps them to screen pixels (applying Sensitivity and Smoothing).
4.  **Dwell:** The system checks if the gaze coordinate overlaps with a `.key` or `.suggestion-item` using `document.elementFromPoint()`.
5.  **Trigger:** If the gaze stays on an item for **800ms**, the `handleKey()` function is called.
6.  **Update:** The `typedText` is modified, the mirror updates the cursor position, and the autocomplete logic refreshes the suggestion bar.

---
*Generated for future reference in the NODTEXT project.*
