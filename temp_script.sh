#!/bin/bash
sed -i "/function setupLanguageToggle() {/,/}/ s/}/    \n    // Make sure the correct button has 'active' class by default\n    languageButtons.forEach(button => {\n        if (button.getAttribute('value') === document.querySelector('input[name=\"language\"]:checked').value) {\n            button.classList.add('active');\n        }\n    });\n}/" static/js/main.js
