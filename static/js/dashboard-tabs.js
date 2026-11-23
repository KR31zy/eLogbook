/**
 * Dashboard-specific tab functionality
 * Enhances the supervision dashboard with tab functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Find the main content card that contains multiple sections
    const mainContentCard = document.querySelector('.col-lg-8 .card-modern');
    
    if (mainContentCard) {
        // Get all card headers in the main content area
        const cardHeaders = mainContentCard.querySelectorAll('.card-header');
        
        // If we have multiple headers, convert them to tabs
        if (cardHeaders.length > 1) {
            // Create tab container
            const tabContainer = document.createElement('div');
            tabContainer.className = 'dashboard-tabs mb-3';
            mainContentCard.prepend(tabContainer);
            
            // Create tabs from headers
            cardHeaders.forEach(function(header, index) {
                // Get the title from the header
                const title = header.querySelector('h5') ? 
                              header.querySelector('h5').textContent : 
                              'Tab ' + (index + 1);
                
                // Create tab button
                const tab = document.createElement('button');
                tab.className = 'dashboard-tab ' + (index === 0 ? 'active' : '');
                tab.textContent = title;
                tab.setAttribute('type', 'button');
                tab.setAttribute('data-tab-index', index);
                tab.setAttribute('tabindex', '0');
                tab.setAttribute('role', 'tab');
                tab.setAttribute('aria-selected', index === 0 ? 'true' : 'false');
                
                tabContainer.appendChild(tab);
                
                // Initially hide all but the first section
                if (index > 0) {
                    // Hide the header and its content
                    const section = getSectionFromHeader(header);
                    if (section) {
                        section.style.display = 'none';
                    }
                }
                
                // Add click event
                tab.addEventListener('click', function() {
                    // Deactivate all tabs
                    document.querySelectorAll('.dashboard-tab').forEach(function(t) {
                        t.classList.remove('active');
                        t.setAttribute('aria-selected', 'false');
                    });
                    
                    // Activate this tab
                    tab.classList.add('active');
                    tab.setAttribute('aria-selected', 'true');
                    
                    // Hide all sections
                    cardHeaders.forEach(function(h) {
                        const section = getSectionFromHeader(h);
                        if (section) {
                            section.style.display = 'none';
                        }
                    });
                    
                    // Show this section
                    const section = getSectionFromHeader(cardHeaders[index]);
                    if (section) {
                        section.style.display = '';
                    }
                });
                
                // Add keyboard navigation
                tab.addEventListener('keydown', function(event) {
                    if (event.key === 'Enter' || event.key === ' ') {
                        event.preventDefault();
                        tab.click();
                    } else if (event.key === 'ArrowRight') {
                        event.preventDefault();
                        const nextIndex = (index + 1) % cardHeaders.length;
                        const nextTab = tabContainer.querySelector(`[data-tab-index="${nextIndex}"]`);
                        if (nextTab) nextTab.focus();
                    } else if (event.key === 'ArrowLeft') {
                        event.preventDefault();
                        const prevIndex = (index - 1 + cardHeaders.length) % cardHeaders.length;
                        const prevTab = tabContainer.querySelector(`[data-tab-index="${prevIndex}"]`);
                        if (prevTab) prevTab.focus();
                    }
                });
            });
        }
    }
    
    // Helper function to get the entire section from a header
    function getSectionFromHeader(header) {
        // Get the header and its content
        let section = document.createElement('div');
        section.appendChild(header.cloneNode(true));
        
        // Get the next element (card body)
        let nextElement = header.nextElementSibling;
        if (nextElement && nextElement.classList.contains('card-body')) {
            section.appendChild(nextElement.cloneNode(true));
        }
        
        // Return the original elements
        return header.parentElement;
    }
});