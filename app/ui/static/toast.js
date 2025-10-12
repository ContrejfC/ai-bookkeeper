/**
 * Toast Notifications (WCAG 2.1 AA Compliant)
 * 
 * Usage:
 *   Toast.show('Operation successful', 'success');
 *   Toast.show('Error occurred', 'error');
 *   Toast.show('Processing...', 'info');
 * 
 * Features:
 * - Queued notifications
 * - Auto-dismiss with configurable duration
 * - ESC to dismiss
 * - aria-live for screen readers
 * - Keyboard accessible
 */

window.Toast = (function() {
    'use strict';
    
    let container = null;
    let queue = [];
    let activeToast = null;
    
    const DURATIONS = {
        success: 3500,  // 3.5 seconds
        info: 3500,
        warning: 4500,
        error: 6000     // 6 seconds for errors
    };
    
    const ICONS = {
        success: `<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
        </svg>`,
        error: `<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
        </svg>`,
        warning: `<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
        </svg>`,
        info: `<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/>
        </svg>`
    };
    
    const COLORS = {
        success: 'bg-green-600 text-white',
        error: 'bg-red-600 text-white',
        warning: 'bg-yellow-500 text-gray-900',
        info: 'bg-blue-600 text-white'
    };
    
    /**
     * Initialize toast container
     */
    function init() {
        if (container) return;
        
        container = document.createElement('div');
        container.id = 'toast-container';
        container.setAttribute('aria-live', 'polite');
        container.setAttribute('aria-atomic', 'true');
        container.setAttribute('role', 'status');
        container.style.cssText = `
            position: fixed;
            top: 1rem;
            right: 1rem;
            z-index: 10000;
            min-width: 20rem;
            max-width: 28rem;
        `;
        document.body.appendChild(container);
        
        // ESC to dismiss
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && activeToast) {
                dismissToast();
            }
        });
    }
    
    /**
     * Show a toast notification
     */
    function show(message, type = 'info', options = {}) {
        init();
        
        const duration = options.duration || DURATIONS[type] || DURATIONS.info;
        const toast = {
            message,
            type,
            duration,
            persistent: options.persistent || false
        };
        
        if (activeToast) {
            queue.push(toast);
        } else {
            displayToast(toast);
        }
    }
    
    /**
     * Display a toast
     */
    function displayToast(toast) {
        const element = document.createElement('div');
        element.className = `toast-item ${COLORS[toast.type]} rounded-lg shadow-lg p-4 mb-2 flex items-center justify-between transition-all duration-300 transform translate-x-0`;
        element.style.cssText = `
            animation: slideIn 0.3s ease-out;
        `;
        
        element.innerHTML = `
            <div class="flex items-center flex-1">
                <div class="flex-shrink-0">
                    ${ICONS[toast.type]}
                </div>
                <div class="ml-3 text-sm font-medium">
                    ${escapeHtml(toast.message)}
                </div>
            </div>
            <button 
                type="button" 
                class="ml-4 flex-shrink-0 inline-flex text-current hover:opacity-75 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-white rounded"
                aria-label="Dismiss notification"
            >
                <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
                </svg>
            </button>
        `;
        
        // Add dismiss handler
        const dismissButton = element.querySelector('button');
        dismissButton.addEventListener('click', () => dismissToast());
        
        container.appendChild(element);
        activeToast = { element, toast };
        
        // Auto-dismiss after duration (unless persistent)
        if (!toast.persistent) {
            setTimeout(() => {
                dismissToast();
            }, toast.duration);
        }
    }
    
    /**
     * Dismiss current toast
     */
    function dismissToast() {
        if (!activeToast) return;
        
        const { element } = activeToast;
        element.style.cssText = `
            animation: slideOut 0.3s ease-in;
            opacity: 0;
            transform: translateX(100%);
        `;
        
        setTimeout(() => {
            if (element.parentNode) {
                element.parentNode.removeChild(element);
            }
            activeToast = null;
            
            // Show next toast in queue
            if (queue.length > 0) {
                const next = queue.shift();
                displayToast(next);
            }
        }, 300);
    }
    
    /**
     * Escape HTML to prevent XSS
     */
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    /**
     * Success toast shorthand
     */
    function success(message, options) {
        show(message, 'success', options);
    }
    
    /**
     * Error toast shorthand
     */
    function error(message, options) {
        show(message, 'error', options);
    }
    
    /**
     * Warning toast shorthand
     */
    function warning(message, options) {
        show(message, 'warning', options);
    }
    
    /**
     * Info toast shorthand
     */
    function info(message, options) {
        show(message, 'info', options);
    }
    
    // Add keyframe animations
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateX(100%);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
        
        @keyframes slideOut {
            from {
                opacity: 1;
                transform: translateX(0);
            }
            to {
                opacity: 0;
                transform: translateX(100%);
            }
        }
    `;
    document.head.appendChild(style);
    
    // Public API
    return {
        show,
        success,
        error,
        warning,
        info,
        dismiss: dismissToast
    };
})();

