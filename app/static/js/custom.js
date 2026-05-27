document.addEventListener('DOMContentLoaded', function() {
    function showToast(title, message, type = 'success') {
        const toast = document.getElementById('toastNotification');

        document.getElementById('toastTitle').textContent = title;

        const icons = {
            'success': 'bi-check-circle text-success',
            'danger': 'bi-x-circle text-danger',
            'warning': 'bi-exclamation-triangle text-warning',
            'info': 'bi-info-circle text-info'
        };
        document.getElementById('toastIcon').className = 'me-2 ' + (icons[type] || icons['info']);

        const bsToast = new bootstrap.Toast(toast, { delay: 5000 });
        bsToast.show();
    }

    const alertMessages = document.querySelectorAll('.alert');
    alertMessages.forEach(function(alert) {
        const category = alert.classList.contains('alert-success') ? 'success' :
                        alert.classList.contains('alert-danger') ? 'danger' :
                        alert.classList.contains('alert-warning') ? 'warning' : 'info';

        let messageText = '';
        for (let i = 0; i < alert.childNodes.length; i++) {
            const node = alert.childNodes[i];
            if (node.nodeType === Node.TEXT_NODE) {
                messageText += node.textContent;
            }
        }
        messageText = messageText.trim();

        if (messageText) {
            showToast(messageText, messageText, category);
        }

        setTimeout(function() {
            alert.style.display = 'none';
        }, 100);
    });

    const forms = document.querySelectorAll('form[method="POST"]');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn && !submitBtn.classList.contains('no-spinner')) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processing...';
            }
        });
    });
});
