document.addEventListener('DOMContentLoaded', function() {
    // Handle signature file input
    const signatureInput = document.getElementById('signature');
    if (signatureInput) {
        signatureInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                // Validate file type
                if (!file.type.startsWith('image/')) {
                    alert('Please select an image file');
                    e.target.value = '';
                    return;
                }

                // Validate file size (max 2MB)
                if (file.size > 2 * 1024 * 1024) {
                    alert('File size should not exceed 2MB');
                    e.target.value = '';
                    return;
                }

                // Preview image
                const reader = new FileReader();
                reader.onload = function(e) {
                    const preview = document.createElement('img');
                    preview.src = e.target.result;
                    preview.style.maxWidth = '300px';
                    preview.style.marginTop = '10px';
                    
                    const previewContainer = document.createElement('div');
                    previewContainer.id = 'signature-preview';
                    previewContainer.appendChild(preview);

                    const existingPreview = document.getElementById('signature-preview');
                    if (existingPreview) {
                        existingPreview.remove();
                    }

                    signatureInput.parentNode.appendChild(previewContainer);
                };
                reader.readAsDataURL(file);
            }
        });
    }

    // Print functionality
    const printButton = document.querySelector('.btn-print');
    if (printButton) {
        printButton.addEventListener('click', function(e) {
            e.preventDefault();
            window.print();
        });
    }

    // Smooth scroll to sections from table of contents
    const tocLinks = document.querySelectorAll('.toc-item');
    tocLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const targetId = this.getAttribute('data-target');
            const targetSection = document.getElementById(targetId);
            if (targetSection) {
                e.preventDefault();
                targetSection.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });

    // Add section navigation
    const sections = document.querySelectorAll('.report-section');
    sections.forEach((section, index) => {
        if (index > 0) { // Skip for cover page
            const nav = document.createElement('div');
            nav.className = 'section-navigation';
            nav.innerHTML = `
                ${index > 1 ? `<a href="#section-${index-1}" class="nav-prev">Previous</a>` : ''}
                ${index < sections.length - 1 ? `<a href="#section-${index+1}" class="nav-next">Next</a>` : ''}
            `;
            section.appendChild(nav);
        }
        section.id = `section-${index}`;
    });

    // Add navigation styles
    const style = document.createElement('style');
    style.textContent = `
        .section-navigation {
            display: flex;
            justify-content: space-between;
            margin-top: 20px;
            padding-top: 10px;
            border-top: 1px solid #e9ecef;
        }

        .nav-prev,
        .nav-next {
            color: #007bff;
            text-decoration: none;
            padding: 5px 10px;
            border: 1px solid #007bff;
            border-radius: 4px;
        }

        .nav-prev:hover,
        .nav-next:hover {
            background-color: #007bff;
            color: white;
        }

        @media print {
            .section-navigation {
                display: none;
            }
        }
    `;
    document.head.appendChild(style);
});