# V3 Eye-Gaze Suite 👁️⌨️🐍📝

A comprehensive, browser-based suite of eye-gaze controlled applications, optimized for accessibility and standalone deployment. This suite uses **MediaPipe Face Mesh** for real-time eye tracking directly in the browser—no external hardware or Python backend required.

## 🚀 Live Demo
The suite is designed to be deployed on **Vercel** for instant access via any webcam-enabled device.

## 📦 Included Applications

1.  **Virtual Keyboard (`/keyboard`)**: A full-featured keyboard with dwell-to-click interaction and text-to-speech capabilities.
2.  **Retro Snake (`/snake`)**: A classic game controlled by eye movement using a 3x3 directional grid mapping.
3.  **Sentence Builder (`/activities`)**: Educational activities designed for building confidence and language skills through eye-gaze selection.

## ✨ Key Features
-   **Client-Side Eye Tracking**: Uses the webcam and MediaPipe for high-performance tracking.
-   **Dwell Interaction**: Visual progress indicators for "clicking" by looking at elements for a set duration.
-   **Unified Launcher**: A central hub to switch between applications using only your eyes.
-   **Responsive Design**: Works on modern browsers (Chrome, Edge, Safari).

## 🛠️ Deployment to Vercel

This repository is "Vercel Ready". To deploy:

1.  **Fork** this repository.
2.  Log in to [Vercel](https://vercel.com).
3.  Click **"New Project"** and select this repository.
4.  Ensure the **Root Directory** is set to `V3_EYE_GAZE_SUITE`.
5.  Click **Deploy**.

Alternatively, using the Vercel CLI:
```bash
cd V3_EYE_GAZE_SUITE
vercel
```

## 🖥️ Local Development
To run the suite locally:
1.  Clone the repository:
    ```bash
    git clone https://github.com/SRIVATHSAV-IITM/virtual_keyboard_vercel.git
    ```
2.  Open `V3_EYE_GAZE_SUITE/index.html` in a web browser (requires a local server like "Live Server" for camera permissions in some browsers).

## 📄 License
This project is open-source. See the repository for details.
