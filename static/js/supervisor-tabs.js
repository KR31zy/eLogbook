/**
 * Supervisor Dashboard Tab Functionality
 * This script adds keyboard navigation and accessibility features to the supervisor dashboard
 */

document.addEventListener('DOMContentLoaded', function() {
    // Get all navigation links in the sidebar
    const navLinks = document.querySelectorAll('.sidebar .nav-link');
    
    // Add tabindex to make all nav links tabbable
    navLinks.forEach(function(link, index) {
        // Set tabindex to 0 to include in natural tab order
        link.setAttribute('tabindex', '0');
        
        // Add active class to current page link
        if (link.href === window.location.href) {
            link.classList.add('active');
        }
        
        // Add keyboard event listener for accessibility
        link.addEventListener('keydown', function(event) {
            // Activate link on Enter or Space key
            if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                link.click();
            }
        });
    });
    
    // Add functionality for card sections that might act as tabs
    const cardHeaders = document.querySelectorAll('.card-header');
    
    cardHeaders.forEach(function(header) {
        // Make card headers tabbable if they control content
        if (header.nextElementSibling && header.nextElementSibling.classList.contains('card-body')) {
            header.setAttribute('tabindex', '0');
            header.setAttribute('role', 'button');
            header.setAttribute('aria-expanded', 'true');
            
            // Add keyboard navigation
            header.addEventListener('keydown', function(event) {
                if (event.key === 'Enter' || event.key === ' ') {
                    event.preventDefault();
                    toggleCardBody(header);
                }
            });
            
            // Add click functionality
            header.addEventListener('click', function() {
                toggleCardBody(header);
            });
        }
    });
    
    // Function to toggle card body visibility
    function toggleCardBody(header) {
        const cardBody = header.nextElementSibling;
        if (cardBody && cardBody.classList.contains('card-body')) {
            if (cardBody.style.display === 'none') {
                cardBody.style.display = '';
                header.setAttribute('aria-expanded', 'true');
            } else {
                cardBody.style.display = 'none';
                header.setAttribute('aria-expanded', 'false');
            }
        }
    }

    // Create tab functionality for dashboard sections
    setupDashboardTabs();
});

/**
 * Sets up tab functionality for dashboard sections
 */
function setupDashboardTabs() {
    // Find all potential tab containers
    const tabContainers = document.querySelectorAll('.card-modern');
    
    tabContainers.forEach(function(container) {
        const headers = container.querySelectorAll('.card-header');
        
        // If we have multiple headers in a container, treat them as tabs
        if (headers.length > 1) {
            // Create a tab navigation if it doesn't exist
            let tabNav = container.querySelector('.tab-nav');
            
            if (!tabNav) {
                tabNav = document.createElement('div');
                tabNav.className = 'tab-nav d-flex border-bottom mb-3';
                container.prepend(tabNav);
                
                // Create tab buttons from headers
                headers.forEach(function(header, index) {
                    const tabButton = document.createElement('button');
                    tabButton.className = 'tab-button btn btn-link px-3 py-2 ' + 
                                         (index === 0 ? 'active' : '');
                    tabButton.textContent = header.querySelector('h5') ? 
                                           header.querySelector('h5').textContent : 
                                           'Tab ' + (index + 1);
                    tabButton.setAttribute('type', 'button');
                    tabButton.setAttribute('tabindex', '0');
                    tabButton.setAttribute('role', 'tab');
                    tabButton.setAttribute('aria-selected', index === 0 ? 'true' : 'false');
                    tabButton.setAttribute('data-tab-index', index);
                    
                    tabNav.appendChild(tabButton);
                    
                    // Initially hide all but first tab content
                    if (index > 0) {
                        header.style.display = 'none';
                        const content = header.nextElementSibling;
                        if (content && content.classList.contains('card-body')) {
                            content.style.display = 'none';
                        }
                    }
                    
                    // Add click event to tab buttons
                    tabButton.addEventListener('click', function() {
                        activateTab(container, index);
                    });
                    
                    // Add keyboard navigation
                    tabButton.addEventListener('keydown', function(event) {
                        if (event.key === 'Enter' || event.key === ' ') {
                            event.preventDefault();
                            activateTab(container, index);
                        } else if (event.key === 'ArrowRight') {
                            event.preventDefault();
                            const nextIndex = (index + 1) % headers.length;
                            const nextTab = tabNav.querySelector(`[data-tab-index="${nextIndex}"]`);
                            if (nextTab) nextTab.focus();
                        } else if (event.key === 'ArrowLeft') {
                            event.preventDefault();
                            const prevIndex = (index - 1 + headers.length) % headers.length;
                            const prevTab = tabNav.querySelector(`[data-tab-index="${prevIndex}"]`);
                            if (prevTab) prevTab.focus();
                        }
                    });
                });
            }
        }
    });
}

/**
 * Activates a specific tab in a container
 * @param {HTMLElement} container - The container element
 * @param {number} tabIndex - The index of the tab to activate
 */
function activateTab(container, tabIndex) {
    const headers = container.querySelectorAll('.card-header');
    const tabButtons = container.querySelectorAll('.tab-button');
    
    // Update tab buttons
    tabButtons.forEach(function(button, index) {
        if (index === tabIndex) {
            button.classList.add('active');
            button.setAttribute('aria-selected', 'true');
        } else {
            button.classList.remove('active');
            button.setAttribute('aria-selected', 'false');
        }
    });
    
    // Show/hide tab content
    headers.forEach(function(header, index) {
        const content = header.nextElementSibling;
        
        if (index === tabIndex) {
            header.style.display = '';
            if (content && content.classList.contains('card-body')) {
                content.style.display = '';
            }
        } else {
            header.style.display = 'none';
            if (content && content.classList.contains('card-body')) {
                content.style.display = 'none';
            }
        }
    });
}