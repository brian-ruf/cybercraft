
// ------------------------------------------------------------
// PYSIDE6 BRIDGE 
// ------------------------------------------------------------
//       Facilitates communication between the web page and 
//       the Python/Pyside6 backend via the QWebChannel object
// ------------------------------------------------------------
// This can be replaced with a handler that uses websockets 
// or other technologies to communicate with a backend, provided
// the replacement handler::
// - forwards JSON messages to the 
//     `ProcessMessageFromBackend` function (location: `dom_management.js`)
// - offers a function named `sendMessage` that
//     accepts JSON messages before forwarding to the backend
// ------------------------------------------------------------ 
let backend = null;
let channelInitialized = false;
var debug=true;

// Setsup the web channel for communication between the web page and the Python backend
// This is done by creating a new QWebChannel object and connecting to the backend object
function initWebChannel() {
    if (channelInitialized) {
        console.log('WebChannel already initialized');
        return;
    }
    
    console.log('Initializing web channel...');
    if (typeof qt === 'undefined' || !qt.webChannelTransport) {
        console.error('Qt transport not available');
        return;
    }
    
    try {
        new QWebChannel(qt.webChannelTransport, function(channel) {
            console.log('QWebChannel callback executing');
            if (!channel || !channel.objects || !channel.objects.backend) {
                console.error('Channel initialization incomplete');
                return;
            }
            
            backend = channel.objects.backend;
            
            // Connect to Python signals
            backend.messageFromPython.connect(function(message) {
                // console.log('Received message from Python:', message);
                ProcessMessageFromBackend(message);
            });

            // Important: Signal to Python that JS is ready
            backend.notify_js_ready();
            channelInitialized = true;
            
            console.log('Bridge fully initialized');
        });
    } catch (error) {
        console.error('Error during QWebChannel initialization:', error);
    }
}

// Event listener for window load event and ensures that the web channel is initialized
window.addEventListener('load', function() {
    console.log('Window load event fired');
    if (!channelInitialized) {
        console.log('Channel not yet initialized, retrying');
        initWebChannel();
    }
});

// Receives messages in JSON format and forwards them to the backend
// Called by functions in dom_management.js
function sendMessage(message) {
    // SEND MESSAGE TO PYTHON
    if (!backend) {
        console.error('Backend not initialized');
        return Promise.reject('Backend not initialized');
    }
    console.log('Sending message to Backend');
    return new Promise((resolve, reject) => {
        try {
            backend.receive_from_js(message, (result) => {
                console.log('Sent to Backend: ' + message);
                resolve(result);
            });
        } catch (error) {
            console.error('Error sending message:', error);
            reject(error);
        }
    });
}

// accepts miessags from the backend and forward them to the ProcessMessageFromBackend function
function processData() {
    if (!backend) {
        console.error('Backend not initialized');
        return Promise.reject('Backend not initialized');
    }
    const data = "test data";
    console.log('Processing data:', data);
    return new Promise((resolve, reject) => {
        try {
            backend.process_data(data, (result) => {
                console.log('Received result from Python:', result);
                resolve(result);
            });
        } catch (error) {
            console.error('Error processing data:', error);
            reject(error);
        }
    });
}

function sendData(data) {
    if (!backend) {
        console.error('Backend not initialized');
        return Promise.reject('Backend not initialized');
    }
    console.log('Sending:', data);
    return new Promise((resolve, reject) => {
        try {
            backend.process_data(data, (result) => {
                console.log('Received result from Python:', result);

                appendMessage('Processed result: ' + result);
                resolve(result);
            });
        } catch (error) {
            console.error('Error processing data:', error);
            reject(error);
        }
    });
}

// (Python/PySide6 Backend) Initialize the web channel when the document is ready
if (document.readyState === 'loading') {
    console.log('Document still loading, waiting for DOMContentLoaded');
    // document.addEventListener('DOMContentLoaded', initWebChannel);
    document.addEventListener('DOMContentLoaded', function() {
        console.log('DOMContentLoaded fired, initializing web channel');
        initWebChannel();
    });
} else {
    console.log('Document already loaded, initializing immediately');
    initWebChannel();
}

// ------------------------------------------------------------
// END PYSIDE6 BRIDGE 
// ------------------------------------------------------------
