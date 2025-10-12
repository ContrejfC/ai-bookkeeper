/**
 * Accessible Tooltips (WCAG 2.1 AA Compliant)
 * 
 * Usage:
 *   <button data-tooltip="Save changes" aria-describedby="tooltip-1">Save</button>
 * 
 * Features:
 * - Keyboard accessible (focus + hover)
 * - ESC to close
 * - aria-describedby for screen readers
 * - Auto-positioning
 */

(function() {
    'use strict';
    
    let activeTooltip = null;
    let tooltipElement = null;
    
    /**
     * Initialize tooltips on page load
     */
    function init() {
        // Create tooltip container
        tooltipElement = document.createElement('div');
        tooltipElement.id = 'tooltip-container';
        tooltipElement.role = 'tooltip';
        tooltipElement.style.cssText = `
            position: absolute;
            z-index: 9999;
            background: rgba(0, 0, 0, 0.9);
            color: white;
            padding: 0.5rem 0.75rem;
            border-radius: 0.375rem;
            font-size: 0.875rem;
            line-height: 1.25rem;
            max-width: 16rem;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.15s ease-in-out;
            white-space: nowrap;
        `;
        document.body.appendChild(tooltipElement);
        
        // Attach event listeners
        document.addEventListener('focusin', handleFocus);
        document.addEventListener('focusout', handleBlur);
        document.addEventListener('mouseover', handleMouseOver);
        document.addEventListener('mouseout', handleMouseOut);
        document.addEventListener('keydown', handleKeyDown);
    }
    
    /**
     * Show tooltip for an element
     */
    function showTooltip(element) {
        const text = element.getAttribute('data-tooltip');
        if (!text) return;
        
        activeTooltip = element;
        tooltipElement.textContent = text;
        
        // Position tooltip
        const rect = element.getBoundingClientRect();
        const tooltipRect = tooltipElement.getBoundingClientRect();
        
        // Try to position above the element
        let top = rect.top - tooltipRect.height - 8;
        let left = rect.left + (rect.width / 2) - (tooltipRect.width / 2);
        
        // If tooltip would be cut off at top, position below
        if (top < 8) {
            top = rect.bottom + 8;
        }
        
        // Keep tooltip within viewport horizontally
        if (left < 8) {
            left = 8;
        } else if (left + tooltipRect.width > window.innerWidth - 8) {
            left = window.innerWidth - tooltipRect.width - 8;
        }
        
        tooltipElement.style.top = `${top + window.scrollY}px`;
        tooltipElement.style.left = `${left + window.scrollX}px`;
        tooltipElement.style.opacity = '1';
        
        // Set aria-describedby if not already set
        if (!element.hasAttribute('aria-describedby')) {
            element.setAttribute('aria-describedby', 'tooltip-container');
        }
    }
    
    /**
     * Hide active tooltip
     */
    function hideTooltip() {
        if (activeTooltip) {
            tooltipElement.style.opacity = '0';
            activeTooltip = null;
        }
    }
    
    /**
     * Handle focus event
     */
    function handleFocus(event) {
        const target = event.target;
        if (target.hasAttribute('data-tooltip')) {
            showTooltip(target);
        }
    }
    
    /**
     * Handle blur event
     */
    function handleBlur(event) {
        const target = event.target;
        if (target === activeTooltip) {
            hideTooltip();
        }
    }
    
    /**
     * Handle mouse over event
     */
    function handleMouseOver(event) {
        const target = event.target.closest('[data-tooltip]');
        if (target && target !== activeTooltip) {
            showTooltip(target);
        }
    }
    
    /**
     * Handle mouse out event
     */
    function handleMouseOut(event) {
        const target = event.target.closest('[data-tooltip]');
        if (target === activeTooltip) {
            // Small delay to prevent flicker
            setTimeout(() => {
                if (activeTooltip === target) {
                    hideTooltip();
                }
            }, 100);
        }
    }
    
    /**
     * Handle key down (ESC to close)
     */
    function handleKeyDown(event) {
        if (event.key === 'Escape' && activeTooltip) {
            hideTooltip();
        }
    }
    
    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();

