document.addEventListener('DOMContentLoaded', () => {
    const deleteForms = document.querySelectorAll('.delete-form');
    const modal = document.getElementById('deleteModal');
    const confirmBtn = document.getElementById('confirmDeleteBtn');
    const cancelBtn = document.getElementById('cancelDeleteBtn');
    let selectedForm = null;

    deleteForms.forEach(form => {
        const triggerBtn = form.querySelector('.open-modal-btn');
        if (triggerBtn) {
            triggerBtn.addEventListener('click', () => {
                selectedForm = form;
                modal.style.display = 'flex';
            });
        }
    });

    confirmBtn.addEventListener('click', () => {
        if (selectedForm) {
            selectedForm.submit();
            selectedForm = null;
        }
        modal.style.display = 'none';
    });

    cancelBtn.addEventListener('click', () => {
        modal.style.display = 'none';
        selectedForm = null;
    });

    window.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
            selectedForm = null;
        }
    });
});
