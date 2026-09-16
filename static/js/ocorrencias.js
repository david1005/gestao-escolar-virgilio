let alunos = [];
let turmas = [];
let cursos = [];
let ocorrencias = [];
let ocorrenciasFiltradas = [];
let ocorrenciaEditandoId = null;
let paginaAtualOcorrencias = 1;
let tiposOcorrencia = [];
let medidasOcorrencia = [];

const medidasPadrao = {
    registro: 'S\u00f3 registro',
    advertencia: 'Advert\u00eancia + Notifica\u00e7\u00e3o ao respons\u00e1vel',
    suspensao: 'Suspens\u00e3o + Notifica\u00e7\u00e3o ao respons\u00e1vel'
};

async function carregarListasOperacionais() {
    try {
        const res = await fetch('/api/sistema/listas-operacionais');
        if (!res.ok) return;
        const listas = await res.json();
        tiposOcorrencia = Array.isArray(listas.tipos_ocorrencia) ? listas.tipos_ocorrencia : [];
        medidasOcorrencia = Array.isArray(listas.medidas_ocorrencia) ? listas.medidas_ocorrencia : [];
        if (medidasOcorrencia[0]) medidasPadrao.registro = medidasOcorrencia[0];
        if (medidasOcorrencia[1]) medidasPadrao.advertencia = medidasOcorrencia[1];
        if (medidasOcorrencia[2]) medidasPadrao.suspensao = medidasOcorrencia[2];
        preencherSelectsOperacionais();
    } catch (erro) {
        console.warn('Listas operacionais nao carregadas.', erro);
    }
}

function preencherOptions(id, lista, manterValor = true) {
    const select = document.getElementById(id);
    if (!select || !lista.length) return;
    const valorAtual = select.value;
    select.innerHTML = lista.map(item => `<option value="${item}">${item}</option>`).join('');
    if (manterValor && lista.includes(valorAtual)) select.value = valorAtual;
}

function preencherSelectsOperacionais() {
    preencherOptions('tipo', tiposOcorrencia);
    preencherOptions('editTipo', tiposOcorrencia);
    preencherOptions('medida', medidasOcorrencia);
    preencherOptions('editMedida', medidasOcorrencia);
}

async function carregarDados() {
    await carregarListasOperacionais();
    const [resAlunos, resTurmas, resCursos, resOcorrencias] = await Promise.all([
        fetch('/api/alunos/'),
        fetch('/api/turmas/'),
        fetch('/api/cursos/'),
        fetch('/api/ocorrencias/')
    ]);

    alunos = await resAlunos.json();
    turmas = await resTurmas.json();
    cursos = await resCursos.json();
    ocorrencias = await resOcorrencias.json();

    document.getElementById('data').valueAsDate = new Date();
    preencherFiltroTurmas();
    renderizarResumo();
    ocorrenciasFiltradas = ocorrencias;
    paginaAtualOcorrencias = 1;
    renderizarOcorrencias(ocorrenciasFiltradas);
}

function normalizarTexto(texto) {
    return String(texto || '')
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .toLowerCase();
}

function getAluno(id) {
    return alunos.find(a => a.id === id);
}

function getNomeAluno(id) {
    const aluno = getAluno(id);
    return aluno ? aluno.nome : '-';
}

function getTurmaAluno(alunoId) {
    const aluno = getAluno(alunoId);
    if (!aluno) return '-';
    const turma = turmas.find(t => t.id === aluno.turma_id);
    if (!turma) return '-';
    const curso = cursos.find(c => c.id === turma.curso_id);
    return `${turma.ano}\u00ba ${turma.letra} - ${curso ? curso.nome : ''}`;
}

function preencherFiltroTurmas() {
    const filtro = document.getElementById('filtroTurma');
    const valorAtual = filtro.value;
    filtro.innerHTML = '<option value="">Todas as turmas</option>';

    turmas
        .slice()
        .sort((a, b) => a.ano - b.ano || String(a.letra).localeCompare(String(b.letra)))
        .forEach(turma => {
            const curso = cursos.find(c => c.id === turma.curso_id);
            filtro.innerHTML += `<option value="${turma.id}">${turma.ano}\u00ba ${turma.letra} - ${curso ? curso.nome : ''}</option>`;
        });

    filtro.value = valorAtual;
}

function renderizarResumo() {
    const hoje = new Date().toISOString().slice(0, 10);
    const mesAtual = hoje.slice(5, 7);

    document.getElementById('totalHoje').textContent =
        ocorrencias.filter(o => o.data === hoje).length;
    document.getElementById('totalAbertas').textContent =
        ocorrencias.filter(o => (o.status || 'Aberta') === 'Aberta').length;
    document.getElementById('totalGraves').textContent =
        ocorrencias.filter(o => (o.gravidade || 'Leve') === 'Grave').length;
    document.getElementById('totalResolvidasMes').textContent =
        ocorrencias.filter(o => (o.status || '') === 'Resolvida' && o.data && o.data.substring(5, 7) === mesAtual).length;
}

function getMedidaBadge(medida) {
    if (medida === medidasPadrao.registro) return '<span class="badge bg-secondary">Registro</span>';
    if ((medida || '').includes('Advert')) return '<span class="badge bg-warning text-dark">Advertencia</span>';
    return '<span class="badge bg-danger">Suspensao</span>';
}

function getGravidadeBadge(gravidade) {
    const valor = gravidade || 'Leve';
    if (valor === 'Grave') return '<span class="badge bg-danger">Grave</span>';
    if (valor === 'Media') return '<span class="badge bg-warning text-dark">Media</span>';
    return '<span class="badge bg-success">Leve</span>';
}

function getStatusBadge(status) {
    const valor = status || 'Aberta';
    if (valor === 'Resolvida') return '<span class="badge bg-success">Resolvida</span>';
    if (valor === 'Em acompanhamento') return '<span class="badge bg-info text-dark">Em acompanhamento</span>';
    return '<span class="badge bg-warning text-dark">Aberta</span>';
}

function escaparHtml(valor) {
    const div = document.createElement('div');
    div.textContent = String(valor || '');
    return div.innerHTML;
}

function montarTextoCompacto(valor, ocorrenciaId, campo, titulo) {
    const texto = String(valor || '').trim();
    if (!texto) return '<span class="text-muted">-</span>';

    const textoSeguro = escaparHtml(texto);
    const precisaExpandir = texto.length > 120 || texto.includes('\n');

    return `
        <div class="texto-compacto">
            <div class="texto-compacto__previa">${textoSeguro}</div>
            ${precisaExpandir ? `
                <button type="button" class="btn btn-link btn-sm texto-compacto__botao" onclick="abrirTextoOcorrencia(${ocorrenciaId}, '${campo}')" title="Ver ${titulo.toLowerCase()} completa">
                    <i class="bi bi-eye me-1"></i>Ver completa
                </button>
            ` : ''}
        </div>
    `;
}

function abrirTextoOcorrencia(id, campo) {
    const ocorrencia = ocorrencias.find(o => o.id === id);
    if (!ocorrencia) return;

    const titulos = {
        descricao: 'Descrição da ocorrência',
        acoes_tomadas: 'Ações tomadas'
    };

    document.getElementById('modalTextoOcorrenciaTitulo').textContent = titulos[campo] || 'Detalhes da ocorrência';
    document.getElementById('modalTextoOcorrenciaConteudo').textContent = ocorrencia[campo] || '-';
    new bootstrap.Modal(document.getElementById('modalTextoOcorrencia')).show();
}

function renderizarOcorrencias(lista) {
    const tbody = document.getElementById('tabelaOcorrencias');

    if (lista.length === 0) {
        tbody.innerHTML = '<tr><td colspan="13" class="text-center text-muted">Nenhuma ocorrencia encontrada.</td></tr>';
        atualizarInfoPaginacaoOcorrencias(0, 1);
        return;
    }

    const porPagina = parseInt(document.getElementById('itensPorPagina')?.value || '25');
    const totalPaginas = Math.max(1, Math.ceil(lista.length / porPagina));
    paginaAtualOcorrencias = Math.min(paginaAtualOcorrencias, totalPaginas);
    const inicio = (paginaAtualOcorrencias - 1) * porPagina;
    const listaPagina = lista.slice(inicio, inicio + porPagina);

    tbody.innerHTML = listaPagina.map(o => {
        const notificado = o.responsavel_notificado
            ? '<i class="bi bi-check-circle-fill text-success"></i>'
            : '<i class="bi bi-x-circle-fill text-danger"></i>';
        const logEdicao = o.editado_por
            ? `<br><small class="text-muted"><i class="bi bi-pencil me-1"></i>Editado por ${o.editado_por} em ${new Date(o.editado_em).toLocaleString('pt-BR')}</small>`
            : '';

        return `
            <tr>
                <td>${o.data}</td>
                <td>${getNomeAluno(o.aluno_id)}${logEdicao}</td>
                <td>${getTurmaAluno(o.aluno_id)}</td>
                <td><span class="badge bg-dark">${o.numero_ocorrencia}\u00aa</span></td>
                <td>${o.tipo}</td>
                <td>${getGravidadeBadge(o.gravidade)}</td>
                <td>${getStatusBadge(o.status)}</td>
                <td class="coluna-texto">${montarTextoCompacto(o.descricao, o.id, 'descricao', 'descrição')}</td>
                <td>${getMedidaBadge(o.medida)}</td>
                <td class="coluna-texto coluna-acoes-tomadas">${montarTextoCompacto(o.acoes_tomadas, o.id, 'acoes_tomadas', 'ações')}</td>
                <td>${escaparHtml(o.registrado_por)}</td>
                <td class="text-center">${notificado}</td>
                <td class="ocorrencias-botoes">
                    <a class="btn btn-sm btn-outline-secondary me-1" href="/aluno/${o.aluno_id}" title="Historico do aluno">
                        <i class="bi bi-person-lines-fill"></i>
                    </a>
                    <button class="btn btn-sm btn-outline-success me-1" onclick="gerarPDF(${o.id})" title="Imprimir termo">
                        <i class="bi bi-file-pdf"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-secondary me-1" onclick="abrirAnexos('ocorrencia', ${o.id}, 'Documentos da ocorrencia')" title="Documentos">
                        <i class="bi bi-paperclip"></i>
                    </button>
                    ${perfilUsuario === 'admin' || perfilUsuario === 'ppdt' ? `
                    <button class="btn btn-sm btn-outline-primary me-1" onclick="abrirEdicao(${o.id})" title="Editar">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="excluirOcorrencia(${o.id})" title="Excluir">
                        <i class="bi bi-trash"></i>
                    </button>` : ''}
                </td>
            </tr>
        `;
    }).join('');

    atualizarInfoPaginacaoOcorrencias(lista.length, totalPaginas);
}

function atualizarInfoPaginacaoOcorrencias(total, totalPaginas) {
    const porPagina = parseInt(document.getElementById('itensPorPagina')?.value || '25');
    const inicio = total === 0 ? 0 : (paginaAtualOcorrencias - 1) * porPagina + 1;
    const fim = Math.min(total, paginaAtualOcorrencias * porPagina);
    document.getElementById('infoPaginacaoOcorrencias').textContent = `${inicio}-${fim} de ${total} ocorrencias encontradas`;
    document.getElementById('paginaAtualOcorrencias').textContent = `${paginaAtualOcorrencias}/${totalPaginas}`;
}

function mudarPaginaOcorrencias(direcao) {
    const porPagina = parseInt(document.getElementById('itensPorPagina')?.value || '25');
    const totalPaginas = Math.max(1, Math.ceil(ocorrenciasFiltradas.length / porPagina));
    paginaAtualOcorrencias = Math.min(Math.max(1, paginaAtualOcorrencias + direcao), totalPaginas);
    renderizarOcorrencias(ocorrenciasFiltradas);
}

function montarItemAluno(aluno, origem) {
    return `
        <button type="button" class="list-group-item list-group-item-action sugestao-aluno" data-aluno-id="${aluno.id}" data-origem="${origem}">
            <div class="fw-semibold">${aluno.nome}</div>
            <div class="small text-muted">${getTurmaAluno(aluno.id)} - Matricula ${aluno.matricula}</div>
        </button>
    `;
}

function renderizarSugestoesAluno(termo, containerId, origem) {
    const sugestoes = document.getElementById(containerId);
    const busca = normalizarTexto(termo);

    if (busca.length < 2) {
        sugestoes.innerHTML = '';
        return;
    }

    const encontrados = alunos
        .filter(a =>
            normalizarTexto(a.nome).includes(busca) ||
            normalizarTexto(a.matricula).includes(busca) ||
            normalizarTexto(getTurmaAluno(a.id)).includes(busca)
        )
        .slice(0, 8);

    sugestoes.innerHTML = encontrados.length
        ? encontrados.map(a => montarItemAluno(a, origem)).join('')
        : '<div class="list-group-item text-muted small">Nenhum aluno encontrado.</div>';
}

document.getElementById('buscaAluno').addEventListener('input', function () {
    document.getElementById('aluno_id').value = '';
    renderizarSugestoesAluno(this.value, 'sugestoesAluno', 'modal');
});

document.getElementById('filtroNome').addEventListener('input', function () {
    renderizarSugestoesAluno(this.value, 'sugestoesFiltroAluno', 'filtro');
});

document.addEventListener('click', function (event) {
    const botao = event.target.closest('.sugestao-aluno');
    if (!botao) {
        if (!event.target.closest('#sugestoesFiltroAluno') && event.target.id !== 'filtroNome') {
            document.getElementById('sugestoesFiltroAluno').innerHTML = '';
        }
        return;
    }

    const aluno = alunos.find(a => a.id === parseInt(botao.dataset.alunoId));
    if (!aluno) return;

    if (botao.dataset.origem === 'modal') {
        selecionarAluno(aluno.id, aluno.nome);
    } else {
        document.getElementById('filtroNome').value = aluno.nome;
        document.getElementById('sugestoesFiltroAluno').innerHTML = '';
        filtrar();
    }
});

async function selecionarAluno(id, nome) {
    document.getElementById('aluno_id').value = id;
    document.getElementById('buscaAluno').value = nome;
    document.getElementById('sugestoesAluno').innerHTML = '';

    const res = await fetch(`/api/ocorrencias/contar/${id}`);
    const dados = await res.json();
    const alerta = document.getElementById('alertaMedida');
    const select = document.getElementById('medida');
    const gravidade = document.getElementById('gravidade');
    const status = document.getElementById('status');
    const total = dados.total;

    if (total === 0) {
        alerta.className = 'alert alert-info';
        alerta.innerHTML = `<i class="bi bi-info-circle me-2"></i>Este e o <strong>1\u00ba registro</strong> deste aluno. Medida sugerida: <strong>${medidasPadrao.registro}</strong>.`;
        select.value = medidasPadrao.registro;
        gravidade.value = 'Leve';
    } else if (total === 1) {
        alerta.className = 'alert alert-warning';
        alerta.innerHTML = `<i class="bi bi-exclamation-triangle me-2"></i>Este aluno ja tem <strong>${total} ocorrencia</strong>. Medida sugerida: <strong>${medidasPadrao.advertencia}</strong>.`;
        select.value = medidasPadrao.advertencia;
        gravidade.value = 'Media';
    } else {
        alerta.className = 'alert alert-danger';
        alerta.innerHTML = `<i class="bi bi-x-octagon me-2"></i>Este aluno ja tem <strong>${total} ocorrencias</strong>. Medida sugerida: <strong>${medidasPadrao.suspensao}</strong>.`;
        select.value = medidasPadrao.suspensao;
        gravidade.value = 'Grave';
    }

    status.value = 'Aberta';
    alerta.classList.remove('d-none');
}

async function salvarOcorrencia() {
    const alunoId = document.getElementById('aluno_id').value;
    if (!alunoId) { alert('Selecione um aluno!'); return; }

    const resContar = await fetch(`/api/ocorrencias/contar/${alunoId}`);
    const contagem = await resContar.json();

    const dados = {
        aluno_id: parseInt(alunoId),
        data: document.getElementById('data').value,
        tipo: document.getElementById('tipo').value,
        descricao: document.getElementById('descricao').value,
        medida: document.getElementById('medida').value,
        gravidade: document.getElementById('gravidade').value,
        status: document.getElementById('status').value,
        acoes_tomadas: document.getElementById('acoes_tomadas').value,
        registrado_por: document.getElementById('registrado_por').value,
        responsavel_notificado: document.getElementById('responsavel_notificado').checked,
        numero_ocorrencia: contagem.total + 1
    };

    const res = await fetch('/api/ocorrencias/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(dados)
    });

    if (res.ok) {
        await res.json();
        bootstrap.Modal.getInstance(document.getElementById('modalOcorrencia')).hide();
        limparFormulario();
        carregarDados();
    } else {
        alert('Erro ao salvar ocorrencia. Verifique os campos!');
    }
}

function abrirEdicao(id) {
    const ocorrencia = ocorrencias.find(o => o.id === id);
    if (!ocorrencia) return;

    ocorrenciaEditandoId = id;
    document.getElementById('editTipo').value = ocorrencia.tipo;
    document.getElementById('editDescricao').value = ocorrencia.descricao;
    document.getElementById('editMedida').value = ocorrencia.medida;
    document.getElementById('editGravidade').value = ocorrencia.gravidade || 'Leve';
    document.getElementById('editStatus').value = ocorrencia.status || 'Aberta';
    document.getElementById('editAcoesTomadas').value = ocorrencia.acoes_tomadas || '';
    document.getElementById('editResponsavelNotificado').checked = ocorrencia.responsavel_notificado;
    document.getElementById('editadoPor').value = '';

    new bootstrap.Modal(document.getElementById('modalEdicao')).show();
}

async function salvarEdicao() {
    const editadoPor = document.getElementById('editadoPor').value;
    if (!editadoPor) { alert('Informe quem esta editando!'); return; }

    const dados = {
        tipo: document.getElementById('editTipo').value,
        descricao: document.getElementById('editDescricao').value,
        medida: document.getElementById('editMedida').value,
        gravidade: document.getElementById('editGravidade').value,
        status: document.getElementById('editStatus').value,
        acoes_tomadas: document.getElementById('editAcoesTomadas').value,
        responsavel_notificado: document.getElementById('editResponsavelNotificado').checked,
        editado_por: editadoPor
    };

    const res = await fetch(`/api/ocorrencias/${ocorrenciaEditandoId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(dados)
    });

    if (res.ok) {
        bootstrap.Modal.getInstance(document.getElementById('modalEdicao')).hide();
        ocorrenciaEditandoId = null;
        carregarDados();
    } else {
        alert('Erro ao editar ocorrencia!');
    }
}

function gerarPDF(id) {
    const o = ocorrencias.find(o => o.id === id);
    if (!o) return;

    const textoDocumento = (valor) => String(valor || '-')
        .replaceAll('So registro', 'Só registro')
        .replaceAll('Advertencia', 'Advertência')
        .replaceAll('Notificacao', 'Notificação')
        .replaceAll('Suspensao', 'Suspensão')
        .replaceAll('Responsavel', 'Responsável')
        .replaceAll('Coordenacao', 'Coordenação')
        .replaceAll('Ocorrencia', 'Ocorrência')
        .replaceAll('Informacoes', 'Informações')
        .replaceAll('Gestao', 'Gestão')
        .replaceAll('Educacao', 'Educação')
        .replaceAll('Virgilio Tavora', 'Virgílio Távora');

    const nomeAluno = getNomeAluno(o.aluno_id);
    const turma = getTurmaAluno(o.aluno_id);
    const aluno = getAluno(o.aluno_id);
    const responsavel = aluno ? aluno.responsavel : '-';
    const matricula = aluno ? aluno.matricula : '-';
    const contatoResponsavel = aluno ? aluno.contato_responsavel : '-';
    const numDoc = String(o.id).padStart(4, '0');
    const logoUrl = `${window.location.origin}/static/img/logo-escola.png`;

    const conteudo = `
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Registro de Ocorrência</title>
            <style>
                @page { size: A4; margin: 14mm; }
                body { font-family: Arial, sans-serif; color: #222; font-size: 13px; line-height: 1.35; }
                .topo { display: flex; align-items: center; gap: 16px; border-bottom: 2px solid #222; padding-bottom: 12px; }
                .logo { width: 76px; height: 76px; object-fit: contain; }
                .cabecalho { flex: 1; text-align: center; }
                .cabecalho .orgao { font-size: 11px; text-transform: uppercase; color: #555; }
                h2 { margin: 4px 0; font-size: 20px; }
                h3 { margin: 0; color: #555; font-size: 16px; }
                .numero { text-align: right; font-size: 12px; margin-top: 10px; color: #555; }
                .secao { margin-top: 18px; }
                .secao-titulo { font-weight: 700; background: #f1f3f5; border: 1px solid #ccc; padding: 7px 9px; margin-bottom: 8px; }
                .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 7px 18px; }
                .campo { margin-bottom: 7px; }
                .campo span { font-weight: bold; }
                .texto-box { border: 1px solid #ccc; min-height: 52px; padding: 8px; white-space: pre-wrap; }
                .ciencia { border: 1px solid #ccc; padding: 9px; margin-top: 10px; font-size: 12px; }
                .assinaturas { display: grid; grid-template-columns: repeat(2, 1fr); gap: 38px 32px; margin-top: 58px; }
                .assinatura { text-align: center; }
                .assinatura .linha-ass { border-top: 1px solid #333; margin-bottom: 5px; }
                .assinatura small { display: block; font-size: 11px; color: #555; }
                .log { font-size: 12px; color: #777; margin-top: 12px; }
                .rodape { text-align: center; margin-top: 28px; font-size: 11px; color: #777; }
            </style>
        </head>
        <body>
            <div class="topo">
                <img class="logo" src="${logoUrl}" onerror="this.style.display='none'">
                <div class="cabecalho">
                    <h2>EEEP Governador Virgílio Távora</h2>
                    <h3>Registro de Ocorrência Escolar</h3>
                </div>
            </div>
            <div class="numero">Documento N\u00ba ${numDoc} | Impresso em ${new Date().toLocaleString('pt-BR')}</div>

            <div class="secao">
                <div class="secao-titulo">1. Identificação do aluno</div>
                <div class="grid">
                    <div class="campo"><span>Aluno:</span> ${textoDocumento(nomeAluno)}</div>
                    <div class="campo"><span>Matricula:</span> ${matricula}</div>
                    <div class="campo"><span>Turma:</span> ${textoDocumento(turma)}</div>
                    <div class="campo"><span>Data da ocorrência:</span> ${o.data}</div>
                    <div class="campo"><span>Responsável:</span> ${textoDocumento(responsavel)}</div>
                    <div class="campo"><span>Contato:</span> ${contatoResponsavel}</div>
                </div>
            </div>

            <div class="secao">
                <div class="secao-titulo">2. Dados da ocorrência</div>
                <div class="grid">
                    <div class="campo"><span>N\u00ba da ocorrência do aluno:</span> ${o.numero_ocorrencia}\u00aa ocorrência</div>
                    <div class="campo"><span>Tipo:</span> ${textoDocumento(o.tipo)}</div>
                    <div class="campo"><span>Gravidade:</span> ${o.gravidade || 'Leve'}</div>
                    <div class="campo"><span>Status:</span> ${o.status || 'Aberta'}</div>
                    <div class="campo"><span>Registrado por:</span> ${textoDocumento(o.registrado_por)}</div>
                    <div class="campo"><span>Responsável notificado:</span> ${o.responsavel_notificado ? 'Sim' : 'Não'}</div>
                </div>
            </div>

            <div class="secao">
                <div class="secao-titulo">3. Descrição do ocorrido</div>
                <div class="texto-box">${textoDocumento(o.descricao)}</div>
            </div>

            <div class="secao">
                <div class="secao-titulo">4. Medidas e encaminhamentos</div>
                <div class="campo"><span>Medida tomada:</span> ${textoDocumento(o.medida)}</div>
                <div class="campo"><span>Ações tomadas:</span></div>
                <div class="texto-box">${textoDocumento(o.acoes_tomadas)}</div>
                <div class="ciencia">
                    Declaro estar ciente das informações registradas neste documento e das medidas adotadas pela escola.
                </div>
            </div>

            ${o.editado_por ? `<div class="log">* Editado por ${o.editado_por} em ${new Date(o.editado_em).toLocaleString('pt-BR')}</div>` : ''}

            <div class="assinaturas">
                <div class="assinatura">
                    <div class="linha-ass"></div>
                    <div>Aluno</div>
                    <small>${textoDocumento(nomeAluno)}</small>
                </div>
                <div class="assinatura">
                    <div class="linha-ass"></div>
                    <div>Responsável</div>
                    <small>${textoDocumento(responsavel)}</small>
                </div>
                <div class="assinatura">
                    <div class="linha-ass"></div>
                    <div>Coordenação</div>
                    <small>${textoDocumento(o.registrado_por)}</small>
                </div>
                <div class="assinatura">
                    <div class="linha-ass"></div>
                    <div>Testemunha / Professor</div>
                    <small>Nome e assinatura</small>
                </div>
            </div>

            <div class="rodape">Documento gerado pelo Sistema de Gestão Escolar</div>
        </body>
        </html>
    `;

    const janela = window.open('', '_blank');
    janela.document.write(conteudo);
    janela.document.close();
    janela.print();
}

async function excluirOcorrencia(id) {
    if (!confirm('Deseja excluir esta ocorrencia?')) return;
    const res = await fetch(`/api/ocorrencias/${id}`, { method: 'DELETE' });
    if (res.ok) { carregarDados(); }
    else { alert('Erro ao excluir ocorrencia!'); }
}

function limparFormulario() {
    document.getElementById('buscaAluno').value = '';
    document.getElementById('aluno_id').value = '';
    document.getElementById('descricao').value = '';
    document.getElementById('acoes_tomadas').value = '';
    document.getElementById('registrado_por').value = '';
    document.getElementById('gravidade').value = 'Leve';
    document.getElementById('status').value = 'Aberta';
    document.getElementById('responsavel_notificado').checked = false;
    document.getElementById('alertaMedida').classList.add('d-none');
}

function filtrar() {
    const nome = normalizarTexto(document.getElementById('filtroNome').value);
    const turmaId = document.getElementById('filtroTurma').value;
    const tipo = document.getElementById('filtroTipo').value;
    const gravidade = document.getElementById('filtroGravidade').value;
    const status = document.getElementById('filtroStatus').value;
    const data = document.getElementById('filtroData').value;

    ocorrenciasFiltradas = ocorrencias.filter(o => {
        const aluno = getAluno(o.aluno_id);
        const nomeAluno = normalizarTexto(getNomeAluno(o.aluno_id));
        return (
            (!nome || nomeAluno.includes(nome)) &&
            (!turmaId || (aluno && aluno.turma_id === parseInt(turmaId))) &&
            (!tipo || o.tipo === tipo) &&
            (!gravidade || (o.gravidade || 'Leve') === gravidade) &&
            (!status || (o.status || 'Aberta') === status) &&
            (!data || o.data === data)
        );
    });

    paginaAtualOcorrencias = 1;
    renderizarOcorrencias(ocorrenciasFiltradas);
}

document.getElementById('filtroNome').addEventListener('input', filtrar);
document.getElementById('filtroTurma').addEventListener('change', filtrar);
document.getElementById('filtroTipo').addEventListener('change', filtrar);
document.getElementById('filtroGravidade').addEventListener('change', filtrar);
document.getElementById('filtroStatus').addEventListener('change', filtrar);
document.getElementById('filtroData').addEventListener('change', filtrar);
document.getElementById('itensPorPagina').addEventListener('change', () => {
    paginaAtualOcorrencias = 1;
    renderizarOcorrencias(ocorrenciasFiltradas);
});

carregarDados();
