/**
 * Loading indicators for async operations (UX Fix #2)
 */

// Show loading spinner
function showLoading(message = 'Loading...') {
    const spinner = document.getElementById('loading-spinner');
    if (spinner) {
        const messageEl = spinner.querySelector('p');
        if (messageEl) messageEl.textContent = message;
        spinner.classList.remove('hidden');
    }
}

// Hide loading spinner
function hideLoading() {
    const spinner = document.getElementById('loading-spinner');
    if (spinner) {
        spinner.classList.add('hidden');
    }
}

// Hook into htmx events for automatic spinner
document.addEventListener('htmx:beforeRequest', function(evt) {
    // Show spinner for specific operations
    const target = evt.detail.elt;
    if (target.dataset.showSpinner || target.classList.contains('needs-spinner')) {
        showLoading(target.dataset.spinnerMessage || 'Processing...');
    }
});

document.addEventListener('htmx:afterRequest', function(evt) {
    hideLoading();
});

// CSV Export with spinner
function exportWithSpinner(url, filename) {
    showLoading('Exporting CSV...');
    
    fetch(url)
        .then(response => response.blob())
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            hideLoading();
        })
        .catch(error => {
            console.error('Export failed:', error);
            alert('Export failed. Please try again.');
            hideLoading();
        });
}

// Make functions globally available
window.showLoading = showLoading;
window.hideLoading = hideLoading;
window.exportWithSpinner = exportWithSpinner;

