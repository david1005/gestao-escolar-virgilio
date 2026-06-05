let usuarioEditandoId = null;
let usuarioResetSenhaId = null;
let usuarioAtualId = null;
let turmas = [];
let cursos = [];
let usuarios = [];

const descricoesPerfil = {
    admin: 'Acesso completo ao sistema, incluindo usuarios e configuracoes.',
    ppdt: 'Pode cadastrar e acompanhar alunos, registros e ocorrencias.',
    biblioteca: 'Pode registrar atrasos e saidas antecipadas.',
    coordenador: 'Visualiza alunos, registros e ocorrencias dos cursos selecionados.',
    diretor_turma: 'Visualiza alunos, registros e ocorrencias da turma selecionada.'
};

async function carregarDados() {
    const [resMe, resUsuarios, resTurmas, resCursos] = await Promise.all([
        fetch('/api/auth/me'),
        fetch('/api/usuarios/'),
        fetch('/api/turmas/'),
        fetch('/api/cursos/')
    ]);

    const me = await resMe.json();
    usuarioAtualId = me.id;
    usuarios = await resUsuarios.json();
    turmas = await resTurmas.json();
    cursos = await resCursos.json();

    preencherSelects();
    mostrarCampoExtra();
    renderizarUsuarios(usuarios);
}

function preencherSelects() {
    preencherCheckboxCursos('curso_ids');
    preencherCheckboxCursos('editCursoIds');

    const opcoesTurmas = turmas.map(t => {
        const curso = cursos.find(c => c.id === t.curso_id);
        return `<option value="${t.id}">${t.ano}º ${t.letra} - ${curso ? curso.nome : ''}</option>`;
    }).join('');

    document.getElementById('turma_id').innerHTML = opcoesTurmas;
    document.getElementById('editTurmaId').innerHTML = opcoesTurmas;
}

function preencherCheckboxCursos(containerId) {
    const container = document.getElementById(containerId);
    container.innerHTML = cursos.map(c => `
        <div class="form-check">
            <input class="form-check-input" type="checkbox" value="${c.id}" id="${containerId}_${c.id}">
            <label class="form-check-label" for="${containerId}_${c.id}">${c.nome}</label>
        </div>
    `).join('');
}

function getPerfilLabel(perfil) {
    const labels = {
        admin: '<span class="badge bg-danger">Administrador</span>',
        ppdt: '<span class="badge bg-primary">PPDT</span>',
        biblioteca: '<span class="badge bg-info">Biblioteca</span>',
        coordenador: '<span class="badge bg-warning text-dark">Coordenador</span>',
        diretor_turma: '<span class="badge bg-secondary">Diretor de Turma</span>'
    };
    return labels[perfil] || perfil;
}

function getCursoNome(id) {
    const curso = cursos.find(c => c.id === id);
    return curso ? curso.nome : '-';
}

function getTurmaNome(id) {
    const turma = turmas.find(t => t.id === id);
    if (!turma) return '-';
    const curso = cursos.find(c => c.id === turma.curso_id);
    return `${turma.ano}º ${turma.letra} - ${curso ? curso.nome : ''}`;
}

function getAcessoLabel(usuario) {
    if (usuario.perfil === 'coordenador') {
        const ids = usuario.curso_ids || (usuario.curso_id ? [usuario.curso_id] : []);
        if (!ids.length) return '<span class="text-muted">Nenhum curso</span>';
        return ids.map(id => `<span class="badge bg-light text-dark border me-1 mb-1">${getCursoNome(id)}</span>`).join('');
    }

    if (usuario.perfil === 'diretor_turma') {
        return `<span class="badge bg-light text-dark border">${getTurmaNome(usuario.turma_id)}</span>`;
    }

    return '<span class="text-muted">Acesso geral</span>';
}

function formatarUltimoLogin(valor) {
    if (!valor) return '<span class="text-muted">Nunca acessou</span>';
    return new Date(valor).toLocaleString('pt-BR');
}

function renderizarUsuarios(lista) {
    const tbody = document.getElementById('tabelaUsuarios');
    if (lista.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">Nenhum usuario encontrado.</td></tr>';
        return;
    }

    tbody.innerHTML = lista.map(u => {
        const bloqueiaProprio = u.id === usuarioAtualId;
        const botaoInativar = bloqueiaProprio
            ? `<button class="btn btn-sm btn-outline-secondary" disabled title="Voce nao pode inativar seu proprio usuario"><i class="bi bi-slash-circle"></i></button>`
            : `<button class="btn btn-sm btn-outline-danger" onclick="inativarUsuario(${u.id})" title="Inativar usuario"><i class="bi bi-person-x"></i></button>`;

        return `
            <tr>
                <td>${u.nome}</td>
                <td>${u.email}</td>
                <td>
                    ${getPerfilLabel(u.perfil)}
                    <div class="small text-muted mt-1">${descricoesPerfil[u.perfil] || ''}</div>
                </td>
                <td>${getAcessoLabel(u)}</td>
                <td>${formatarUltimoLogin(u.ultimo_login)}</td>
                <td>${u.ativo ? '<span class="badge bg-success">Ativo</span>' : '<span class="badge bg-secondary">Inativo</span>'}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary me-1" onclick="abrirEdicao(${u.id})" title="Editar">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-warning me-1" onclick="abrirResetSenha(${u.id})" title="Redefinir senha">
                        <i class="bi bi-key"></i>
                    </button>
                    ${botaoInativar}
                </td>
            </tr>
        `;
    }).join('');
}

function normalizarTexto(texto) {
    return String(texto || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
}

function aplicarFiltros() {
    const busca = normalizarTexto(document.getElementById('filtroBusca').value);
    const perfil = document.getElementById('filtroPerfil').value;
    const status = document.getElementById('filtroStatus').value;

    const lista = usuarios.filter(u => {
        const texto = normalizarTexto(`${u.nome} ${u.email}`);
        return (
            (!busca || texto.includes(busca)) &&
            (!perfil || u.perfil === perfil) &&
            (status === '' || String(u.ativo) === status)
        );
    });

    renderizarUsuarios(lista);
}

function limparFiltros() {
    document.getElementById('filtroBusca').value = '';
    document.getElementById('filtroPerfil').value = '';
    document.getElementById('filtroStatus').value = '';
    renderizarUsuarios(usuarios);
}

function valoresCursosMarcados(containerId) {
    return Array.from(document.querySelectorAll(`#${containerId} input[type="checkbox"]:checked`))
        .map(input => parseInt(input.value));
}

function marcarCursos(containerId, valores) {
    const ids = new Set((valores || []).map(String));
    document.querySelectorAll(`#${containerId} input[type="checkbox"]`).forEach(input => {
        input.checked = ids.has(input.value);
    });
}

function atualizarDescricaoPerfil(prefixo = '') {
    const perfilId = prefixo ? 'editPerfil' : 'perfil';
    const descricaoId = prefixo ? 'editDescricaoPerfil' : 'descricaoPerfil';
    const perfil = document.getElementById(perfilId).value;
    document.getElementById(descricaoId).textContent = descricoesPerfil[perfil] || '';
}

function mostrarCampoExtra() {
    const perfil = document.getElementById('perfil').value;
    document.getElementById('campoCurso').classList.toggle('d-none', perfil !== 'coordenador');
    document.getElementById('campoTurma').classList.toggle('d-none', perfil !== 'diretor_turma');
    atualizarDescricaoPerfil();
}

function mostrarCampoExtraEdicao() {
    const perfil = document.getElementById('editPerfil').value;
    document.getElementById('editCampoCurso').classList.toggle('d-none', perfil !== 'coordenador');
    document.getElementById('editCampoTurma').classList.toggle('d-none', perfil !== 'diretor_turma');
    atualizarDescricaoPerfil('edit');
}

async function salvarUsuario() {
    const perfil = document.getElementById('perfil').value;
    const cursoIds = perfil === 'coordenador' ? valoresCursosMarcados('curso_ids') : [];
    const senha = document.getElementById('senha').value;

    if (perfil === 'coordenador' && cursoIds.length === 0) {
        alert('Selecione pelo menos um curso para o coordenador.');
        return;
    }
    if (senha.length < 8 || !/[A-Za-z]/.test(senha) || !/\d/.test(senha)) {
        alert('A senha deve ter pelo menos 8 caracteres, com letras e numeros.');
        return;
    }

    const dados = {
        nome: document.getElementById('nome').value,
        email: document.getElementById('email').value,
        senha,
        perfil,
        curso_ids: cursoIds,
        curso_id: cursoIds.length ? cursoIds[0] : null,
        turma_id: perfil === 'diretor_turma' ? parseInt(document.getElementById('turma_id').value) : null
    };

    const res = await fetch('/api/usuarios/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(dados)
    });

    if (res.ok) {
        bootstrap.Modal.getInstance(document.getElementById('modalUsuario')).hide();
        limparFormulario();
        carregarDados();
    } else {
        const erro = await res.json();
        alert(erro.detail || 'Erro ao salvar usuario!');
    }
}

function abrirEdicao(id) {
    const usuario = usuarios.find(u => u.id === id);
    if (!usuario) return;

    usuarioEditandoId = id;
    document.getElementById('editNome').value = usuario.nome;
    document.getElementById('editPerfil').value = usuario.perfil;
    document.getElementById('editAtivo').value = usuario.ativo;
    document.getElementById('editTurmaId').value = usuario.turma_id || '';
    document.getElementById('editAtivo').disabled = usuario.id === usuarioAtualId;
    marcarCursos('editCursoIds', usuario.curso_ids || (usuario.curso_id ? [usuario.curso_id] : []));
    mostrarCampoExtraEdicao();
    new bootstrap.Modal(document.getElementById('modalEditar')).show();
}

async function salvarEdicaoUsuario() {
    const perfil = document.getElementById('editPerfil').value;
    const cursoIds = perfil === 'coordenador' ? valoresCursosMarcados('editCursoIds') : [];

    if (perfil === 'coordenador' && cursoIds.length === 0) {
        alert('Selecione pelo menos um curso para o coordenador.');
        return;
    }

    const usuario = usuarios.find(u => u.id === usuarioEditandoId);
    const dados = {
        nome: document.getElementById('editNome').value,
        perfil,
        ativo: usuario && usuario.id === usuarioAtualId ? 1 : parseInt(document.getElementById('editAtivo').value),
        curso_ids: cursoIds,
        curso_id: cursoIds.length ? cursoIds[0] : null,
        turma_id: perfil === 'diretor_turma' ? parseInt(document.getElementById('editTurmaId').value) : null
    };

    const res = await fetch(`/api/usuarios/${usuarioEditandoId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(dados)
    });

    if (res.ok) {
        bootstrap.Modal.getInstance(document.getElementById('modalEditar')).hide();
        carregarDados();
    } else {
        const erro = await res.json();
        alert(erro.detail || 'Erro ao editar usuario!');
    }
}

function abrirResetSenha(id) {
    const usuario = usuarios.find(u => u.id === id);
    if (!usuario) return;
    usuarioResetSenhaId = id;
    document.getElementById('resetUsuarioNome').value = `${usuario.nome} (${usuario.email})`;
    document.getElementById('novaSenha').value = '';
    new bootstrap.Modal(document.getElementById('modalResetSenha')).show();
}

async function salvarResetSenha() {
    const novaSenha = document.getElementById('novaSenha').value;
    if (novaSenha.length < 8 || !/[A-Za-z]/.test(novaSenha) || !/\d/.test(novaSenha)) {
        alert('A senha deve ter pelo menos 8 caracteres, com letras e numeros.');
        return;
    }

    const res = await fetch(`/api/usuarios/${usuarioResetSenhaId}/resetar-senha`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nova_senha: novaSenha })
    });

    if (res.ok) {
        bootstrap.Modal.getInstance(document.getElementById('modalResetSenha')).hide();
        alert('Senha redefinida com sucesso.');
    } else {
        const erro = await res.json();
        alert(erro.detail || 'Erro ao redefinir senha.');
    }
}

async function inativarUsuario(id) {
    if (id === usuarioAtualId) {
        alert('Voce nao pode inativar seu proprio usuario.');
        return;
    }
    if (!confirm('Deseja inativar este usuario? O historico sera mantido.')) return;
    const res = await fetch(`/api/usuarios/${id}`, { method: 'DELETE' });
    if (res.ok) { carregarDados(); }
    else {
        const erro = await res.json();
        alert(erro.detail || 'Erro ao inativar usuario!');
    }
}

function limparFormulario() {
    document.getElementById('nome').value = '';
    document.getElementById('email').value = '';
    document.getElementById('senha').value = '';
    marcarCursos('curso_ids', []);
    document.getElementById('perfil').value = 'admin';
    mostrarCampoExtra();
}

document.getElementById('editPerfil').addEventListener('change', mostrarCampoExtraEdicao);
document.getElementById('filtroBusca').addEventListener('input', aplicarFiltros);
document.getElementById('filtroPerfil').addEventListener('change', aplicarFiltros);
document.getElementById('filtroStatus').addEventListener('change', aplicarFiltros);

carregarDados();
