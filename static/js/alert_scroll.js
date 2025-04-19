async function fetchAlerts() {
    try {
        const response = await fetch('/alerts');
        const alerts = await response.json();
        const alertText = alerts.map(alert => `${alert.event}: ${alert.details}`).join(' | ');
        const alertTextElement = document.getElementById('alert-text');
        alertTextElement.textContent = alertText;

        // Dynamically adjust the animation duration based on text width
        const containerWidth = alertTextElement.parentElement.offsetWidth;
        const textWidth = alertTextElement.scrollWidth;
        const animationDuration = Math.max(15, (textWidth / containerWidth) * 15); // Adjust duration proportionally
        alertTextElement.style.animationDuration = `${animationDuration}s`;
    } catch (error) {
        console.error('Error fetching alerts:', error);
    }
}

// Fetch alerts every 5 minutes
fetchAlerts();
setInterval(fetchAlerts, 300000);