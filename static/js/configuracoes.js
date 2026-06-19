let cursos = [];
let turmas = [];
let permissoes = {};
let listasOperacionais = {};
const perfilAtual = window.perfilAtual || '';
const modulos = ['alunos', 'registros', 'ocorrencias', 'dashboard', 'relatorios', 'usuarios', 'configuracoes', 'anexos'];

async function carregarTudo() {
    const [cfg, anos, perms, listas, auditoria, backups, anexos, resCursos, resTurmas] = await Promise.all([
        fetch('/api/sistema/configuracoes').then(r => r.json()),
        fetch('/api/sistema/anos-letivos').then(r => r.json()),
        fetch('/api/sistema/permissoes').then(r => r.json()),
        fetch('/api/sistema/listas-operacionais').then(r => r.json()),
        fetch('/api/sistema/auditoria').then(r => r.json()),
        perfilAtual === 'admin' ? fetch('/api/sistema/backups').then(r => r.json()) : Promise.resolve([]),
        fetch('/api/sistema/anexos').then(r => r.json()),
        fetch('/api/cursos/').then(r => r.json()),
        fetch('/api/turmas/').then(r => r.json())
    ]);
    cursos = resCursos;
    turmas = resTurmas;
    permissoes = perms;
    listasOperacionais = listas;
    renderConfig(cfg);
    renderListasOperacionais();
    renderAnos(anos);
    renderPermissoes();
    renderAuditoria(auditoria);
    renderBackups(backups);
    renderAnexos(anexos);
    renderTurmasRelatorio();
    renderCursosTurmas();
}

function textoSeguro(valor) {
    return String(valor ?? '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#039;');
}

function renderConfig(cfg) {
    document.getElementById('config_escola_nome').value = cfg.escola_nome || '';
    document.getElementById('config_escola_endereco').value = cfg.escola_endereco || '';
    document.getElementById('config_escola_telefone').value = cfg.escola_telefone || '';
    document.getElementById('config_responsavel_sistema').value = cfg.responsavel_sistema || '';
}

async function salvarConfiguracoes() {
    const configuracoes = {
        escola_nome: document.getElementById('config_escola_nome').value,
        escola_endereco: document.getElementById('config_escola_endereco').value,
        escola_telefone: document.getElementById('config_escola_telefone').value,
        responsavel_sistema: document.getElementById('config_responsavel_sistema').value
    };
    const res = await fetch('/api/sistema/configuracoes', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ configuracoes })
    });
    alert(res.ok ? 'Configuracoes salvas.' : 'Erro ao salvar configuracoes.');
}

function linhasTextarea(id) {
    return document.getElementById(id).value
        .split('\n')
        .map(linha => linha.trim())
        .filter(Boolean);
}

function renderListasOperacionais() {
    const campos = {
        listaMotivosAtraso: listasOperacionais.motivos_atraso || [],
        listaMotivosSaida: listasOperacionais.motivos_saida || [],
        listaTiposOcorrencia: listasOperacionais.tipos_ocorrencia || [],
        listaMedidasOcorrencia: listasOperacionais.medidas_ocorrencia || []
    };
    Object.entries(campos).forEach(([id, lista]) => {
        const campo = document.getElementById(id);
        if (campo) campo.value = lista.join('\n');
    });
}

async function salvarListasOperacionais() {
    const dados = {
        motivos_atraso: linhasTextarea('listaMotivosAtraso'),
        motivos_saida: linhasTextarea('listaMotivosSaida'),
        tipos_ocorrencia: linhasTextarea('listaTiposOcorrencia'),
        medidas_ocorrencia: linhasTextarea('listaMedidasOcorrencia')
    };
    const res = await fetch('/api/sistema/listas-operacionais', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(dados)
    });
    if (res.ok) {
        listasOperacionais = dados;
        alert('Listas salvas.');
    } else {
        const erro = await res.json().catch(() => ({}));
        alert(erro.detail || 'Erro ao salvar listas.');
    }
}

function renderAnos(anos) {
    const tbody = document.getElementById('listaAnos');
    if (!anos.length) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">Nenhum ano letivo cadastrado.</td></tr>';
        return;
    }
    tbody.innerHTML = anos.map(a => {
        const status = a.encerrado
            ? '<span class="badge bg-dark">Encerrado</span>'
            : (a.ativo ? '<span class="badge bg-success">Ativo</span>' : '<span class="badge bg-secondary">Inativo</span>');
        const botaoAtivar = `<button class="btn btn-sm btn-outline-primary me-1" onclick="ativarAno(${a.id})" ${a.ativo || a.encerrado ? 'disabled' : ''}>Ativar</button>`;
        const botaoEncerrar = `<button class="btn btn-sm btn-outline-danger" onclick="encerrarAno(${a.id})" ${a.encerrado ? 'disabled' : ''}>Encerrar</button>`;
        return `
        <tr>
            <td>${a.nome}</td>
            <td>${a.data_inicio} ate ${a.data_fim}</td>
            <td>${status}</td>
            <td>${botaoAtivar}${botaoEncerrar}</td>
        </tr>
    `;
    }).join('');
}

function classeStatusVirada(status) {
    if (status === 'erro') return 'bg-danger';
    if (status === 'concluir') return 'bg-secondary';
    return 'bg-success';
}

async function abrirViradaAnoLetivo() {
    const modalEl = document.getElementById('modalViradaAno');
    if (!modalEl) return;

    document.getElementById('viradaAnoAtivo').textContent = 'Carregando...';
    document.getElementById('viradaProximoAno').textContent = '-';
    document.getElementById('viradaProximoStatus').textContent = '-';
    document.getElementById('viradaProximoInicio').value = '';
    document.getElementById('viradaProximoFim').value = '';
    document.getElementById('viradaPrimeiro').textContent = '0';
    document.getElementById('viradaSegundo').textContent = '0';
    document.getElementById('viradaTerceiro').textContent = '0';
    document.getElementById('viradaConfirmacao').value = '';
    document.getElementById('btnExecutarVirada').disabled = true;
    document.getElementById('viradaAvisoDestino').classList.add('d-none');
    document.getElementById('viradaTabelaMovimentos').innerHTML = '<tr><td colspan="4" class="text-center text-muted">Carregando previa...</td></tr>';

    new bootstrap.Modal(modalEl).show();

    try {
        const resposta = await fetch('/api/alunos/virada-ano/previa');
        const previa = await resposta.json();
        if (!resposta.ok) {
            alert(previa.detail || 'Erro ao carregar previa da virada.');
            return;
        }
        renderViradaAnoLetivo(previa);
    } catch (error) {
        console.error('Erro ao carregar previa da virada:', error);
        alert('Erro ao carregar previa da virada.');
    }
}

function renderViradaAnoLetivo(previa) {
    window.previaViradaAno = previa;
    document.getElementById('viradaAnoAtivo').textContent = previa.ano_letivo?.nome || '-';
    document.getElementById('viradaProximoAno').textContent = previa.proximo_ano_letivo?.nome || '-';
    document.getElementById('viradaProximoStatus').textContent = previa.proximo_ano_letivo?.sera_criado
        ? 'Será criado automaticamente'
        : 'Já cadastrado no sistema';
    document.getElementById('viradaPrimeiro').textContent = previa.primeiro_para_segundo || 0;
    document.getElementById('viradaSegundo').textContent = previa.segundo_para_terceiro || 0;
    document.getElementById('viradaTerceiro').textContent = previa.terceiro_concluido || 0;

    const proximoAno = previa.proximo_ano_letivo?.ano || new Date().getFullYear() + 1;
    document.getElementById('viradaProximoInicio').value = `${proximoAno}-02-01`;
    document.getElementById('viradaProximoFim').value = `${proximoAno}-12-31`;

    const movimentos = previa.movimentos || [];
    document.getElementById('viradaTabelaMovimentos').innerHTML = movimentos.map(item => `
        <tr>
            <td>${textoSeguro(item.origem)}</td>
            <td>${textoSeguro(item.destino)}</td>
            <td>${item.total}</td>
            <td><span class="badge ${classeStatusVirada(item.status)}">${textoSeguro(item.resultado)}</span></td>
        </tr>
    `).join('') || '<tr><td colspan="4" class="text-center text-muted">Nenhum aluno ativo para movimentar.</td></tr>';

    const proximoEncerrado = Boolean(previa.proximo_ano_letivo?.encerrado);
    const temErro = movimentos.some(item => item.status === 'erro') || (previa.sem_destino || 0) > 0 || proximoEncerrado;
    if (proximoEncerrado) {
        document.getElementById('viradaAvisoDestino').textContent = 'O próximo ano letivo existe, mas está encerrado. Reabra ou crie outro ano antes da virada.';
    } else {
        document.getElementById('viradaAvisoDestino').textContent = 'Existem alunos sem turma de destino. Crie as turmas faltantes antes de executar a virada.';
    }
    document.getElementById('viradaAvisoDestino').classList.toggle('d-none', !temErro);
    validarConfirmacaoVirada();
}

function validarConfirmacaoVirada() {
    const campo = document.getElementById('viradaConfirmacao');
    const botao = document.getElementById('btnExecutarVirada');
    const previa = window.previaViradaAno || {};
    const movimentos = previa.movimentos || [];
    const inicio = document.getElementById('viradaProximoInicio').value;
    const fim = document.getElementById('viradaProximoFim').value;
    const temErro = movimentos.some(item => item.status === 'erro') || (previa.sem_destino || 0) > 0 || Boolean(previa.proximo_ano_letivo?.encerrado);
    botao.disabled = campo.value.trim().toUpperCase() !== 'VIRADA' || temErro || !inicio || !fim || inicio > fim;
}

async function executarViradaAnoLetivo() {
    if (document.getElementById('btnExecutarVirada').disabled) return;

    try {
        const formData = new FormData();
        formData.append('proximo_inicio', document.getElementById('viradaProximoInicio').value);
        formData.append('proximo_fim', document.getElementById('viradaProximoFim').value);

        const resposta = await fetch('/api/alunos/virada-ano', {
            method: 'POST',
            body: formData
        });
        const resultado = await resposta.json();

        if (!resposta.ok) {
            alert(resultado.detail || 'Erro ao realizar virada de ano.');
            return;
        }

        alert(`${resultado.mensagem}\nAno origem: ${resultado.ano_origem}\nAno destino: ${resultado.ano_destino}\nPromovidos: ${resultado.promovidos}\nConcluidos: ${resultado.concluidos}`);
        bootstrap.Modal.getInstance(document.getElementById('modalViradaAno'))?.hide();
        carregarTudo();
    } catch (error) {
        console.error('Erro na virada de ano:', error);
        alert('Erro ao realizar virada de ano.');
    }
}

async function criarAnoLetivo() {
    const dados = {
        nome: document.getElementById('anoNome').value,
        ano: parseInt(document.getElementById('anoNumero').value),
        data_inicio: document.getElementById('anoInicio').value,
        data_fim: document.getElementById('anoFim').value,
        ativo: document.getElementById('anoAtivo').checked
    };
    const res = await fetch('/api/sistema/anos-letivos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(dados)
    });
    if (res.ok) carregarTudo();
    else alert('Erro ao criar ano letivo.');
}

async function ativarAno(id) {
    await fetch(`/api/sistema/anos-letivos/${id}/ativar`, { method: 'PUT' });
    carregarTudo();
}

async function encerrarAno(id) {
    if (!confirm('Encerrar este ano letivo? Ele deixara de ser o ano ativo.')) return;
    const res = await fetch(`/api/sistema/anos-letivos/${id}/encerrar`, { method: 'PUT' });
    if (res.ok) carregarTudo();
    else {
        const erro = await res.json().catch(() => ({}));
        alert(erro.detail || 'Erro ao encerrar ano letivo.');
    }
}

function renderPermissoes() {
    const select = document.getElementById('permissaoPerfil');
    select.innerHTML = Object.keys(permissoes).map(p => `<option value="${p}">${p}</option>`).join('');
    renderPermissoesPerfil();
}

function renderPermissoesPerfil() {
    const perfil = document.getElementById('permissaoPerfil').value;
    const marcadas = new Set(permissoes[perfil] || []);
    document.getElementById('permissoesChecks').innerHTML = modulos.map(m => `
        <div class="form-check form-check-inline">
            <input class="form-check-input" type="checkbox" value="${m}" id="perm_${m}" ${marcadas.has('*') || marcadas.has(m) ? 'checked' : ''}>
            <label class="form-check-label" for="perm_${m}">${m}</label>
        </div>
    `).join('');
}

async function salvarPermissoes() {
    const perfil = document.getElementById('permissaoPerfil').value;
    const selecionadas = Array.from(document.querySelectorAll('#permissoesChecks input:checked')).map(i => i.value);
    const res = await fetch('/api/sistema/permissoes', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ perfil, permissoes: selecionadas })
    });
    if (res.ok) {
        permissoes[perfil] = selecionadas;
        alert('Permissoes salvas.');
    } else {
        alert('Erro ao salvar permissoes.');
    }
}

function renderAuditoria(lista) {
    const tbody = document.getElementById('listaAuditoria');
    if (!lista.length) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">Nenhum log encontrado.</td></tr>';
        return;
    }
    tbody.innerHTML = lista.map(l => `
        <tr>
            <td>${new Date(l.criado_em).toLocaleString('pt-BR')}</td>
            <td>${l.usuario_nome || '-'}</td>
            <td>${l.acao}</td>
            <td>${l.entidade}${l.entidade_id ? ` #${l.entidade_id}` : ''}</td>
            <td>${l.detalhes || '-'}</td>
        </tr>
    `).join('');
}

async function carregarAuditoria() {
    const params = new URLSearchParams();
    const campos = {
        usuario_nome: 'auditoriaUsuario',
        acao: 'auditoriaAcao',
        entidade: 'auditoriaEntidade',
        data_inicio: 'auditoriaInicio',
        data_fim: 'auditoriaFim'
    };
    Object.entries(campos).forEach(([chave, id]) => {
        const valor = document.getElementById(id)?.value;
        if (valor) params.set(chave, valor);
    });
    const res = await fetch(`/api/sistema/auditoria?${params.toString()}`);
    renderAuditoria(await res.json());
}

function renderTurmasRelatorio() {
    const select = document.getElementById('relatorioTurma');
    select.innerHTML = '<option value="">Todas</option>' + turmas.map(t => {
        const curso = cursos.find(c => c.id === t.curso_id);
        return `<option value="${t.id}">${t.ano}º ${t.letra} - ${curso ? curso.nome : ''}</option>`;
    }).join('');
}

function abrirRelatorio() {
    const tipo = document.getElementById('relatorioTipo').value;
    const turmaId = document.getElementById('relatorioTurma').value;
    const params = new URLSearchParams({ tipo });
    if (turmaId) params.set('turma_id', turmaId);
    window.open(`/api/sistema/relatorios/oficial?${params.toString()}`, '_blank');
}

function renderCursosTurmas() {
    const listaCursos = document.getElementById('listaCursosConfig');
    const listaTurmas = document.getElementById('listaTurmasConfig');
    const selectCurso = document.getElementById('turmaCurso');

    if (!listaCursos || !listaTurmas || !selectCurso) return;

    if (!cursos.length) {
        listaCursos.innerHTML = '<tr><td colspan="3" class="text-center text-muted">Nenhum curso cadastrado.</td></tr>';
        selectCurso.innerHTML = '<option value="">Cadastre um curso primeiro</option>';
    } else {
        listaCursos.innerHTML = cursos.map(c => `
            <tr>
                <td>${textoSeguro(c.nome)}</td>
                <td>${textoSeguro(c.sigla || '-')}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick="editarCurso(${c.id})" title="Editar curso">
                        <i class="bi bi-pencil"></i>
                    </button>
                </td>
            </tr>
        `).join('');
        selectCurso.innerHTML = '<option value="">Selecione o curso</option>' + cursos.map(c => (
            `<option value="${c.id}">${textoSeguro(c.nome)}</option>`
        )).join('');
    }

    if (!turmas.length) {
        listaTurmas.innerHTML = '<tr><td colspan="3" class="text-center text-muted">Nenhuma turma cadastrada.</td></tr>';
        return;
    }

    listaTurmas.innerHTML = turmas.map(t => {
        const curso = cursos.find(c => c.id === t.curso_id);
        return `
            <tr>
                <td>${t.ano}º ${textoSeguro(t.letra)}</td>
                <td>${textoSeguro(curso ? curso.nome : '-')}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick="editarTurma(${t.id})" title="Editar turma">
                        <i class="bi bi-pencil"></i>
                    </button>
                </td>
            </tr>
        `;
    }).join('');
}

async function criarCurso() {
    const nome = document.getElementById('cursoNome').value.trim();
    const sigla = document.getElementById('cursoSigla').value.trim().toUpperCase();

    if (!nome || !sigla) {
        alert('Informe o nome e a sigla do curso.');
        return;
    }

    const res = await fetch('/api/cursos/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nome, sigla })
    });

    if (res.ok) {
        document.getElementById('cursoNome').value = '';
        document.getElementById('cursoSigla').value = '';
        await carregarTudo();
        alert('Curso criado com sucesso.');
        return;
    }

    const erro = await res.json().catch(() => ({}));
    alert(erro.detail || 'Erro ao criar curso.');
}

async function criarTurma() {
    const cursoId = parseInt(document.getElementById('turmaCurso').value);
    const ano = parseInt(document.getElementById('turmaAno').value);
    const letra = document.getElementById('turmaLetra').value.trim().toUpperCase();

    if (!cursoId || !ano || !letra) {
        alert('Informe curso, ano e letra da turma.');
        return;
    }

    const res = await fetch('/api/turmas/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ curso_id: cursoId, ano, letra })
    });

    if (res.ok) {
        document.getElementById('turmaLetra').value = '';
        await carregarTudo();
        alert('Turma criada com sucesso.');
        return;
    }

    const erro = await res.json().catch(() => ({}));
    alert(erro.detail || 'Erro ao criar turma.');
}

async function editarCurso(id) {
    const curso = cursos.find(c => c.id === id);
    if (!curso) return;

    const nome = prompt('Nome do curso:', curso.nome);
    if (nome === null) return;

    const sigla = prompt('Sigla do curso:', curso.sigla || '');
    if (sigla === null) return;

    const dados = {
        nome: nome.trim(),
        sigla: sigla.trim().toUpperCase()
    };

    if (!dados.nome || !dados.sigla) {
        alert('Informe o nome e a sigla do curso.');
        return;
    }

    const res = await fetch(`/api/cursos/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(dados)
    });

    if (res.ok) {
        await carregarTudo();
        alert('Curso atualizado com sucesso.');
        return;
    }

    const erro = await res.json().catch(() => ({}));
    alert(erro.detail || 'Erro ao atualizar curso.');
}

async function editarTurma(id) {
    const turma = turmas.find(t => t.id === id);
    if (!turma) return;

    const anoTexto = prompt('Ano da turma (1, 2 ou 3):', turma.ano);
    if (anoTexto === null) return;

    const letra = prompt('Letra da turma:', turma.letra || '');
    if (letra === null) return;

    const cursoAtual = cursos.find(c => c.id === turma.curso_id);
    const opcoes = cursos.map(c => `${c.id} - ${c.nome}`).join('\n');
    const cursoTexto = prompt(`ID do curso:\n${opcoes}`, cursoAtual ? cursoAtual.id : '');
    if (cursoTexto === null) return;

    const dados = {
        ano: parseInt(anoTexto),
        letra: letra.trim().toUpperCase(),
        curso_id: parseInt(cursoTexto)
    };

    if (![1, 2, 3].includes(dados.ano) || !dados.letra || !dados.curso_id) {
        alert('Informe ano, letra e curso validos.');
        return;
    }

    const res = await fetch(`/api/turmas/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(dados)
    });

    if (res.ok) {
        await carregarTudo();
        alert('Turma atualizada com sucesso.');
        return;
    }

    const erro = await res.json().catch(() => ({}));
    alert(erro.detail || 'Erro ao atualizar turma.');
}

function formatarTamanho(bytes) {
    if (!bytes) return '0 KB';
    if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function renderBackups(lista) {
    const tbody = document.getElementById('listaBackups');
    if (!lista.length) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">Nenhum backup gerado.</td></tr>';
        return;
    }
    tbody.innerHTML = lista.map(b => {
        const tipo = b.nome.startsWith('anexos_') ? 'Anexos' : (b.nome.endsWith('.sql') ? 'Banco SQL' : 'Banco JSON');
        const botaoRestaurar = b.nome.startsWith('anexos_')
            ? ''
            : `<button class="btn btn-sm btn-outline-danger" onclick="restaurarBackup('${textoSeguro(b.nome)}')">
                    <i class="bi bi-arrow-counterclockwise me-1"></i>Restaurar
                </button>`;
        return `
        <tr>
            <td>${b.nome}<div class="small text-muted">${tipo}</div></td>
            <td>${formatarTamanho(b.tamanho)}</td>
            <td>${new Date(b.criado_em).toLocaleString('pt-BR')}</td>
            <td>
                <a class="btn btn-sm btn-outline-success me-1" href="${b.url}"><i class="bi bi-download me-1"></i>Baixar</a>
                ${botaoRestaurar}
            </td>
        </tr>
    `;
    }).join('');
}

async function gerarBackupSelecionado() {
    const tipo = document.getElementById('backupTipo').value;
    if (tipo === 'anexos') {
        await gerarBackupAnexos();
        return;
    }
    await gerarBackup(tipo);
}

async function gerarBackup(tipo = 'auto') {
    const textoTipo = {
        auto: 'automatico recomendado',
        sql: 'Banco completo SQL',
        json: 'Dados do sistema JSON'
    }[tipo] || 'backup';
    if (!confirm(`Gerar backup ${textoTipo} agora?`)) return;

    const res = await fetch(`/api/sistema/backups?tipo=${encodeURIComponent(tipo)}`, { method: 'POST' });
    if (res.ok) {
        const backup = await res.json();
        alert(`Backup gerado: ${backup.nome}`);
        carregarTudo();
    } else {
        const erro = await res.json();
        alert(erro.detail || 'Erro ao gerar backup.');
    }
}

async function gerarBackupAnexos() {
    if (!confirm('Gerar um pacote .zip com todos os anexos enviados?')) return;
    const res = await fetch('/api/sistema/backups/anexos', { method: 'POST' });
    if (res.ok) {
        const backup = await res.json();
        alert(`Backup dos anexos gerado: ${backup.nome}\nArquivos incluidos: ${backup.total_arquivos}`);
        carregarTudo();
    } else {
        const erro = await res.json().catch(() => ({}));
        alert(erro.detail || 'Erro ao gerar backup dos anexos.');
    }
}

async function restaurarBackup(nome) {
    const ehSql = nome.toLowerCase().endsWith('.sql');
    const textoConfirmacao = ehSql ? 'RESTAURAR SQL' : 'RESTAURAR';
    const confirmacao = prompt(`Restaurar o backup ${nome}?\n\nDigite ${textoConfirmacao} para confirmar.`);
    if (confirmacao !== textoConfirmacao) return;
    const res = await fetch(`/api/sistema/backups/${encodeURIComponent(nome)}/restaurar`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ confirmacao })
    });
    if (res.ok) {
        alert('Backup restaurado com sucesso.');
        carregarTudo();
    } else {
        const erro = await res.json().catch(() => ({}));
        alert(erro.detail || 'Erro ao restaurar backup.');
    }
}

async function restaurarBackupUpload() {
    const arquivo = document.getElementById('arquivoRestauracao').files[0];
    if (!arquivo) {
        alert('Selecione um arquivo .json ou .sql para restaurar.');
        return;
    }

    const ehSql = arquivo.name.toLowerCase().endsWith('.sql');
    const ehJson = arquivo.name.toLowerCase().endsWith('.json');
    if (!ehSql && !ehJson) {
        alert('Envie apenas arquivo .json ou .sql.');
        return;
    }

    const textoConfirmacao = ehSql ? 'RESTAURAR SQL' : 'RESTAURAR';
    const confirmacao = prompt(`Restaurar o arquivo ${arquivo.name}?\n\nEssa acao pode substituir dados do sistema.\nDigite ${textoConfirmacao} para confirmar.`);
    if (confirmacao !== textoConfirmacao) return;

    const formData = new FormData();
    formData.append('arquivo', arquivo);
    formData.append('confirmacao', confirmacao);

    const res = await fetch('/api/sistema/backups/restaurar-upload', {
        method: 'POST',
        body: formData
    });

    if (res.ok) {
        const resultado = await res.json();
        alert(resultado.mensagem || 'Backup restaurado com sucesso.');
        document.getElementById('arquivoRestauracao').value = '';
        carregarTudo();
        return;
    }

    const erro = await res.json().catch(() => ({}));
    alert(erro.detail || 'Erro ao restaurar backup.');
}

function renderAnexos(lista) {
    const tbody = document.getElementById('listaAnexos');
    if (!lista.length) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">Nenhum anexo enviado.</td></tr>';
        return;
    }
    tbody.innerHTML = lista.map(a => `
        <tr>
            <td><a href="${a.url}" target="_blank">${a.nome_original}</a></td>
            <td>${a.entidade} #${a.entidade_id}</td>
            <td>${a.enviado_por_nome || '-'}</td>
            <td>${new Date(a.criado_em).toLocaleString('pt-BR')}</td>
            <td><button class="btn btn-sm btn-outline-danger" onclick="excluirAnexo(${a.id})"><i class="bi bi-trash"></i></button></td>
        </tr>
    `).join('');
}

async function enviarAnexo() {
    const arquivo = document.getElementById('anexoArquivo').files[0];
    const entidadeId = document.getElementById('anexoEntidadeId').value;
    if (!arquivo || !entidadeId) {
        alert('Informe o ID e selecione um arquivo.');
        return;
    }
    const form = new FormData();
    form.append('entidade', document.getElementById('anexoEntidade').value);
    form.append('entidade_id', entidadeId);
    form.append('arquivo', arquivo);
    const res = await fetch('/api/sistema/anexos', { method: 'POST', body: form });
    if (res.ok) {
        document.getElementById('anexoArquivo').value = '';
        carregarTudo();
    } else {
        const erro = await res.json();
        alert(erro.detail || 'Erro ao enviar anexo.');
    }
}

async function excluirAnexo(id) {
    if (!confirm('Excluir este anexo?')) return;
    await fetch(`/api/sistema/anexos/${id}`, { method: 'DELETE' });
    carregarTudo();
}

carregarTudo();
