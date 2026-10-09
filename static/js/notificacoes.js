(function () {
    const esc = window.escapeHtml;
    const nav = document.querySelector('.navbar-nav.ms-auto');
    if (!nav) return;
    const item = document.createElement('li');
    item.className = 'nav-item dropdown d-lg-flex align-items-center ms-lg-2 my-2 my-lg-0';
    item.innerHTML = `
        <button class="btn btn-outline-light notificacoes-sino" type="button" id="sinoNotificacoes" data-bs-toggle="dropdown" aria-expanded="false" aria-label="Notificações" title="Notificações">
            <i class="bi bi-bell"></i><span class="badge bg-danger notificacoes-contador" hidden></span>
        </button>
        <div class="dropdown-menu dropdown-menu-end notificacoes-menu">
            <div class="d-flex justify-content-between align-items-center p-3 border-bottom">
                <strong>Notificações</strong><div class="d-flex gap-1">
                    <a class="btn btn-sm btn-link" href="/notificacoes/preferencias" title="Preferências de notificações" aria-label="Preferências de notificações"><i class="bi bi-sliders"></i></a>
                    <button type="button" class="btn btn-sm btn-link" data-ler-todas title="Marcar todas como lidas"><i class="bi bi-check2-all"></i></button>
                </div>
            </div>
            <div id="notificacoesRecentes" aria-live="polite"></div>
            <a class="d-block text-center p-3" href="/notificacoes">Todas as notificações</a>
        </div>`;
    nav.insertBefore(item, nav.lastElementChild);
    let page = 1;
    let pages = 1;
    let resumoEmCurso = false;
    const lista = document.getElementById('listaNotificacoes');

    function renderizar(items, container) {
        container.innerHTML = items.length ? items.map(n => {
            const icone = n.tipo === 'seguranca' ? 'bi-shield-exclamation text-danger' : n.tipo === 'alteracao' ? 'bi-pencil text-primary' : 'bi-clock-history text-warning';
            return `<div class="notificacao-item ${n.lida_em ? '' : 'nao-lida'}">
                <i class="bi ${icone}" aria-hidden="true"></i>
                <a href="/api/notificacoes/${Number(n.id)}/abrir" data-abrir="${Number(n.id)}"><strong>${esc(n.titulo)}</strong><p>${esc(n.mensagem)}</p>
                <time>${esc(new Date(n.atualizada_em).toLocaleString('pt-BR'))}${n.ativa ? '' : ' · Encerrada'}</time></a>
                ${n.lida_em ? '' : `<button type="button" class="btn btn-sm btn-outline-secondary" data-ler="${Number(n.id)}" title="Marcar como lida" aria-label="Marcar como lida"><i class="bi bi-check2"></i></button>`}
            </div>`;
        }).join('') : '<p class="text-center text-muted p-4 mb-0">Nenhuma notificação.</p>';
    }

    async function atualizarResumo() {
        if (resumoEmCurso) return;
        resumoEmCurso = true;
        try {
            const res = await fetch('/api/notificacoes/resumo');
            if (!res.ok) throw new Error();
            const dados = await res.json();
            const badge = item.querySelector('.notificacoes-contador');
            badge.hidden = dados.nao_lidas === 0;
            badge.textContent = dados.nao_lidas > 99 ? '99+' : dados.nao_lidas;
            item.querySelector('button').setAttribute('aria-label', `Notificações, ${dados.nao_lidas} não lidas`);
            renderizar(dados.items, document.getElementById('notificacoesRecentes'));
        } catch {
            document.getElementById('notificacoesRecentes').innerHTML = '<p class="text-muted p-3 mb-0">Não foi possível carregar as notificações.</p>';
        } finally { resumoEmCurso = false; }
    }

    async function carregarHistorico() {
        if (!lista) return;
        const params = new URLSearchParams({page, leitura: document.getElementById('filtroLeitura').value, tipo: document.getElementById('filtroTipoNotificacao').value});
        try {
            const res = await fetch(`/api/notificacoes/?${params}`);
            if (!res.ok) throw new Error();
            const dados = await res.json();
            pages = dados.pages;
            renderizar(dados.items, lista);
            document.getElementById('paginaNotificacoes').textContent = `${page} / ${pages} · ${dados.total} notificações`;
            document.getElementById('anteriorNotificacoes').disabled = page <= 1;
            document.getElementById('proximaNotificacoes').disabled = page >= pages;
        } catch { lista.innerHTML = '<p class="text-danger py-4">Erro ao carregar notificações.</p>'; }
    }

    document.addEventListener('click', async e => {
        const botao = e.target.closest('[data-ler], [data-ler-todas], [data-abrir]');
        if (!botao) return;
        e.preventDefault();
        e.stopPropagation();
        botao.disabled = true;
        try {
            const path = botao.hasAttribute('data-ler-todas') ? 'ler-todas' : `${botao.dataset.ler || botao.dataset.abrir}/ler`;
            const res = await fetch(`/api/notificacoes/${path}`, {method: 'PUT'});
            if (!res.ok) throw new Error();
            if (botao.dataset.abrir) { window.location.assign(botao.href); return; }
            await atualizarResumo();
            await carregarHistorico();
        } catch { alert('Não foi possível marcar a notificação como lida.'); }
        finally { botao.disabled = false; }
    });
    item.addEventListener('show.bs.dropdown', atualizarResumo);
    document.addEventListener('preferenciasnotificacoesalteradas', () => {
        atualizarResumo();
        carregarHistorico();
    });
    setInterval(() => { if (!document.hidden) atualizarResumo(); }, 300000);
    document.addEventListener('visibilitychange', () => { if (!document.hidden) atualizarResumo(); });
    if (lista) {
        ['filtroLeitura', 'filtroTipoNotificacao'].forEach(id => document.getElementById(id).addEventListener('change', () => { page = 1; carregarHistorico(); }));
        document.getElementById('anteriorNotificacoes').addEventListener('click', () => { if (page > 1) { page--; carregarHistorico(); } });
        document.getElementById('proximaNotificacoes').addEventListener('click', () => { if (page < pages) { page++; carregarHistorico(); } });
        carregarHistorico().then(atualizarResumo);
    } else atualizarResumo();
})();
