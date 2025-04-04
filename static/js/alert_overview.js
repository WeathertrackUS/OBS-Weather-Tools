let currentIndex = 0;
let alerts = [];

async function fetchAlerts() {
    try {
        const response = await fetch('/alerts');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        alerts = await response.json();
        console.debug('Fetched alerts:', alerts); // Log the fetched alerts
        if (alerts.length > 0) {
            currentIndex = 0;
            displayAlert(alerts[currentIndex]);
        } else {
            displayNoAlerts();
        }
    } catch (error) {
        console.error('Error fetching alerts:', error);
        displayNoAlerts();
    }
}

function displayAlert(alert) {
    if (!alert) {
        console.error('Invalid alert object:', alert);
        displayNoAlerts();
        return;
    }

    const container = document.getElementById('alert-container');

    // Set background color based on alert type
    container.className = 'alert-container'; // Reset classes
    if (alert.event && alert.event.toLowerCase().includes('severe thunderstorm')) {
        container.classList.add('severe-thunderstorm');
    } else if (alert.event && alert.event.toLowerCase().includes('tornado')) {
        container.classList.add('tornado-warning');
    }

    document.getElementById('alert-header').textContent = alert.event || 'Unknown Event';
    document.getElementById('alert-details').textContent = alert.details || 'No details available';
    document.getElementById('alert-locations').textContent = alert.locations || 'No locations specified';
    document.getElementById('alert-expiration').textContent = `Expires: ${alert.expiration_time ? new Date(alert.expiration_time).toLocaleString() : 'Unknown'}`;

    enableScrollingIfNeeded(); // Check if scrolling is needed for locations
}

function displayNoAlerts() {
    const container = document.getElementById('alert-container');
    container.className = 'alert-container no-alerts'; // Add no-alerts class

    document.getElementById('alert-header').textContent = 'No Active Alerts';
    document.getElementById('alert-details').textContent = '';
    document.getElementById('alert-locations').textContent = '';
    document.getElementById('alert-expiration').textContent = '';
}

function cycleAlerts() {
    if (alerts.length > 0) {
        currentIndex = (currentIndex + 1) % alerts.length;
        console.debug('Cycling to alert:', alerts[currentIndex]);
        displayAlert(alerts[currentIndex]);
    } else {
        console.warn('No alerts to cycle through.');
        displayNoAlerts();
    }
}

function enableScrollingIfNeeded() {
    const locationsElement = document.getElementById('alert-locations');

    // Measure the text width and container width
    const textWidth = locationsElement.scrollWidth;
    const containerWidth = locationsElement.offsetWidth;

    // Check if scrolling is needed
    if (textWidth > containerWidth) {
        locationsElement.classList.add('scrollable');
    } else {
        locationsElement.classList.remove('scrollable');
    }
}

// Fetch alerts initially and then every 5 minutes
fetchAlerts();
setInterval(fetchAlerts, 300000);

// Cycle through alerts every 10 seconds
setInterval(cycleAlerts, 10000);

// Call the function initially and whenever the content changes
enableScrollingIfNeeded();
setInterval(enableScrollingIfNeeded, 1000); // Recheck periodically in case of dynamic updates