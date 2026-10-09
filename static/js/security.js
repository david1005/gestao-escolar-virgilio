function getCookieValue(nome) {
    return document.cookie
        .split('; ')
        .find(item => item.startsWith(`${nome}=`))
        ?.split('=')
        .slice(1)
        .join('=') || '';
}

window.escapeHtml = function(valor) {
    return String(valor ?? '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#039;');
};

const fetchOriginal = window.fetch.bind(window);

window.fetch = function(url, options = {}) {
    const metodo = String(options.method || 'GET').toUpperCase();
    const protegido = ['POST', 'PUT', 'PATCH', 'DELETE'].includes(metodo);

    if (protegido) {
        const headers = new Headers(options.headers || {});
        const csrfToken = getCookieValue('csrf_token');
        if (csrfToken && !headers.has('x-csrf-token')) {
            headers.set('x-csrf-token', decodeURIComponent(csrfToken));
        }
        options = { ...options, headers };
    }

    return fetchOriginal(url, options);
};
