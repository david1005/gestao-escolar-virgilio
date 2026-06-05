(function () {
    const storageKey = 'gestaoEscolarTema';

    function getPreferredTheme() {
        const savedTheme = localStorage.getItem(storageKey);
        if (savedTheme === 'dark' || savedTheme === 'light') return savedTheme;
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }

    function applyTheme(theme) {
        document.documentElement.setAttribute('data-bs-theme', theme);
        document.documentElement.setAttribute('data-theme', theme);
    }

    function updateButton(button) {
        const isDark = document.documentElement.getAttribute('data-bs-theme') === 'dark';
        button.innerHTML = `<i class="bi ${isDark ? 'bi-sun' : 'bi-moon-stars'}"></i>`;
        button.title = isDark ? 'Ativar modo claro' : 'Ativar modo escuro';
        button.setAttribute('aria-label', button.title);
    }

    function toggleTheme(button) {
        const currentTheme = document.documentElement.getAttribute('data-bs-theme') || 'light';
        const nextTheme = currentTheme === 'dark' ? 'light' : 'dark';
        localStorage.setItem(storageKey, nextTheme);
        applyTheme(nextTheme);
        updateButton(button);
        document.dispatchEvent(new CustomEvent('themechange', { detail: { theme: nextTheme } }));
    }

    function createButton(isFloating) {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = isFloating
            ? 'btn btn-light theme-toggle-btn theme-toggle-floating shadow-sm'
            : 'btn btn-outline-light theme-toggle-btn ms-lg-2 my-2 my-lg-0';
        button.addEventListener('click', () => toggleTheme(button));
        updateButton(button);
        return button;
    }

    function mountToggle() {
        const userNav = document.querySelector('.navbar-nav.ms-auto');
        if (userNav) {
            const item = document.createElement('li');
            item.className = 'nav-item d-flex align-items-center';
            item.appendChild(createButton(false));
            userNav.insertBefore(item, userNav.firstChild);
            return;
        }

        document.body.appendChild(createButton(true));
    }

    applyTheme(getPreferredTheme());

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', mountToggle);
    } else {
        mountToggle();
    }
})();
