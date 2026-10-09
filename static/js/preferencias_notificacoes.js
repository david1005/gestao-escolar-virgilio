(function () {
    const form = document.getElementById('formPreferenciasNotificacoes');
    if (!form) return;
    const campos = document.getElementById('camposPreferenciasNotificacoes');
    const status = document.getElementById('statusPreferenciasNotificacoes');
    const repetir = document.getElementById('recarregarPreferenciasNotificacoes');
    const tipos = ['ocorrencia_antiga', 'retorno_pendente', 'alteracao'];
    const endpoint = '/api/notificacoes/preferencias';

    function mensagem(texto, erro = false) {
        status.textContent = texto;
        status.className = erro ? 'small text-danger' : 'small text-muted';
    }

    async function carregar() {
        campos.disabled = true;
        repetir.hidden = true;
        mensagem('Carregando preferências...');
        try {
            const res = await fetch(endpoint);
            if (!res.ok) throw new Error();
            const dados = await res.json();
            tipos.forEach(tipo => { form.elements[tipo].checked = dados[tipo]; });
            campos.disabled = false;
            mensagem('');
        } catch {
            mensagem('Não foi possível carregar suas preferências.', true);
            repetir.hidden = false;
        }
    }

    form.addEventListener('submit', async e => {
        e.preventDefault();
        if (campos.disabled) return;
        const dados = Object.fromEntries(tipos.map(tipo => [tipo, form.elements[tipo].checked]));
        campos.disabled = true;
        mensagem('Salvando...');
        try {
            const res = await fetch(endpoint, {method: 'PUT', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(dados)});
            if (!res.ok) throw new Error();
            mensagem('Preferências salvas.');
            document.dispatchEvent(new CustomEvent('preferenciasnotificacoesalteradas'));
        } catch { mensagem('Não foi possível salvar. Tente novamente.', true); }
        finally { campos.disabled = false; }
    });
    repetir.addEventListener('click', carregar);
    carregar();
})();
