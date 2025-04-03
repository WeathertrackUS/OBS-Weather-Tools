async function fetchAlerts() {
    try {
        const response = await fetch('/alerts');
        const alerts = await response.json();
        const alertText = alerts.map(alert => `${alert.event}: ${alert.details}`).join(' | ');
        document.getElementById('alert-text').textContent = alertText;
    } catch (error) {
        console.error('Error fetching alerts:', error);
    }
}

// Fetch alerts every 5 minutes
fetchAlerts();
setInterval(fetchAlerts, 300000);