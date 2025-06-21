

document.addEventListener('DOMContentLoaded', function() {
    
    if (document.querySelector('.footer')) {
        const currentYear = new Date().getFullYear();
        const footerYear = document.querySelector('.footer .text-muted');
        if (footerYear) {
            footerYear.textContent = footerYear.textContent.replace('{{ current_year }}', currentYear);
        }
    }
    
    
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
   
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
  
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert:not(.alert-important)');
        alerts.forEach(function(alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
    
 
    document.querySelectorAll('.confirm-delete').forEach(function(button) {
        button.addEventListener('click', function(e) {
            if (!confirm('هل أنت متأكد من أنك تريد حذف هذا العنصر؟')) {
                e.preventDefault();
            }
        });
    });
    
  
    function addRtlToArabicText() {
        const arabicPattern = /[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]/;
        const textElements = document.querySelectorAll('p, h1, h2, h3, h4, h5, h6, span, div, td, th, button, a, label, input, textarea');
        
        textElements.forEach(function(element) {
            if (element.innerText && arabicPattern.test(element.innerText)) {
                element.classList.add('rtl');
                element.dir = 'rtl';
            }
        });
    }
    
   
    addRtlToArabicText();
    
  
    document.querySelectorAll('.toggle-password').forEach(function(button) {
        button.addEventListener('click', function() {
            const passwordField = document.querySelector(this.getAttribute('data-target'));
            if (passwordField) {
                const type = passwordField.getAttribute('type') === 'password' ? 'text' : 'password';
                passwordField.setAttribute('type', type);
                
        
                this.innerHTML = type === 'password' ? 
                    '<i class="fas fa-eye"></i>' : 
                    '<i class="fas fa-eye-slash"></i>';
            }
        });
    });
});
