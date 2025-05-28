document.querySelectorAll('.auth-modal__close').forEach(btn => {
    btn.addEventListener('click', function() {
        const modal = this.closest('.auth-modal-overlay');
        if (modal) {
            modal.classList.add('fade-out');
            setTimeout(() => modal.remove(), 300);
        }
    });
});