document.querySelectorAll('[data-submit-form]').forEach((form) => {
    form.addEventListener('submit', () => {
        if (!form.checkValidity()) return;
        const button = form.querySelector('button[type="submit"]');
        if (button) {
            button.disabled = true;
            button.textContent = 'Salvando…';
        }
    });
});

window.addEventListener('pageshow', () => {
    document.querySelectorAll('[data-submit-form] button[type="submit"]').forEach((button) => {
        if (button.dataset.label) button.textContent = button.dataset.label;
        button.disabled = false;
    });
});

document.querySelectorAll('[data-submit-form] button[type="submit"]').forEach((button) => {
    button.dataset.label = button.textContent;
});
