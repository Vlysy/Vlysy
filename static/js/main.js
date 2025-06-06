document.addEventListener('DOMContentLoaded', function() {
    // Loading overlay functionality
    const loadingOverlay = document.getElementById('loadingOverlay');
    const loadingText = document.getElementById('loadingText');
    
    // Show loading overlay function
    window.showLoading = function(message) {
        if (loadingText && message) {
            loadingText.textContent = message;
        }
        if (loadingOverlay) {
            loadingOverlay.classList.add('active');
        }
    };
    
    // Hide loading overlay function
    window.hideLoading = function() {
        if (loadingOverlay) {
            loadingOverlay.classList.remove('active');
        }
    };
    
    // Language selector functionality
    const languageButtons = document.querySelectorAll('.lang-btn');
    const languageInput = document.getElementById('language-input');
    
    // Initialize active language button based on current language
    const currentLanguage = languageInput ? languageInput.value : 'en';
    console.log('Current language set to:', currentLanguage);
    highlightActiveLanguage(currentLanguage);
    
    // Apply translations for current language
    applyTranslations(currentLanguage);
    
    // Add click event to language buttons
    languageButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const lang = this.getAttribute('data-lang');
            console.log('Language selected:', lang);
            
            // Set hidden input value for forms
            if (languageInput) {
                languageInput.value = lang;
            }
            
            // Highlight active language
            highlightActiveLanguage(lang);
            
            // Apply translations for selected language
            applyTranslations(lang);
            
            // Redirect to current page with language parameter
            const url = new URL(window.location.href);
            url.searchParams.set('lang', lang);
            window.location.href = url.toString();
        });
    });
    
    // Function to highlight active language button
    function highlightActiveLanguage(lang) {
        languageButtons.forEach(btn => {
            if (btn.getAttribute('data-lang') === lang) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });
    }
    
    // Function to apply translations
    function applyTranslations(lang) {
        console.log('Applying translations for language:', lang);
        if (!translations || !translations[lang]) {
            console.error('Translations not available for language:', lang);
            return;
        }
        
        document.querySelectorAll('.translate').forEach(element => {
            const key = element.getAttribute('data-key');
            if (key && translations[lang][key]) {
                element.textContent = translations[lang][key];
            } else if (key) {
                // If translation not found, try to use English as fallback
                if (translations['en'] && translations['en'][key]) {
                    element.textContent = translations['en'][key];
                } else {
                    console.warn('Missing translation for key:', key, 'in language:', lang);
                }
            }
        });
        
        // Also apply translations to data-placeholder attributes
        document.querySelectorAll('[data-translate-placeholder]').forEach(element => {
            const key = element.getAttribute('data-translate-placeholder');
            if (key && translations[lang][key]) {
                element.placeholder = translations[lang][key];
            }
        });
        
        // Update the document language attribute
        document.documentElement.setAttribute('lang', lang);
    }
    
    // File upload handling
    const fileInput = document.getElementById('resume-file');
    const fileNameDisplay = document.querySelector('.file-name-display');
    
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            if (fileNameDisplay) {
                if (this.files.length > 0) {
                    fileNameDisplay.textContent = this.files[0].name;
                    fileNameDisplay.style.display = 'block';
                } else {
                    fileNameDisplay.style.display = 'none';
                }
            }
        });
    }
    
    // Upload/Paste toggle
    const uploadOption = document.getElementById('upload-option');
    const pasteOption = document.getElementById('paste-option');
    const uploadSection = document.getElementById('upload-section');
    const pasteSection = document.getElementById('paste-section');
    
    if (uploadOption && pasteOption) {
        uploadOption.addEventListener('change', function() {
            if (this.checked) {
                uploadSection.style.display = 'block';
                pasteSection.style.display = 'none';
            }
        });
        
        pasteOption.addEventListener('change', function() {
            if (this.checked) {
                uploadSection.style.display = 'none';
                pasteSection.style.display = 'block';
            }
        });
    }
    
    // Tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Set copyright year to current year
    const currentYear = new Date().getFullYear();
    const yearElements = document.querySelectorAll('.current-year');
    yearElements.forEach(element => {
        element.textContent = currentYear.toString();
    });
    
    // Handle score animations
    const scoreCircle = document.querySelector('.overall-score-circle');
    if (scoreCircle) {
        setTimeout(() => {
            scoreCircle.style.opacity = '1';
        }, 300);
    }
    
    // Progress bar animations
    const progressBars = document.querySelectorAll('.progress-bar');
    if (progressBars.length > 0) {
        progressBars.forEach((bar, index) => {
            setTimeout(() => {
                bar.style.width = bar.getAttribute('aria-valuenow') + '%';
            }, 500 + (index * 150));
        });
    }
    
    // Card animations
    const animatedCards = document.querySelectorAll('.animate-card');
    if (animatedCards.length > 0) {
        animatedCards.forEach((card, index) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            
            setTimeout(() => {
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, 100 + (index * 150));
        });
    }
    
    // Add loading animation for form submission
    const resumeForm = document.getElementById('resume-form');
    if (resumeForm) {
        resumeForm.addEventListener('submit', function(e) {
            // Show loading message based on input type
            const uploadOption = document.getElementById('upload-option');
            const isFileUpload = uploadOption && uploadOption.checked;
            
            if (isFileUpload) {
                const fileInput = document.getElementById('resume-file');
                if (fileInput && fileInput.files.length > 0) {
                    showLoading('Uploading and analyzing your CV...');
                }
            } else {
                const textInput = document.getElementById('resume-text');
                if (textInput && textInput.value.trim() !== '') {
                    showLoading('Analyzing your CV text...');
                }
            }
        });
    }
    
    // Add loading for anschreiben form
    const anschreibenForm = document.getElementById('anschreiben-form');
    if (anschreibenForm) {
        anschreibenForm.addEventListener('submit', function(e) {
            const jobDescription = document.getElementById('job-description');
            if (jobDescription && jobDescription.value.trim() !== '') {
                showLoading('Generating your personalized cover letter...');
            }
        });
    }
});
