let alunos = [];
let turmas = [];
let cursos = [];
let registros = [];
let registrosFiltrados = [];
let registroEditandoId = null;
let paginaAtualRegistros = 1;

const motivosPorTipo = {
    'Atraso': [
        'Transporte',
        'Consulta m\u00e9dica',
        'Exame m\u00e9dico',
        'Atestado m\u00e9dico',
        'Problema odontol\u00f3gico',
        'Compromisso familiar',
        'Quest\u00e3o judicial',
        'Atividade externa da escola'
    ],
    'Sa\u00edda antecipada': [
        'Consulta m\u00e9dica',
        'Exame m\u00e9dico',
        'Mal-estar',
        'Respons\u00e1vel solicitou',
        'Problema odontol\u00f3gico',
        'Compromisso familiar',
        'Doen\u00e7a na fam\u00edlia',
        'Quest\u00e3o judicial',
        'Atividade externa da escola'
    ]
};

async function carregarListasOperacionais() {
    try {
        const res = await fetch('/api/sistema/listas-operacionais');
        if (!res.ok) return;
        const listas = await res.json();
        if (Array.isArray(listas.motivos_atraso) && listas.motivos_atraso.length) {
            motivosPorTipo['Atraso'] = listas.motivos_atraso;
        }
        if (Array.isArray(listas.motivos_saida) && listas.motivos_saida.length) {
            motivosPorTipo['Sa\u00edda antecipada'] = listas.motivos_saida;
        }
    } catch (erro) {
        console.warn('Listas operacionais nao carregadas.', erro);
    }
}

function atualizarListaMotivos() {
    const tipo = document.getElementById('tipo').value;
    const select = document.getElementById('motivoSelect');
    const motivos = motivosPorTipo[tipo] || motivosPorTipo['Atraso'];

    select.innerHTML = '<option value="">Selecione um motivo...</option>' +
        motivos.map(motivo => `<option value="${motivo}">${motivo}</option>`).join('') +
        '<option value="outro">Outro motivo...</option>';

    atualizarMotivo();
}

function atualizarMotivo() {
    const select = document.getElementById('motivoSelect');
    const input = document.getElementById('motivo');
    if (select.value === 'outro') {
        input.classList.remove('d-none');
        input.value = '';
        input.focus();
    } else {
        input.classList.add('d-none');
        input.value = select.value;
    }
}

async function carregarDados() {
    await carregarListasOperacionais();
    const [resAlunos, resTurmas, resCursos, resRegistros] = await Promise.all([
        fetch('/api/alunos/'),
        fetch('/api/turmas/'),
        fetch('/api/cursos/'),
        fetch('/api/registros/')
    ]);

    alunos = await resAlunos.json();
    turmas = await resTurmas.json();
    cursos = await resCursos.json();
    registros = await resRegistros.json();

    document.getElementById('data').valueAsDate = new Date();
    preencherFiltroTurmas();
    atualizarListaMotivos();
    atualizarCamposSaida();
    renderizarResumoRegistros();
    registrosFiltrados = registros;
    paginaAtualRegistros = 1;
    renderizarRegistros(registrosFiltrados);
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

function renderizarResumoRegistros() {
    const hoje = new Date().toISOString().slice(0, 10);
    const mesAtual = hoje.slice(5, 7);

    document.getElementById('totalAtrasosHoje').textContent =
        registros.filter(r => r.data === hoje && r.tipo === 'Atraso').length;
    document.getElementById('totalSaidasHoje').textContent =
        registros.filter(r => r.data === hoje && r.tipo !== 'Atraso').length;
    document.getElementById('totalMes').textContent =
        registros.filter(r => r.data && r.data.substring(5, 7) === mesAtual).length;
    document.getElementById('totalComDocumento').textContent =
        registros.filter(r => r.tem_documento).length;
}

function getNomeAluno(id) {
    const a = alunos.find(a => a.id === id);
    return a ? a.nome : '-';
}

function getTurmaAluno(aluno_id) {
    const a = alunos.find(a => a.id === aluno_id);
    if (!a) return '-';
    const t = turmas.find(t => t.id === a.turma_id);
    if (!t) return '-';
    const c = cursos.find(c => c.id === t.curso_id);
    return `${t.ano}º ${t.letra} - ${c ? c.nome : ''}`;
}

function normalizarTexto(texto) {
    return String(texto || '')
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .toLowerCase();
}

function ehSaidaAntecipada(tipo) {
    return tipo !== 'Atraso';
}

function montarItemAluno(a, origem) {
    return `
        <button type="button" class="list-group-item list-group-item-action sugestao-aluno" data-aluno-id="${a.id}" data-origem="${origem}">
            <div class="fw-semibold">${a.nome}</div>
            <div class="small text-muted">${getTurmaAluno(a.id)} - Matricula ${a.matricula}</div>
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

function atualizarCamposSaida(prefixo = '') {
    const editando = prefixo === 'edit';
    const tipo = document.getElementById(editando ? 'editTipo' : 'tipo')?.value;
    const tipoSaida = document.getElementById(editando ? 'editTipoSaida' : 'tipoSaida')?.value;
    const grupoTipoSaida = document.getElementById(editando ? 'editGrupoTipoSaida' : 'grupoTipoSaida');
    const grupoAulaRetorno = document.getElementById(editando ? 'editGrupoAulaRetorno' : 'grupoAulaRetorno');
    const grupoStatusRetorno = document.getElementById(editando ? 'editGrupoStatusRetorno' : 'grupoStatusRetorno');
    const ehSaida = ehSaidaAntecipada(tipo);

    grupoTipoSaida?.classList.toggle('d-none', !ehSaida);
    grupoAulaRetorno?.classList.toggle('d-none', !ehSaida || tipoSaida !== 'temporaria');
    grupoStatusRetorno?.classList.toggle('d-none', !ehSaida || tipoSaida !== 'temporaria');
}

function descricaoRetorno(registro) {
    if (!ehSaidaAntecipada(registro.tipo)) return '-';
    if (registro.tipo_saida !== 'temporaria') return '<span class="badge bg-secondary">Não retorna</span>';

    const status = registro.status_retorno || 'Pendente';
    const classe = status === 'Retornou'
        ? 'bg-success'
        : status === 'Nao retornou'
            ? 'bg-danger'
            : 'bg-info text-dark';
    const previsto = registro.aula_retorno_prevista ? `${registro.aula_retorno_prevista}ª aula` : '-';
    const real = registro.aula_retorno_real ? `<div class="small text-muted">Voltou: ${registro.aula_retorno_real}ª aula</div>` : '';
    return `<span class="badge ${classe}">${status}</span><div class="small">Previsto: ${previsto}</div>${real}`;
}

function formatarDataRegistro(registro) {
    const data = registro.data
        ? new Date(`${registro.data}T00:00:00`).toLocaleDateString('pt-BR')
        : '-';
    if (!registro.criado_em) return data;

    const criadoEm = new Date(registro.criado_em);
    const hora = criadoEm.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
    return `${data}<div class="small text-muted">Registrado ${hora}</div>`;
}

function renderizarRegistros(lista) {
    const tbody = document.getElementById('tabelaRegistros');

    if (lista.length === 0) {
        tbody.innerHTML = '<tr><td colspan="10" class="text-center text-muted">Nenhum registro encontrado.</td></tr>';
        atualizarInfoPaginacaoRegistros(0, 1);
        return;
    }

    const porPagina = parseInt(document.getElementById('itensPorPagina')?.value || '25');
    const totalPaginas = Math.max(1, Math.ceil(lista.length / porPagina));
    paginaAtualRegistros = Math.min(paginaAtualRegistros, totalPaginas);
    const inicio = (paginaAtualRegistros - 1) * porPagina;
    const listaPagina = lista.slice(inicio, inicio + porPagina);

    tbody.innerHTML = listaPagina.map(r => {
        const badgeTipo = r.tipo === 'Atraso'
            ? '<span class="badge bg-warning text-dark">Atraso</span>'
            : '<span class="badge bg-danger">Saída antecipada</span>';

        const documento = r.tem_documento
            ? '<i class="bi bi-check-circle-fill text-success"></i>'
            : '<i class="bi bi-x-circle-fill text-danger"></i>';
        const botaoConfirmarRetorno = ehSaidaAntecipada(r.tipo) && r.tipo_saida === 'temporaria' && (r.status_retorno || 'Pendente') === 'Pendente'
            ? `<button class="btn btn-sm btn-outline-info me-1" onclick="confirmarRetorno(${r.id})" title="Confirmar retorno">
        <i class="bi bi-arrow-return-left"></i>
    </button>`
            : '';

        return `
            <tr>
                <td>${formatarDataRegistro(r)}</td>
                <td>${getNomeAluno(r.aluno_id)}</td>
                <td>${getTurmaAluno(r.aluno_id)}</td>
                <td>${badgeTipo}</td>
                <td>${r.aula}ª aula</td>
                <td>${descricaoRetorno(r)}</td>
                <td>${r.motivo}</td>
                <td class="text-center">${documento}</td>
                <td>${r.observacoes || '-'}</td>
                <td>
    ${perfilUsuario === 'admin' || perfilUsuario === 'ppdt' || perfilUsuario === 'biblioteca' ? `
    ${botaoConfirmarRetorno}
    <button class="btn btn-sm btn-outline-success me-1" onclick="imprimirAutorizacao(${r.id})" title="Imprimir autorização">
        <i class="bi bi-printer"></i>
    </button>
    <button class="btn btn-sm btn-outline-secondary me-1" onclick="abrirAnexos('registro', ${r.id}, 'Anexos do registro')" title="Anexos">
        <i class="bi bi-paperclip"></i>
    </button>
    <button class="btn btn-sm btn-outline-primary me-1" onclick="abrirEdicaoRegistro(${r.id})">
        <i class="bi bi-pencil"></i>
    </button>
    <button class="btn btn-sm btn-outline-danger" onclick="excluirRegistro(${r.id})">
        <i class="bi bi-trash"></i>
    </button>` : ''}
</td>
            </tr>
        `;
    }).join('');

    atualizarInfoPaginacaoRegistros(lista.length, totalPaginas);
}

function atualizarInfoPaginacaoRegistros(total, totalPaginas) {
    const porPagina = parseInt(document.getElementById('itensPorPagina')?.value || '25');
    const inicio = total === 0 ? 0 : (paginaAtualRegistros - 1) * porPagina + 1;
    const fim = Math.min(total, paginaAtualRegistros * porPagina);
    document.getElementById('infoPaginacaoRegistros').textContent = `${inicio}-${fim} de ${total} registros encontrados`;
    document.getElementById('paginaAtualRegistros').textContent = `${paginaAtualRegistros}/${totalPaginas}`;
}

function mudarPaginaRegistros(direcao) {
    const porPagina = parseInt(document.getElementById('itensPorPagina')?.value || '25');
    const totalPaginas = Math.max(1, Math.ceil(registrosFiltrados.length / porPagina));
    paginaAtualRegistros = Math.min(Math.max(1, paginaAtualRegistros + direcao), totalPaginas);
    renderizarRegistros(registrosFiltrados);
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

function selecionarAluno(id, nome) {
    document.getElementById('aluno_id').value = id;
    document.getElementById('buscaAluno').value = nome;
    document.getElementById('sugestoesAluno').innerHTML = '';
}

function valorInteiroOuNulo(id) {
    const valor = document.getElementById(id)?.value;
    return valor ? parseInt(valor) : null;
}

async function salvarRegistro() {
    const aluno_id = document.getElementById('aluno_id').value;
    if (!aluno_id) { alert('Selecione um aluno!'); return; }
    const tipoRegistro = document.getElementById('tipo').value;
    const tipoSaidaValor = ehSaidaAntecipada(tipoRegistro)
        ? document.getElementById('tipoSaida').value
        : null;
    const aulaRetornoSelecionada = valorInteiroOuNulo('aulaRetornoPrevista');
    const ehTemporaria = ehSaidaAntecipada(tipoRegistro) && (tipoSaidaValor === 'temporaria' || aulaRetornoSelecionada);
    const tipoSaidaFinal = ehSaidaAntecipada(tipoRegistro) ? (ehTemporaria ? 'temporaria' : 'definitiva') : null;
    const aulaRetornoPrevista = ehTemporaria ? aulaRetornoSelecionada : null;

    if (tipoSaidaFinal === 'temporaria' && !aulaRetornoPrevista) {
        alert('Informe a aula prevista de retorno.');
        return;
    }

    const dados = {
        aluno_id: parseInt(aluno_id),
        data: document.getElementById('data').value,
        tipo: tipoRegistro,
        aula: parseInt(document.getElementById('aula').value),
        aula_retorno_prevista: aulaRetornoPrevista,
        aula_retorno_real: null,
        tipo_saida: tipoSaidaFinal,
        status_retorno: null,
        motivo: document.getElementById('motivo').value,
        tem_documento: document.getElementById('tem_documento').checked,
        observacoes: document.getElementById('observacoes').value
    };

    const res = await fetch('/api/registros/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(dados)
    });

    if (res.ok) {
        const registroCriado = await res.json();
        const arquivo = document.getElementById('arquivoRegistro').files[0];
        if (arquivo) {
            try {
                await enviarAnexoPara('registro', registroCriado.id, arquivo);
            } catch (erro) {
                alert(`Registro salvo, mas o anexo falhou: ${erro.message}`);
            }
        }
        bootstrap.Modal.getInstance(document.getElementById('modalRegistro')).hide();
        document.getElementById('buscaAluno').value = '';
        document.getElementById('aluno_id').value = '';
        document.getElementById('motivo').value = '';
        document.getElementById('observacoes').value = '';
        document.getElementById('tem_documento').checked = false;
        document.getElementById('arquivoRegistro').value = '';
        document.getElementById('tipoSaida').value = 'definitiva';
        document.getElementById('aulaRetornoPrevista').value = '';
        atualizarCamposSaida();
        carregarDados();
    } else {
        alert('Erro ao salvar registro. Verifique os campos!');
    }
}

function abrirEdicaoRegistro(id) {
    const r = registros.find(r => r.id === id);
    if (!r) return;

    registroEditandoId = id;
    document.getElementById('editTipo').value = r.tipo;
    document.getElementById('editAula').value = r.aula;
    document.getElementById('editTipoSaida').value = r.tipo_saida || 'definitiva';
    document.getElementById('editAulaRetornoPrevista').value = r.aula_retorno_prevista || '';
    document.getElementById('editStatusRetorno').value = r.status_retorno || 'Pendente';
    document.getElementById('editMotivo').value = r.motivo;
    document.getElementById('editObservacoes').value = r.observacoes || '';
    document.getElementById('editTemDocumento').checked = r.tem_documento;
    atualizarCamposSaida('edit');

    new bootstrap.Modal(document.getElementById('modalEdicaoRegistro')).show();
}

async function salvarEdicaoRegistro() {
    const tipoRegistro = document.getElementById('editTipo').value;
    const tipoSaidaValor = ehSaidaAntecipada(tipoRegistro)
        ? document.getElementById('editTipoSaida').value
        : null;
    const aulaRetornoSelecionada = valorInteiroOuNulo('editAulaRetornoPrevista');
    const ehTemporaria = ehSaidaAntecipada(tipoRegistro) && (tipoSaidaValor === 'temporaria' || aulaRetornoSelecionada);
    const tipoSaidaFinal = ehSaidaAntecipada(tipoRegistro) ? (ehTemporaria ? 'temporaria' : 'definitiva') : null;
    const aulaRetornoPrevista = ehTemporaria ? aulaRetornoSelecionada : null;

    if (tipoSaidaFinal === 'temporaria' && !aulaRetornoPrevista) {
        alert('Informe a aula prevista de retorno.');
        return;
    }

    const registroAtual = registros.find(r => r.id === registroEditandoId);
    const dados = {
        tipo: tipoRegistro,
        aula: parseInt(document.getElementById('editAula').value),
        aula_retorno_prevista: aulaRetornoPrevista,
        aula_retorno_real: tipoSaidaFinal === 'temporaria' ? (registroAtual?.aula_retorno_real || null) : null,
        tipo_saida: tipoSaidaFinal,
        status_retorno: tipoSaidaFinal === 'temporaria' ? (document.getElementById('editStatusRetorno')?.value || 'Pendente') : null,
        motivo: document.getElementById('editMotivo').value,
        tem_documento: document.getElementById('editTemDocumento').checked,
        observacoes: document.getElementById('editObservacoes').value
    };

    const res = await fetch(`/api/registros/${registroEditandoId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(dados)
    });

    if (res.ok) {
        bootstrap.Modal.getInstance(document.getElementById('modalEdicaoRegistro')).hide();
        registroEditandoId = null;
        carregarDados();
    } else {
        alert('Erro ao editar registro!');
    }
}

async function excluirRegistro(id) {
    if (!confirm('Deseja excluir este registro?')) return;
    const res = await fetch(`/api/registros/${id}`, { method: 'DELETE' });
    if (res.ok) { carregarDados(); }
    else { alert('Erro ao excluir registro!'); }
}

async function confirmarRetorno(id) {
    const registro = registros.find(r => r.id === id);
    const sugestao = registro?.aula_retorno_prevista || '';
    const aula = prompt('Informe a aula em que o aluno retornou:', sugestao);
    if (!aula) return;
    const aulaNumero = parseInt(aula);
    if (!aulaNumero || aulaNumero < 1 || aulaNumero > 9) {
        alert('Informe uma aula entre 1 e 9.');
        return;
    }

    const res = await fetch(`/api/registros/${id}/confirmar-retorno?aula_retorno_real=${aulaNumero}`, {
        method: 'PUT'
    });
    if (res.ok) {
        carregarDados();
    } else {
        alert('Erro ao confirmar retorno.');
    }
}

function imprimirAutorizacao(id) {
    const registro = registros.find(r => r.id === id);
    if (!registro) return;

    const aluno = alunos.find(a => a.id === registro.aluno_id);
    const nomeAluno = aluno ? aluno.nome : '-';
    const matricula = aluno ? aluno.matricula : '-';
    const turma = getTurmaAluno(registro.aluno_id);
    const data = new Date(`${registro.data}T00:00:00`).toLocaleDateString('pt-BR');
    const hora = new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
    const tipoSaida = registro.tipo !== 'Atraso';
    const titulo = tipoSaida ? 'AUTORIZAÇÃO DE SAIDA' : 'AUTORIZAÇÃO DE ENTRADA';
    const textoPrincipal = tipoSaida
        ? 'Aluno autorizado a sair antecipadamente da escola.'
        : 'Aluno autorizado a entrar em sala após passar pela secretaria.';
    const destinatario = tipoSaida ? 'Entregar ao vigilante/Porteiro' : 'Entregar ao professor';
    const retornoTexto = ehSaidaAntecipada(registro.tipo)
        ? (registro.tipo_saida === 'temporaria'
            ? `Retorna ainda hoje - previsto para ${registro.aula_retorno_prevista || '-'}ª aula`
            : 'Não retorna hoje')
        : '';
    const logoUrl = `${window.location.origin}/static/img/logo-escola.png`;

    const janela = window.open('', '_blank', 'width=420,height=640');
    janela.document.write(`
        <html>
        <head>
            <meta charset="UTF-8">
            <title>${titulo}</title>
            <style>
                @page { size: 80mm auto; margin: 4mm; }
                body {
                    width: 72mm;
                    margin: 0 auto;
                    font-family: Arial, sans-serif;
                    color: #111;
                    font-size: 12px;
                }
                .ticket { padding: 6px 0; }
                .center { text-align: center; }
                .logo { width: 18mm; height: 18mm; object-fit: contain; margin-bottom: 2px; }
                .titulo { font-size: 15px; font-weight: 700; margin: 6px 0 2px; }
                .subtitulo { font-size: 11px; margin-bottom: 8px; }
                .linha { border-top: 1px dashed #333; margin: 8px 0; }
                .campo { margin: 5px 0; }
                .campo strong { display: inline-block; min-width: 23mm; }
                .texto { margin: 8px 0; line-height: 1.35; }
                .assinatura { margin-top: 22px; text-align: center; }
                .assinatura .risco { border-top: 1px solid #111; margin: 0 8mm 4px; }
                .rodape { font-size: 10px; margin-top: 10px; }
                @media print {
                    body { width: 72mm; }
                }
            </style>
        </head>
        <body>
            <div class="ticket">
                <div class="center">
                    <img class="logo" src="${logoUrl}" onerror="this.style.display='none'">
                    <div><strong>EEEP GOVERNADOR VIRGÍLIO TÁVORA</strong></div>
                    <div class="titulo">${titulo}</div>
                    <div class="subtitulo">${destinatario}</div>
                </div>
                <div class="linha"></div>
                <div class="campo"><strong>Data:</strong> ${data}</div>
                <div class="campo"><strong>Hora:</strong> ${hora}</div>
                <div class="campo"><strong>Aluno:</strong> ${nomeAluno}</div>
                <div class="campo"><strong>Matricula:</strong> ${matricula}</div>
                <div class="campo"><strong>Turma:</strong> ${turma}</div>
                <div class="campo"><strong>Tipo:</strong> ${registro.tipo}</div>
                <div class="campo"><strong>Aula:</strong> ${registro.aula}ª aula</div>
                ${retornoTexto ? `<div class="campo"><strong>Retorno:</strong> ${retornoTexto}</div>` : ''}
                <div class="campo"><strong>Motivo:</strong> ${registro.motivo}</div>
                <div class="campo"><strong>Documento:</strong> ${registro.tem_documento ? 'Sim' : 'Não'}</div>
                ${registro.observacoes ? `<div class="campo"><strong>Obs.:</strong> ${registro.observacoes}</div>` : ''}
                <div class="linha"></div>
                <div class="texto">${textoPrincipal}</div>
                <div class="assinatura">
                    <div class="risco"></div>
                    Secretaria / Coordenação
                </div>
                <div class="center rodape">Impresso em ${new Date().toLocaleString('pt-BR')}</div>
            </div>
            <script>
                window.onload = () => {
                    window.print();
                };
            </script>
        </body>
        </html>
    `);
    janela.document.close();
}

document.getElementById('filtroNome').addEventListener('input', filtrar);
document.getElementById('filtroTurma').addEventListener('change', filtrar);
document.getElementById('filtroTipo').addEventListener('change', filtrar);
document.getElementById('filtroData').addEventListener('change', filtrar);
document.getElementById('filtroMes').addEventListener('change', filtrar);
document.getElementById('itensPorPagina').addEventListener('change', () => {
    paginaAtualRegistros = 1;
    renderizarRegistros(registrosFiltrados);
});
document.getElementById('tipo').addEventListener('change', () => {
    atualizarListaMotivos();
    atualizarCamposSaida();
});
document.getElementById('tipoSaida')?.addEventListener('change', () => atualizarCamposSaida());
document.getElementById('editTipo')?.addEventListener('change', () => atualizarCamposSaida('edit'));
document.getElementById('editTipoSaida')?.addEventListener('change', () => atualizarCamposSaida('edit'));

function filtrar() {
    const nome = document.getElementById('filtroNome').value.toLowerCase();
    const turmaId = document.getElementById('filtroTurma').value;
    const tipo = document.getElementById('filtroTipo').value;
    const data = document.getElementById('filtroData').value;
    const mes = document.getElementById('filtroMes').value;

    registrosFiltrados = registros.filter(r => {
        const nomeAluno = getNomeAluno(r.aluno_id).toLowerCase();
        const aluno = alunos.find(a => a.id === r.aluno_id);
        const mesDado = r.data.substring(5, 7);
        return (
            (!nome || nomeAluno.includes(nome)) &&
            (!turmaId || (aluno && aluno.turma_id === parseInt(turmaId))) &&
            (!tipo || r.tipo === tipo) &&
            (!data || r.data === data) &&
            (!mes || mesDado === mes)
        );
    });

    paginaAtualRegistros = 1;
    renderizarRegistros(registrosFiltrados);
}

carregarDados();
