document.addEventListener('DOMContentLoaded', () => {
    const buttons = document.querySelectorAll('.menu-button');
    let hoverStates = {}; // Stores { buttonId: { isHovered: false, hoverStartTime: null, dwellProgress: 0 } }
    const DWELL_TIME_MS = 1500; // 1.5 seconds to activate

    // Create gaze pointer element
    const gazePointer = document.createElement('div');
    gazePointer.id = 'gaze-pointer';
    document.body.appendChild(gazePointer);

    buttons.forEach(button => {
        hoverStates[button.id] = { isHovered: false, hoverStartTime: null, dwellProgress: 0 };

        // Initial setup for CSS animation properties
        button.style.setProperty('--dwell-progress', '0%');
    });

    async function updateGaze() {
        const gazeCoords = await eel.get_gaze_coordinates()();
        const gazeX = gazeCoords[0];
        const gazeY = gazeCoords[1];

        // Update gaze pointer position
        if (gazeX !== null && gazeY !== null) {
            gazePointer.style.left = `${gazeX}px`;
            gazePointer.style.top = `${gazeY}px`;
            gazePointer.style.display = 'block'; // Show pointer
        } else {
            gazePointer.style.display = 'none'; // Hide pointer if no gaze detected
        }

        const currentTime = Date.now();

        buttons.forEach(button => {
            const rect = button.getBoundingClientRect();
            const isCurrentlyHovered = gazeX >= rect.left && gazeX <= rect.right &&
                                       gazeY >= rect.top && gazeY <= rect.bottom;

            let state = hoverStates[button.id];

            if (isCurrentlyHovered) {
                if (!state.isHovered) {
                    // Just started hovering
                    console.log(`Started hovering on ${button.id}`);
                    state.isHovered = true;
                    state.hoverStartTime = currentTime;
                    state.dwellProgress = 0;
                } else {
                    // Already hovering, update progress
                    const elapsedTime = currentTime - state.hoverStartTime;
                    state.dwellProgress = Math.min(1, elapsedTime / DWELL_TIME_MS);
                    button.style.setProperty('--dwell-progress', `${state.dwellProgress * 100}%`);
                    console.log(`Hovering on ${button.id}, progress: ${state.dwellProgress}`);

                    if (state.dwellProgress === 1) {
                        // Dwell complete, trigger action
                        console.log(`Dwell complete on ${button.id}`);
                        if (button.id === 'exit') {
                            window.close();
                        } else if (button.id === 'snake-game') {
                            eel.launch_snake_game()();
                        } else if (button.id === 'virtual-keyboard') {
                            eel.launch_virtual_keyboard()();
                        } else if (button.id === 'virtual-keyboard-web') {
                            eel.launch_virtual_keyboard_web()();
                        } else if (button.id === 'activities-center') {
                            eel.launch_activities_center()();
                        } else if (button.id === 'tic-tac-toe') {
                            eel.launch_tic_tac_toe()();
                        }
                        // Reset state after action
                        state.isHovered = false;
                        state.hoverStartTime = null;
                        state.dwellProgress = 0;
                        button.style.setProperty('--dwell-progress', '0%');
                    }
                }
            } else {
                // Not hovered or stopped hovering
                if (state.isHovered) {
                    // Just stopped hovering, reset immediately
                    console.log(`Stopped hovering on ${button.id}`);
                    state.isHovered = false;
                    state.hoverStartTime = null;
                    state.dwellProgress = 0;
                    button.style.setProperty('--dwell-progress', '0%');
                }
            }
        });

        requestAnimationFrame(updateGaze); // Continue the loop
    }

    // Start the gaze update loop
    updateGaze();
});