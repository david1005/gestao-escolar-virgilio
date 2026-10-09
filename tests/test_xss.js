const assert = require('node:assert/strict');

global.window = {
    fetch: async () => ({ ok: true })
};
global.document = { cookie: '' };

require('../static/js/security.js');

assert.equal(
    window.escapeHtml('<img src=x onerror="alert(1)">'),
    '&lt;img src=x onerror=&quot;alert(1)&quot;&gt;'
);
assert.equal(
    window.escapeHtml("' & < > \""),
    '&#039; &amp; &lt; &gt; &quot;'
);
assert.equal(window.escapeHtml(null), '');

console.log('Testes de escape HTML: OK');
