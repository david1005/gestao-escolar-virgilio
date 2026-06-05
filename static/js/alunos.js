let turmas = [];
let cursos = [];
let alunosCarregados = [];
let alunosFiltrados = [];
let alunoEditandoId = null;
let paginaAtual = 1;

// Carrega turmas, cursos e alunos ao abrir a página
async function carregarDados() {
    try {
        const status = document.getElementById('filtroStatus')?.value || 'ativo';
        const [resTurmas, resCursos, resAlunos, resTodosAlunos] = await Promise.all([
            fetch('/api/turmas/'),
            fetch('/api/cursos/'),
            fetch(`/api/alunos/?status=${status}`),
            fetch('/api/alunos/?status=todos')
        ]);

        turmas = await resTurmas.json();
        cursos = await resCursos.json();
        alunosCarregados = await resAlunos.json();
        const todosAlunos = await resTodosAlunos.json();

        preencherSelectTurmas();
        preencherSelectCursos();
        renderizarResumoStatus(todosAlunos);
        aplicarFiltros();
    } catch (error) {
        console.error('Erro ao carregar dados:', error);
        alert('Erro ao carregar dados da página.');
    }
}

function renderizarResumoStatus(alunos) {
    const totais = alunos.reduce((acc, aluno) => {
        const status = aluno.status || 'ativo';
        acc[status] = (acc[status] || 0) + 1;
        return acc;
    }, {});

    document.getElementById('totalAtivos').textContent = totais.ativo || 0;
    document.getElementById('totalConcluidos').textContent = totais.concluido || 0;
    document.getElementById('totalTransferidos').textContent = totais.transferido || 0;
    document.getElementById('totalDesistentes').textContent = totais.desistente || 0;
}

function preencherSelectCursos() {
    const filtroCurso = document.getElementById('filtroCurso');
    const valorAtual = filtroCurso.value;
    const importCurso = document.getElementById('importCurso');
    const valorImportacao = importCurso.value;
    filtroCurso.innerHTML = '<option value="">Todos os cursos</option>';
    importCurso.innerHTML = '<option value="">Selecione o curso</option>';

    cursos.forEach(curso => {
        filtroCurso.innerHTML += `<option value="${curso.id}">${curso.nome}</option>`;
        importCurso.innerHTML += `<option value="${curso.id}">${curso.nome}</option>`;
    });

    filtroCurso.value = valorAtual;
    importCurso.value = valorImportacao;
}

// Preenche os selects de turma
function preencherSelectTurmas() {
    const select = document.getElementById('turma_id');
    const filtro = document.getElementById('filtroTurma');

    select.innerHTML = '<option value="">Selecione a turma</option>';
    filtro.innerHTML = '<option value="">Todas as turmas</option>';

    const turmasOrdenadas = [...turmas].sort((a, b) =>
        a.ano - b.ano || a.letra.localeCompare(b.letra)
    );

    turmasOrdenadas.forEach(t => {
        const curso = cursos.find(c => c.id === t.curso_id);
        const label = formatarTurma(t, curso);

        select.innerHTML += `<option value="${t.id}">${label}</option>`;
        filtro.innerHTML += `<option value="${t.id}">${label}</option>`;
    });
}

function formatarTurma(turma, curso) {
    return `${turma.ano}\u00ba ${turma.letra} - ${curso ? curso.nome : ''}`;
}

// Mostra os alunos na tabela
function renderizarAlunos(alunos) {
    const tbody = document.getElementById('tabelaAlunos');

    if (!alunos || alunos.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center text-muted">
                    Nenhum aluno cadastrado.
                </td>
            </tr>
        `;
        atualizarInfoPaginacao(0, 1);
        return;
    }

    const porPagina = parseInt(document.getElementById('itensPorPagina').value);
    const totalPaginas = Math.max(1, Math.ceil(alunos.length / porPagina));
    paginaAtual = Math.min(paginaAtual, totalPaginas);
    const inicio = (paginaAtual - 1) * porPagina;
    const alunosPagina = alunos.slice(inicio, inicio + porPagina);

    tbody.innerHTML = alunosPagina.map(a => {
        const turma = turmas.find(t => t.id === a.turma_id);
        const curso = turma ? cursos.find(c => c.id === turma.curso_id) : null;
        const turmaLabel = turma ? formatarTurma(turma, curso) : '-';

        return `
            <tr>
                <td>${a.nome}</td>
                <td>${a.matricula}</td>
                <td>${turmaLabel}</td>
                <td>${formatarStatus(a.status)}</td>
                <td>${a.responsavel}</td>
                <td>${a.contato_responsavel}</td>
            <td>
    <a href="/aluno/${a.id}" class="btn btn-sm btn-outline-primary me-1" title="Ver aluno">
        <i class="bi bi-person"></i>
    </a>
    ${perfilUsuario === 'admin' || perfilUsuario === 'ppdt' ? `
    <button class="btn btn-sm btn-outline-secondary me-1" onclick="abrirEdicaoAluno(${a.id})" title="Editar aluno">
        <i class="bi bi-pencil"></i>
    </button>
    <button class="btn btn-sm btn-outline-danger" onclick="excluirAluno(${a.id})" title="Excluir aluno">
        <i class="bi bi-trash"></i>
    </button>` : ''}
</td>
            </tr>
        `;
    }).join('');

    atualizarInfoPaginacao(alunos.length, totalPaginas);
}

function atualizarInfoPaginacao(total, totalPaginas) {
    const porPagina = parseInt(document.getElementById('itensPorPagina').value);
    const inicio = total === 0 ? 0 : (paginaAtual - 1) * porPagina + 1;
    const fim = Math.min(total, paginaAtual * porPagina);
    document.getElementById('infoPaginacao').textContent = `${inicio}-${fim} de ${total} alunos encontrados`;
    document.getElementById('paginaAtual').textContent = `${paginaAtual}/${totalPaginas}`;
}

function mudarPagina(direcao) {
    const porPagina = parseInt(document.getElementById('itensPorPagina').value);
    const totalPaginas = Math.max(1, Math.ceil(alunosFiltrados.length / porPagina));
    paginaAtual = Math.min(Math.max(1, paginaAtual + direcao), totalPaginas);
    renderizarAlunos(alunosFiltrados);
}

function abrirNovoAluno() {
    alunoEditandoId = null;
    limparFormulario();
    document.getElementById('modalAlunoTitulo').innerHTML = '<i class="bi bi-person-plus me-2"></i>Novo Aluno';

    const modal = new bootstrap.Modal(document.getElementById('modalAluno'));
    modal.show();
}

function formatarStatus(status) {
    const labels = {
        ativo: ['Ativo', 'bg-success'],
        concluido: ['Concluido', 'bg-secondary'],
        transferido: ['Transferido', 'bg-info text-dark'],
        desistente: ['Desistente', 'bg-danger']
    };
    const [texto, classe] = labels[status] || [status || 'Ativo', 'bg-success'];
    return `<span class="badge ${classe}">${texto}</span>`;
}

function abrirEdicaoAluno(id) {
    const aluno = alunosCarregados.find(a => a.id === id);
    if (!aluno) {
        alert('Aluno não encontrado para edição.');
        return;
    }

    alunoEditandoId = id;
    document.getElementById('modalAlunoTitulo').innerHTML = '<i class="bi bi-pencil-square me-2"></i>Editar Aluno';
    document.getElementById('nome').value = aluno.nome;
    document.getElementById('matricula').value = aluno.matricula;
    document.getElementById('data_nascimento').value = aluno.data_nascimento;
    document.getElementById('responsavel').value = aluno.responsavel;
    document.getElementById('contato_responsavel').value = aluno.contato_responsavel;
    document.getElementById('turma_id').value = aluno.turma_id;
    document.getElementById('status').value = aluno.status || 'ativo';

    const modal = new bootstrap.Modal(document.getElementById('modalAluno'));
    modal.show();
}

// Salva aluno novo ou editado
async function salvarAluno() {
    const dados = {
        nome: document.getElementById('nome').value.trim(),
        matricula: document.getElementById('matricula').value.trim(),
        data_nascimento: document.getElementById('data_nascimento').value,
        responsavel: document.getElementById('responsavel').value.trim(),
        contato_responsavel: document.getElementById('contato_responsavel').value.trim(),
        turma_id: parseInt(document.getElementById('turma_id').value),
        status: document.getElementById('status').value
    };

    if (
        !dados.nome ||
        !dados.matricula ||
        !dados.data_nascimento ||
        !dados.responsavel ||
        !dados.contato_responsavel ||
        !dados.turma_id
    ) {
        alert('Preencha todos os campos antes de salvar.');
        return;
    }

    try {
        const url = alunoEditandoId ? `/api/alunos/${alunoEditandoId}` : '/api/alunos/';
        const metodo = alunoEditandoId ? 'PUT' : 'POST';

        const resposta = await fetch(url, {
            method: metodo,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(dados)
        });

        if (!resposta.ok) {
            const erro = await resposta.json();
            console.error(erro);
            alert(erro.detail || 'Erro ao salvar aluno. Verifique os dados informados.');
            return;
        }

        alert(alunoEditandoId ? 'Aluno atualizado com sucesso!' : 'Aluno cadastrado com sucesso!');

        limparFormulario();

        const modalElemento = document.getElementById('modalAluno');
        const modal = bootstrap.Modal.getInstance(modalElemento);
        modal.hide();

        carregarDados();
    } catch (error) {
        console.error('Erro ao salvar aluno:', error);
        alert('Erro ao salvar aluno.');
    }
}

// Exclui aluno
async function excluirAluno(id) {
    const confirmar = confirm('Tem certeza que deseja excluir este aluno?');

    if (!confirmar) {
        return;
    }

    try {
        const resposta = await fetch(`/api/alunos/${id}`, {
            method: 'DELETE'
        });

        if (!resposta.ok) {
            alert('Erro ao excluir aluno.');
            return;
        }

        alert('Aluno excluído com sucesso!');
        carregarDados();
    } catch (error) {
        console.error('Erro ao excluir aluno:', error);
        alert('Erro ao excluir aluno.');
    }
}

// Limpa o formulário após salvar
function limparFormulario() {
    alunoEditandoId = null;
    document.getElementById('nome').value = '';
    document.getElementById('matricula').value = '';
    document.getElementById('data_nascimento').value = '';
    document.getElementById('responsavel').value = '';
    document.getElementById('contato_responsavel').value = '';
    document.getElementById('turma_id').value = '';
    document.getElementById('status').value = 'ativo';
}

// Filtra alunos por nome e turma
function aplicarFiltros() {
    const nome = document.getElementById('filtroNome').value.toLowerCase();
    const turmaId = document.getElementById('filtroTurma').value;
    const ano = document.getElementById('filtroAno').value;
    const cursoId = document.getElementById('filtroCurso').value;

    alunosFiltrados = alunosCarregados.filter(a => {
        const turma = turmas.find(t => t.id === a.turma_id);
        const combinaNome = a.nome.toLowerCase().includes(nome);
        const combinaTurma = turmaId === '' || a.turma_id === parseInt(turmaId);
        const combinaAno = ano === '' || (turma && turma.ano === parseInt(ano));
        const combinaCurso = cursoId === '' || (turma && turma.curso_id === parseInt(cursoId));

        return combinaNome && combinaTurma && combinaAno && combinaCurso;
    });

    paginaAtual = 1;
    renderizarAlunos(alunosFiltrados);
}

// Eventos dos filtros
document.getElementById('filtroNome').addEventListener('input', aplicarFiltros);
document.getElementById('filtroTurma').addEventListener('change', aplicarFiltros);
document.getElementById('filtroAno').addEventListener('change', aplicarFiltros);
document.getElementById('filtroCurso').addEventListener('change', aplicarFiltros);
document.getElementById('filtroStatus').addEventListener('change', carregarDados);
document.getElementById('itensPorPagina').addEventListener('change', () => {
    paginaAtual = 1;
    renderizarAlunos(alunosFiltrados);
});

function exportarAlunosCSV() {
    const cabecalho = ['nome', 'matricula', 'data_nascimento', 'turma', 'status', 'responsavel', 'contato_responsavel'];
    const linhas = alunosFiltrados.map(a => {
        const turma = turmas.find(t => t.id === a.turma_id);
        const curso = turma ? cursos.find(c => c.id === turma.curso_id) : null;
        const turmaLabel = turma ? formatarTurma(turma, curso) : '';
        return [
            a.nome,
            a.matricula,
            a.data_nascimento,
            turmaLabel,
            a.status || 'ativo',
            a.responsavel,
            a.contato_responsavel
        ].map(valor => `"${String(valor || '').replaceAll('"', '""')}"`).join(';');
    });

    const csv = ['sep=;', cabecalho.join(';'), ...linhas].join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'alunos_filtrados.csv';
    link.click();
    URL.revokeObjectURL(link.href);
}

function baixarModeloImportacao() {
    const linhas = [
        'sep=;',
        'nome;matricula;data_nascimento;responsavel;contato_responsavel;ano;letra;curso;status',
        'Maria Exemplo;20260001;2010-03-15;Ana Responsavel;(88) 99999-0000;1;A;Enfermagem;ativo',
        'Joao Exemplo;20260002;2010-07-22;Carlos Responsavel;(88) 98888-0000;1;B;Informática;ativo'
    ];
    const csv = linhas.join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'modelo_importacao_alunos.csv';
    link.click();
    URL.revokeObjectURL(link.href);
}

async function importarAlunosCSV(event) {
    const arquivo = event.target.files[0];
    event.target.value = '';
    if (!arquivo) {
        return;
    }

    const formData = new FormData();
    formData.append('arquivo', arquivo);

    try {
        const resposta = await fetch('/api/alunos/importar-csv', {
            method: 'POST',
            body: formData
        });
        const resultado = await resposta.json();

        if (!resposta.ok) {
            alert(resultado.detail || 'Erro ao importar alunos.');
            return;
        }

        const erros = resultado.erros && resultado.erros.length
            ? `\n\nPrimeiros erros:\n${resultado.erros.join('\n')}`
            : '';
        alert(`Importacao concluida.\nCriados: ${resultado.criados}\nIgnorados: ${resultado.ignorados}${erros}`);
        carregarDados();
    } catch (error) {
        console.error('Erro ao importar CSV:', error);
        alert('Erro ao importar CSV.');
    }
}

async function realizarViradaAno() {
    const primeiraConfirmacao = confirm(
        'A virada de ano vai concluir alunos do 3º ano e promover alunos do 1º e 2º ano. Deseja continuar?'
    );
    if (!primeiraConfirmacao) {
        return;
    }

    const texto = prompt('Digite VIRADA para confirmar a alteração das turmas.');
    if (texto !== 'VIRADA') {
        alert('Virada de ano cancelada.');
        return;
    }

    try {
        const resposta = await fetch('/api/alunos/virada-ano', { method: 'POST' });
        const resultado = await resposta.json();

        if (!resposta.ok) {
            alert(resultado.detail || 'Erro ao realizar virada de ano.');
            return;
        }

        alert(`${resultado.mensagem}\nPromovidos: ${resultado.promovidos}\nConcluidos: ${resultado.concluidos}`);
        document.getElementById('filtroStatus').value = 'ativo';
        carregarDados();
    } catch (error) {
        console.error('Erro na virada de ano:', error);
        alert('Erro ao realizar virada de ano.');
    }
}

// Inicia a página
baixarModeloImportacao = function () {
    const linhas = [
        'sep=;',
        'nome;matricula;data_nascimento;responsavel;contato_responsavel;status',
        'Maria Exemplo;20260001;2010-03-15;Ana Responsavel;(88) 99999-0000;ativo',
        'Joao Exemplo;20260002;2010-07-22;Carlos Responsavel;(88) 98888-0000;ativo'
    ];
    const csv = linhas.join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'modelo_importacao_alunos.csv';
    link.click();
    URL.revokeObjectURL(link.href);
};

abrirModalImportacao = function () {
    document.getElementById('importCurso').value = '';
    document.getElementById('importAno').value = '';
    document.getElementById('arquivoImportacao').value = '';
    new bootstrap.Modal(document.getElementById('modalImportacao')).show();
};

importarAlunosCSV = async function () {
    const arquivo = document.getElementById('arquivoImportacao').files[0];
    const cursoId = document.getElementById('importCurso').value;
    const ano = document.getElementById('importAno').value;

    if (!arquivo) {
        alert('Selecione um arquivo CSV.');
        return;
    }
    if (!cursoId || !ano) {
        alert('Selecione o curso e o ano da turma.');
        return;
    }

    const formData = new FormData();
    formData.append('arquivo', arquivo);
    formData.append('curso_id', cursoId);
    formData.append('ano', ano);

    try {
        const resposta = await fetch('/api/alunos/importar-csv', {
            method: 'POST',
            body: formData
        });
        const resultado = await resposta.json();

        if (!resposta.ok) {
            alert(resultado.detail || 'Erro ao importar alunos.');
            return;
        }

        const erros = resultado.erros && resultado.erros.length
            ? `\n\nPrimeiros erros:\n${resultado.erros.join('\n')}`
            : '';
        alert(`Importacao concluida.\nCriados: ${resultado.criados}\nIgnorados: ${resultado.ignorados}${erros}`);
        bootstrap.Modal.getInstance(document.getElementById('modalImportacao')).hide();
        carregarDados();
    } catch (error) {
        console.error('Erro ao importar CSV:', error);
        alert('Erro ao importar CSV.');
    }
};

realizarViradaAno = async function () {
    let previa;
    try {
        const respostaPrevia = await fetch('/api/alunos/virada-ano/previa');
        previa = await respostaPrevia.json();
    } catch (error) {
        console.error('Erro ao carregar previa:', error);
        alert('Erro ao carregar previa da virada.');
        return;
    }

    const primeiraConfirmacao = confirm(
        `Previa da virada de ano:\n\n1 ano para 2 ano: ${previa.primeiro_para_segundo}\n2 ano para 3 ano: ${previa.segundo_para_terceiro}\n3 ano concluidos: ${previa.terceiro_concluido}\nSem destino: ${previa.sem_destino}\n\nDeseja continuar?`
    );
    if (!primeiraConfirmacao) {
        return;
    }

    const texto = prompt('Digite VIRADA para confirmar a alteracao das turmas.');
    if (texto !== 'VIRADA') {
        alert('Virada de ano cancelada.');
        return;
    }

    try {
        const resposta = await fetch('/api/alunos/virada-ano', { method: 'POST' });
        const resultado = await resposta.json();

        if (!resposta.ok) {
            alert(resultado.detail || 'Erro ao realizar virada de ano.');
            return;
        }

        alert(`${resultado.mensagem}\nPromovidos: ${resultado.promovidos}\nConcluidos: ${resultado.concluidos}`);
        document.getElementById('filtroStatus').value = 'ativo';
        carregarDados();
    } catch (error) {
        console.error('Erro na virada de ano:', error);
        alert('Erro ao realizar virada de ano.');
    }
};

carregarDados();
