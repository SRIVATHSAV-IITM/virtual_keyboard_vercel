# Vercel Deployment Guidelines: Migrating from Desktop to Web

This document outlines the architectural changes required to migrate the **Nodtext V3 Tic-Tac-Toe / Virtual Keyboard** project from a local Python-based desktop application (using Eel) to a cloud-hosted web application on Vercel.

## ⚠️ The Architectural Challenge
The current application is a **Desktop App** that uses a local Python backend to control hardware (Webcam, Text-to-Speech) and local system files. **Vercel is a Cloud Platform** for hosting frontend websites and serverless functions. 

Cloud servers **cannot** access a user's local webcam or speakers directly through Python.

---

## 1. Phase 1: Frontend Migration (Browser-Side)
To run on Vercel, all hardware-dependent logic must move from Python (`launch_keyboard.py`) to JavaScript (`script.js`).

### A. Gaze Tracking (Webcam)
*   **Current:** Uses Python + OpenCV + MediaPipe on your local machine.
*   **Vercel Version:** Must use a JavaScript-based tracker that runs in the user's browser.
*   **Recommended Tool:** [WebGazer.js](https://webgazer.cs.brown.edu/) or [MediaPipe Face Mesh (JS)](https://developers.google.com/mediapipe/solutions/vision/face_landmarker).
*   **Action:** Replace `eel.get_gaze_coordinates()` with a local JS function that requests webcam permission via `navigator.mediaDevices.getUserMedia()`.

### B. Text-to-Speech (Audio)
*   **Current:** Uses Python `pyttsx3`.
*   **Vercel Version:** Use the built-in Browser Speech API.
*   **Action:** Replace `eel.speak_text(text)` with:
    ```javascript
    const utterance = new SpeechSynthesisUtterance(text);
    window.speechSynthesis.speak(utterance);
    ```

### C. File Saving
*   **Current:** Saves `.txt` files to a local `notes/` folder on your hard drive.
*   **Vercel Version:** Browsers cannot write to a user's hard drive for security reasons.
*   **Action:** Use the [File System Access API](https://developer.mozilla.org/en-US/docs/Web/API/File_System_API) or simply trigger a browser download:
    ```javascript
    const blob = new Blob([content], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    // Create a temporary link and click it to download
    ```

---

## 2. Phase 2: Backend Migration (Serverless)
Vercel does not support long-running Python scripts or WebSockets (used by Eel). You must convert Python logic into **Serverless Functions**.

### A. Word Suggestions (NLTK)
*   **Action:** Move your `get_suggestions` logic into a Vercel Python Function.
*   **File Path:** `/api/suggestions.py`
*   **Logic:** The frontend sends a `POST` request with the current text, and the Python function returns a JSON list of 5 words.

### B. Project Structure for Vercel
```text
project-root/
├── public/              # Static assets (images, sounds)
├── api/                 # Python Serverless Functions
│   └── suggestions.py   # Ported NLTK logic
├── index.html           # Main UI
├── script.js            # Main Logic (now includes Gaze & TTS)
├── style.css            # UI Styling
├── vercel.json          # Vercel configuration
└── requirements.txt     # Python dependencies for API
```

---

## 3. Phase 3: Deployment Steps
1.  **Remove Eel:** Delete all `import eel` and `@eel.expose` lines.
2.  **Rewrite Communication:** Replace `eel.function()()` calls with standard JavaScript `fetch()` calls to your `/api` endpoints.
3.  **Push to GitHub:** Vercel deploys directly from your GitHub repository.
4.  **Connect to Vercel:** Go to [vercel.com](https://vercel.com), "Add New Project," and select your repository.

---

## 4. Why This is Necessary
*   **Security:** Browsers block websites from "reaching out" to run scripts on a user's computer.
*   **Portability:** By moving logic to JavaScript, your keyboard will work on any device (including tablets and phones) without the user needing to install Python or OpenCV.
