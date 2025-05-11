
// ------------------------------------------------------------
// DOM MANAGEMENT SCRIPTS 
// ------------------------------------------------------------
// This script is responsible for managing the DOM elements
// and handling user interactions in the web page. It is
// designed to be agnostic of the backend technology and should
// work with any backend that can send and receive JSON messages.

// function create_message(command, data) {
//     const message = {
//         "session-id": session_id,
//         "command": command,
//         "data": data
//     };
//     return JSON.stringify(message);
// }

// ==== Process messages received from the backend =====
function ProcessMessageFromBackend(message) {
    try {
        // Try to parse the message as JSON
        const data = JSON.parse(message);
        
        // Handle different types of messages
        switch (data.type) {
            case 'snackbar':
                console.log('Received snackbar message');
                showSnackbar(data.content, data.duration, data.level);
            case 'status':
                var level = 'info';
                console.log('Received status update');
                if (data.level) {
                    console.log('Status level:', data.level);
                    level = data.level;
                }
                appendMessage(data.content, level);
                break;
            case 'spinning-start':
                console.log('Received waiting-start message');
                toggleSpinner(true);
                break;
            case 'spinning-stop':
                console.log('Received waiting-stop message');
                toggleSpinner(false);
                break;
            case 'content':
                console.log('Received content message');
                if (data.targetId) {
                    console.log('has targetId');
                    const element = document.getElementById(data.targetId);
                    if (element) {
                        console.log('element found');
                        if (data.html) {
                            console.log('has html');
                            element.innerHTML = atob(data.html);
                        }
                        if (data.styling) {
                            console.log('has styling');
                            element.style.cssText += atob(data.styling);
                        }
                    } else {
                        console.error('Target element not found:', data.targetId);
                    }
                }
                else {
                    console.error('Invalid content update message format');
                    return;
                }
                break;

            case 'styling':
                console.log('Received styling message');
                // Create a style element
                const styleElement = document.createElement('style');
                styleElement.textContent = atob(data.styling);
                // Append to document head
                document.head.appendChild(styleElement);
                break;

            case 'theme':
                console.log('Received theme command');
                const targetId = 'theme-styles';
                const element = document.getElementById('theme-styles');
                if (element && data.styling) {
                    console.log('Updating theme');
                    element.style.cssText += atob(data.styling);
                } else {
                    console.error('Theme style element or theme update not found!');
                }

                break;

            case 'error':
                console.error('Error from backend:', data.content);
                appendMessage('Error: ' + data.content);
                break;
                
            case 'sections':
                console.log('Received sections');
                toggleLayout({
                    header: data.header,
                    footer: data.footer,
                    status: data.status,
                    aside: data.aside,
                    asideOpen: data.asideOpen,
                    statusOpen: data.statusOpen
                });
                break;
            
            case 'received':
                console.log('Backend acknowledged receipt');
                break;

            case 'startAnimation':
                console.log('Received startAnimation message');
                if (typeof window.startAnimationProcess === 'function') {
                    window.startAnimationProcess();
                } else {
                    console.log('Animation function not available, adding to queue');
                    // Create a startup function if it doesn't exist
                    if (!window.startupFunctions) {
                        window.startupFunctions = [];
                        
                        // Create a processor for queued functions
                        window.processStartupFunctions = function() {
                            while (window.startupFunctions.length > 0) {
                                const fn = window.startupFunctions.shift();
                                try {
                                    fn();
                                } catch (e) {
                                    console.error('Error executing startup function:', e);
                                }
                            }
                        };
                    }
                    
                    // Add the animation to the queue
                    window.startupFunctions.push(() => {
                        if (typeof window.startAnimationProcess === 'function') {
                            window.startAnimationProcess();
                        } else {
                            console.error('Animation function still not available');
                        }
                    });
                }
                break;
            

            default:
                console.warn('Unknown message type:', data.type);
        }
    } catch (error) {
        // If parsing fails, treat it as a simple status message for backward compatibility
        console.log('Parsing error:', error);
        console.log('Treating message as plain text:', message);
    }
}

// ==== Update the content of an element ====
function updateElementContent(elementId, htmlContent) {
    const element = document.getElementById(elementId);
    if (element) {
        // Safely update the HTML content
        element.innerHTML = htmlContent;
        console.log(`Updated element ${elementId} with new content`);
    } else {
        console.error(`Target element ${elementId} not found`);
    }
}

// ==== Apply styles to an element ====
function applyStyles(element_id, styling) {
    const element = document.getElementById(element_id);
    
    if (element) {
        // Decode the encoded CSS string
        // const decodedStyles = decodeURIComponent(styling);
        element.style.cssText += styling;
        console.log(`Applied styles to element with ID '${element_id}'`);
    } else {
        console.warn(`Element with ID '${element_id}' not found`);
        return;
    }
}

// ==== Adds messages to the status area ====
function appendMessage(text, level = 'info') {
    const statusElement = document.getElementById('status-content');
    if (statusElement) {
        // Create the new message element
        const newMessage = document.createElement('p');
        newMessage.classList.add(`${level}`); 
        newMessage.classList.add(`status-message`); 
        
        // Add timestamp
        const now = new Date();
        const timestamp = now.toTimeString().split(' ')[0] + '.' + 
                         now.getMilliseconds().toString().padStart(3, '0');
        
        // Combine timestamp and text
        newMessage.innerHTML = `[${timestamp}] ${text}`;
        
        // Append the message at the end
        statusElement.appendChild(newMessage);
        
        // Scroll to show the newest message
        statusElement.scrollTop = statusElement.scrollHeight;
    } else {
        console.error('Messages element not found');
    }
}

// ==== User Interaction Handlers ====
document.addEventListener('click', function(event) {
    const element = event.target;
    
    // Create the JSON object with click data
    const clickData = {
        // timestamp: new Date().toISOString(),
        type: 'click',
        tagName: element.tagName.toLowerCase(),
        id: element.id || null,
        className: element.className || null
        // path: getElementPath(element)
    };

    // Send via sendMessage instead of fetch
    sendMessage(JSON.stringify(clickData));
});

// Helper function to get element's DOM path
function getElementPath(element) {
    let path = [];
    while (element && element.tagName) {
        let selector = element.tagName.toLowerCase();
        if (element.id) {
            selector += `#${element.id}`;
        } else if (element.className) {
            selector += `.${element.className.replace(/\s+/g, '.')}`;
        }
        path.unshift(selector);
        element = element.parentElement;
    }
    return path.join('/');
}

function button_click(button_name) {
    console.log('Button clicked:', button_name);
    sendMessage(button_name + ' clicked').catch(error => {
        console.error('Error in button click handler:', error);
    });
}


// ==== Waiting Spinner Functions ====
// Function to control the spinner state
function toggleSpinner(shouldSpin = null) {
    const spinnerContainer = document.getElementById('spinner-container');
    if (!spinnerContainer) {
        console.error('Spinner container not found');
        return;
    }

    // If no state is provided, toggle the current state
    const newState = (shouldSpin !== null) ? shouldSpin : 
                    !spinnerContainer.classList.contains('spinning');

    if (newState) {
        spinnerContainer.classList.add('spinning');
    } else {
        spinnerContainer.classList.remove('spinning');
    }

    return newState;
}

// Helper function to initialize the spinner
function initializeSpinner() {
    const container = document.getElementById('spinner-container');
    if (!container) {
        console.error('Cannot initialize spinner: container not found');
        return;
    }

    // Add necessary styles if not already present
    // if (!document.getElementById('spinner-styles')) {
    //     const styleSheet = document.createElement('style');
    //     styleSheet.id = 'spinner-styles';
    //     styleSheet.textContent = ` `;
    //     document.head.appendChild(styleSheet);
    // }
}

// ==== Snackbar Notification Functions ====
function showSnackbar(message, duration = 0, level = 'info') {
    // Remove any existing snackbar
    const existingSnackbar = document.querySelector('.snackbar');
    if (existingSnackbar) {
        existingSnackbar.remove();
    }

    // Create snackbar container
    const snackbar = document.createElement('div');
    snackbar.className = `snackbar ${level}`;

    // Create message text
    const messageText = document.createElement('span');
    messageText.textContent = message;

    // Create close button
    const closeButton = document.createElement('button');
    closeButton.className = 'snackbar-close';
    closeButton.innerHTML = '×';
    closeButton.setAttribute('aria-label', 'Close notification');

    // Add elements to snackbar
    snackbar.appendChild(messageText);
    snackbar.appendChild(closeButton);

    // Add snackbar to the main container
    const mainContainer = document.getElementById('main');
    mainContainer.appendChild(snackbar);

    // Show the snackbar
    setTimeout(() => {
        snackbar.classList.add('show');
    }, 100);

    // Handle close button click
    closeButton.addEventListener('click', () => {
        snackbar.classList.remove('show');
        setTimeout(() => {
            snackbar.remove();
        }, 300);
    });

    // Auto-hide after specified time
    if (duration && duration > 0) {
        setTimeout(() => {
            if (snackbar.parentElement) {  // Check if snackbar still exists
                snackbar.classList.remove('show');
                setTimeout(() => {
                    if (snackbar.parentElement) {  // Double check before removal
                        snackbar.remove();
                    }
                }, 300);
            }
        }, duration * 1000);
    }
}

// ------------------------------------------------------------
// END DOM MANAGEMENT SCRIPTS 
// ------------------------------------------------------------
