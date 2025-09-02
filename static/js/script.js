// Handle flash messages
document.addEventListener('DOMContentLoaded', function() {
    // Close flash messages when clicked
    document.querySelectorAll('.flash').forEach(flash => {
        flash.addEventListener('click', () => {
            flash.style.animation = 'slideOut 0.5s forwards';
            setTimeout(() => flash.remove(), 500);
        });
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            flash.style.animation = 'slideOut 0.5s forwards';
            setTimeout(() => flash.remove(), 500);
        }, 5000);
    });
});