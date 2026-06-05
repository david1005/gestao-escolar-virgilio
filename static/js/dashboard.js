let dashboardData = null;
let filtrosCarregados = false;
const charts = {};

function getFiltros() {
    const params = new URLSearchParams();
    const campos = [
        ['ano_letivo', 'filtroAnoLetivo'],
        ['mes', 'filtroMes'],
        ['curso_id', 'filtroCurso'],
        ['turma_id', 'filtroTurma'],
        ['data_inicio', 'filtroInicio'],
        ['data_fim', 'filtroFim']
    ];

    campos.forEach(([param, id]) => {
        const valor = document.getElementById(id).value;
        if (valor) params.set(param, valor);
    });

    return params;
}

async function carregarDashboard() {
    const params = getFiltros();
    const res = await fetch(`/api/dashboard/gerencial?${params.toString()}`);
    dashboardData = await res.json();

    if (!filtrosCarregados) {
        preencherFiltros(dashboardData.filtros);
        filtrosCarregados = true;
    }

    renderizarCards(dashboardData.resumo);
    renderizarGraficos(dashboardData);
    renderizarRankings(dashboardData);
}

function preencherFiltros(filtros) {
    const anoAtual = new Date().getFullYear();
    document.getElementById('filtroAnoLetivo').value = anoAtual;

    const cursoSelect = document.getElementById('filtroCurso');
    cursoSelect.innerHTML = '<option value="">Todos</option>' +
        filtros.cursos.map(c => `<option value="${c.id}">${c.nome}</option>`).join('');

    preencherTurmas(filtros.turmas);

    cursoSelect.addEventListener('change', () => {
        document.getElementById('filtroTurma').value = '';
        preencherTurmas(dashboardData.filtros.turmas);
        carregarDashboard();
    });
}

function preencherTurmas(turmas) {
    const cursoId = document.getElementById('filtroCurso').value;
    const turmaSelect = document.getElementById('filtroTurma');
    const turmaAtual = turmaSelect.value;
    const filtradas = cursoId
        ? turmas.filter(t => t.curso_id === parseInt(cursoId))
        : turmas;

    turmaSelect.innerHTML = '<option value="">Todas</option>' +
        filtradas.map(t => `<option value="${t.id}">${t.nome}</option>`).join('');
    turmaSelect.value = filtradas.some(t => String(t.id) === turmaAtual) ? turmaAtual : '';
}

function renderizarCards(resumo) {
    document.getElementById('cardAlunosAtivos').textContent = resumo.alunos_ativos;
    document.getElementById('cardTotalAlunos').textContent = resumo.total_alunos;
    document.getElementById('cardAtrasos').textContent = resumo.atrasos;
    document.getElementById('cardSaidas').textContent = resumo.saidas;
    document.getElementById('cardOcorrencias').textContent = resumo.ocorrencias;
    document.getElementById('cardAbertas').textContent = resumo.ocorrencias_abertas;
    document.getElementById('cardGraves').textContent = resumo.ocorrencias_graves;
    document.getElementById('cardResolvidas').textContent = resumo.ocorrencias_resolvidas;
}

function destruirChart(id) {
    if (charts[id]) {
        charts[id].destroy();
        charts[id] = null;
    }
}

function corTextoGrafico() {
    return document.documentElement.getAttribute('data-bs-theme') === 'dark' ? '#e5e7eb' : '#212529';
}

function opcoesBase() {
    const color = corTextoGrafico();
    return {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
            legend: { labels: { color } }
        },
        scales: {
            x: { ticks: { color }, grid: { color: 'rgba(148, 163, 184, 0.18)' } },
            y: { beginAtZero: true, ticks: { color, precision: 0 }, grid: { color: 'rgba(148, 163, 184, 0.18)' } }
        }
    };
}

function renderizarGraficos(data) {
    destruirChart('turmas');
    destruirChart('status');
    destruirChart('evolucao');

    charts.turmas = new Chart(document.getElementById('graficoTurmas'), {
        type: 'bar',
        data: {
            labels: data.por_turma.map(t => t.turma),
            datasets: [
                { label: 'Atrasos', data: data.por_turma.map(t => t.atrasos), backgroundColor: '#f59e0b', borderRadius: 5 },
                { label: 'Saidas', data: data.por_turma.map(t => t.saidas), backgroundColor: '#0ea5e9', borderRadius: 5 },
                { label: 'Ocorrencias', data: data.por_turma.map(t => t.ocorrencias), backgroundColor: '#ef4444', borderRadius: 5 }
            ]
        },
        options: opcoesBase()
    });

    charts.status = new Chart(document.getElementById('graficoStatus'), {
        type: 'doughnut',
        data: {
            labels: data.status_ocorrencias.map(s => s.status),
            datasets: [{
                data: data.status_ocorrencias.map(s => s.total),
                backgroundColor: ['#f59e0b', '#06b6d4', '#22c55e']
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { position: 'bottom', labels: { color: corTextoGrafico() } } }
        }
    });

    charts.evolucao = new Chart(document.getElementById('graficoEvolucao'), {
        type: 'line',
        data: {
            labels: data.evolucao_mensal.map(m => m.mes),
            datasets: [
                { label: 'Atrasos', data: data.evolucao_mensal.map(m => m.atrasos), borderColor: '#f59e0b', backgroundColor: 'rgba(245, 158, 11, .12)', tension: .3, fill: true },
                { label: 'Saidas', data: data.evolucao_mensal.map(m => m.saidas), borderColor: '#0ea5e9', backgroundColor: 'rgba(14, 165, 233, .12)', tension: .3, fill: true },
                { label: 'Ocorrencias', data: data.evolucao_mensal.map(m => m.ocorrencias), borderColor: '#ef4444', backgroundColor: 'rgba(239, 68, 68, .12)', tension: .3, fill: true }
            ]
        },
        options: opcoesBase()
    });
}

function linkAluno(aluno) {
    return `<a href="/aluno/${aluno.id}" class="text-decoration-none fw-semibold">${aluno.nome}</a>`;
}

function renderRanking(tbodyId, lista, tipo) {
    const tbody = document.getElementById(tbodyId);
    if (!lista.length) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">Nenhum dado.</td></tr>';
        return;
    }

    if (tipo === 'atencao') {
        tbody.innerHTML = lista.map(a => `
            <tr>
                <td>${linkAluno(a)}</td>
                <td>${a.turma}</td>
                <td><span class="badge bg-warning text-dark">${a.atrasos}</span></td>
                <td><span class="badge bg-danger">${a.ocorrencias}</span></td>
                <td><span class="badge bg-dark">${a.graves}</span></td>
            </tr>
        `).join('');
        return;
    }

    if (tipo === 'criticos') {
        tbody.innerHTML = lista.map(a => `
            <tr>
                <td>${linkAluno(a)}</td>
                <td>${a.turma}</td>
                <td><span class="badge bg-warning text-dark">${a.abertas}</span></td>
                <td><span class="badge bg-danger">${a.graves}</span></td>
                <td><span class="badge bg-secondary">${a.ocorrencias}</span></td>
            </tr>
        `).join('');
        return;
    }

    tbody.innerHTML = lista.map((a, i) => `
        <tr>
            <td><strong>${i + 1}º</strong></td>
            <td>${linkAluno(a)}</td>
            <td>${a.turma}</td>
            <td><span class="badge ${tipo === 'atrasos' ? 'bg-warning text-dark' : 'bg-danger'}">${tipo === 'atrasos' ? a.atrasos : a.ocorrencias}</span></td>
        </tr>
    `).join('');
}

function renderizarRankings(data) {
    renderRanking('rankingAtencao', data.ranking_atencao, 'atencao');
    renderRanking('alunosCriticos', data.alunos_criticos, 'criticos');
    renderRanking('rankingAtrasos', data.ranking_atrasos, 'atrasos');
    renderRanking('rankingOcorrencias', data.ranking_ocorrencias, 'ocorrencias');
}

function exportarRelatorio() {
    if (!dashboardData) return;

    const linhas = [
        ['Indicador', 'Valor'],
        ['Alunos ativos', dashboardData.resumo.alunos_ativos],
        ['Total de alunos', dashboardData.resumo.total_alunos],
        ['Atrasos', dashboardData.resumo.atrasos],
        ['Saidas antecipadas', dashboardData.resumo.saidas],
        ['Ocorrencias', dashboardData.resumo.ocorrencias],
        ['Ocorrencias abertas', dashboardData.resumo.ocorrencias_abertas],
        ['Ocorrencias graves', dashboardData.resumo.ocorrencias_graves],
        ['Resolvidas', dashboardData.resumo.ocorrencias_resolvidas],
        [],
        ['Turma', 'Atrasos', 'Saidas', 'Ocorrencias'],
        ...dashboardData.por_turma.map(t => [t.turma, t.atrasos, t.saidas, t.ocorrencias]),
        [],
        ['Alunos em atencao', 'Turma', 'Atrasos', 'Ocorrencias', 'Graves', 'Abertas'],
        ...dashboardData.ranking_atencao.map(a => [a.nome, a.turma, a.atrasos, a.ocorrencias, a.graves, a.abertas])
    ];

    const csv = '\ufeff' + linhas.map(linha =>
        linha.map(valor => `"${String(valor ?? '').replace(/"/g, '""')}"`).join(';')
    ).join('\n');

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `dashboard_${new Date().toISOString().slice(0, 10)}.csv`;
    link.click();
    URL.revokeObjectURL(link.href);
}

['filtroAnoLetivo', 'filtroMes', 'filtroTurma', 'filtroInicio', 'filtroFim'].forEach(id => {
    document.getElementById(id).addEventListener('change', carregarDashboard);
});

document.addEventListener('themechange', () => {
    if (dashboardData) renderizarGraficos(dashboardData);
});

document.getElementById('filtroAnoLetivo').value = new Date().getFullYear();
carregarDashboard();
