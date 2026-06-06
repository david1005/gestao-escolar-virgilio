let dadosAluno = null;

async function carregarAluno() {
    const res = await fetch(`/api/dashboard/aluno/${alunoId}`);
    dadosAluno = await res.json();

    const { aluno, resumo, ocorrencias, registros } = dadosAluno;
    gerarGrafico(registros, ocorrencias);

    // Cabeçalho
    document.getElementById('nomeAluno').textContent = aluno.nome;
    document.getElementById('turmaAluno').textContent = aluno.turma;
    document.getElementById('matriculaAluno').textContent = aluno.matricula;
    document.getElementById('responsavelAluno').textContent = aluno.responsavel;
    document.getElementById('contatoAluno').textContent = aluno.contato_responsavel;

    // Cards
    document.getElementById('totalAtrasos').textContent = resumo.total_atrasos;
    document.getElementById('totalSaidas').textContent = resumo.total_saidas;
    document.getElementById('totalOcorrencias').textContent = resumo.total_ocorrencias;
    document.getElementById('proximaMedida').textContent = resumo.proxima_medida;

    // Tabela registros
    const tbodyReg = document.getElementById('tabelaRegistros');
    if (registros.length === 0) {
        tbodyReg.innerHTML = '<tr><td colspan="4" class="text-center text-muted">Nenhum registro.</td></tr>';
    } else {
        tbodyReg.innerHTML = registros.map(r => {
            const badge = r.tipo === 'Atraso'
                ? '<span class="badge bg-warning text-dark">Atraso</span>'
                : '<span class="badge bg-info">Saída</span>';
            return `
                <tr>
                    <td>${r.data}</td>
                    <td>${badge}</td>
                    <td>${r.aula}ª aula</td>
                    <td>${r.motivo}</td>
                </tr>
            `;
        }).join('');
    }

    // Tabela ocorrências
    const tbodyOcorr = document.getElementById('tabelaOcorrencias');
    if (ocorrencias.length === 0) {
        tbodyOcorr.innerHTML = '<tr><td colspan="3" class="text-center text-muted">Nenhuma ocorrência.</td></tr>';
    } else {
        tbodyOcorr.innerHTML = ocorrencias.map(o => {
            let badge = '';
            if (o.medida === 'Só registro') badge = '<span class="badge bg-secondary">Só registro</span>';
            else if (o.medida.includes('Advertência')) badge = '<span class="badge bg-warning text-dark">Advertência</span>';
            else badge = '<span class="badge bg-danger">Suspensão</span>';
            return `
                <tr>
                    <td>${o.data}</td>
                    <td>${o.tipo}</td>
                    <td>${badge}</td>
                </tr>
            `;
        }).join('');
    }

    carregarAnexosAluno();
}

async function carregarAnexosAluno() {
    const tbody = document.getElementById('tabelaAnexosAluno');
    if (!tbody) return;
    const res = await fetch(`/api/sistema/anexos?entidade=aluno&entidade_id=${alunoId}`);
    const anexos = await res.json();
    if (!anexos.length) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">Nenhum documento anexado.</td></tr>';
        return;
    }
    tbody.innerHTML = anexos.map(anexo => `
        <tr>
            <td><a href="${anexo.url}" target="_blank"><i class="bi bi-file-earmark me-1"></i>${anexo.nome_original}</a></td>
            <td>${anexo.enviado_por_nome || '-'}</td>
            <td>${new Date(anexo.criado_em).toLocaleString('pt-BR')}</td>
            <td>
                <a class="btn btn-sm btn-outline-success me-1" href="${anexo.url}" target="_blank" title="Abrir">
                    <i class="bi bi-box-arrow-up-right"></i>
                </a>
                <button class="btn btn-sm btn-outline-danger" onclick="excluirAnexoAluno(${anexo.id})" title="Excluir">
                    <i class="bi bi-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

async function excluirAnexoAluno(id) {
    if (!confirm('Excluir este documento?')) return;
    const res = await fetch(`/api/sistema/anexos/${id}`, { method: 'DELETE' });
    if (res.ok) carregarAnexosAluno();
    else {
        const erro = await res.json();
        alert(erro.detail || 'Erro ao excluir documento.');
    }
}

function gerarRelatorio() {
    if (!dadosAluno) return;
    const { aluno, resumo, ocorrencias, registros } = dadosAluno;
    const logoUrl = `${window.location.origin}/static/img/logo-escola.png`;

    const linhasRegistros = registros.map(r =>
        `<tr><td>${r.data}</td><td>${r.tipo}</td><td>${r.aula}ª aula</td><td>${r.motivo}</td></tr>`
    ).join('');

    const linhasOcorrencias = ocorrencias.map(o =>
        `<tr><td>${o.data}</td><td>${o.tipo}</td><td>${o.descricao}</td><td>${o.medida}</td></tr>`
    ).join('');

    const conteudo = `
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body { font-family: Arial, sans-serif; padding: 40px; color: #222; }
                .topo { display: flex; align-items: center; gap: 16px; border-bottom: 1px solid #ccc; padding-bottom: 14px; margin-bottom: 20px; }
                .logo { width: 78px; height: 78px; object-fit: contain; }
                .cabecalho { flex: 1; text-align: center; }
                h2 { margin: 0 0 4px; }
                h3 { color: #555; margin-top: 0; }
                .topo + h2, .topo + h2 + h3, .topo + h2 + h3 + .linha { display: none; }
                table { width: 100%; border-collapse: collapse; margin-top: 12px; }
                th { background: #f0f0f0; padding: 8px; text-align: left; font-size: 13px; }
                td { padding: 7px 8px; border-bottom: 1px solid #eee; font-size: 13px; }
                .secao { margin-top: 30px; }
                .secao h4 { border-bottom: 2px solid #0d6efd; padding-bottom: 6px; color: #0d6efd; }
                .resumo { display: flex; gap: 20px; margin: 16px 0; }
                .card-res { border: 1px solid #ddd; border-radius: 8px; padding: 12px 20px; text-align: center; flex: 1; }
                .card-res h3 { font-size: 28px; margin: 4px 0; }
                .linha { border-top: 1px solid #ccc; margin: 20px 0; }
            </style>
        </head>
        <body>
            <div class="topo">
                <img class="logo" src="${logoUrl}" onerror="this.style.display='none'">
                <div class="cabecalho">
                    <h2>EEEP Governador Virgilio Tavora</h2>
                    <h3>Relatorio Individual do Aluno</h3>
                </div>
            </div>
            <h2>Escola Virgílio Távora</h2>
            <h3>Relatório Individual do Aluno</h3>
            <div class="linha"></div>

            <p><strong>Nome:</strong> ${aluno.nome}</p>
            <p><strong>Matrícula:</strong> ${aluno.matricula}</p>
            <p><strong>Turma:</strong> ${aluno.turma}</p>
            <p><strong>Responsável:</strong> ${aluno.responsavel} — ${aluno.contato_responsavel}</p>

            <div class="resumo">
                <div class="card-res"><h3>${resumo.total_atrasos}</h3>Atrasos</div>
                <div class="card-res"><h3>${resumo.total_saidas}</h3>Saídas Antecipadas</div>
                <div class="card-res"><h3>${resumo.total_ocorrencias}</h3>Ocorrências</div>
            </div>

            <div class="secao">
                <h4>Atrasos e Saídas Antecipadas</h4>
                <table>
                    <thead><tr><th>Data</th><th>Tipo</th><th>Aula</th><th>Motivo</th></tr></thead>
                    <tbody>${linhasRegistros || '<tr><td colspan="4">Nenhum registro.</td></tr>'}</tbody>
                </table>
            </div>

            <div class="secao">
                <h4>Ocorrências</h4>
                <table>
                    <thead><tr><th>Data</th><th>Tipo</th><th>Descrição</th><th>Medida</th></tr></thead>
                    <tbody>${linhasOcorrencias || '<tr><td colspan="4">Nenhuma ocorrência.</td></tr>'}</tbody>
                </table>
            </div>

            <div style="text-align:center; margin-top:40px; font-size:12px; color:#aaa;">
              Relatório gerado em ${new Date().toLocaleDateString('pt-BR')} — R. Pergentino Silva, S/N - Seminário, Crato-CE, 63123-440
            </div>
        </body>
        </html>
    `;

    const janela = window.open('', '_blank');
    janela.document.write(conteudo);
    janela.document.close();
    janela.print();
}

function gerarGrafico(registros, ocorrencias) {
    const meses = {};

    registros.forEach(r => {
        const mes = r.data.substring(0, 7);
        if (!meses[mes]) meses[mes] = { atrasos: 0, ocorrencias: 0 };
        if (r.tipo === 'Atraso') meses[mes].atrasos++;
        else meses[mes].ocorrencias++;
    });

    ocorrencias.forEach(o => {
        const mes = o.data.substring(0, 7);
        if (!meses[mes]) meses[mes] = { atrasos: 0, ocorrencias: 0 };
        meses[mes].ocorrencias++;
    });

    const labels = Object.keys(meses).sort().map(m => {
        const [ano, mes] = m.split('-');
        return new Date(ano, mes - 1).toLocaleDateString('pt-BR', { month: 'short', year: 'numeric' });
    });

    const dadosAtrasos = Object.keys(meses).sort().map(m => meses[m].atrasos);
    const dadosOcorrencias = Object.keys(meses).sort().map(m => meses[m].ocorrencias);

    new Chart(document.getElementById('graficoEvolucao'), {
        type: 'line',
        data: {
            labels,
            datasets: [
                {
                    label: 'Atrasos',
                    data: dadosAtrasos,
                    borderColor: '#ffc107',
                    backgroundColor: 'rgba(255,193,7,0.1)',
                    tension: 0.4,
                    fill: true
                },
                {
                    label: 'Ocorrências',
                    data: dadosOcorrencias,
                    borderColor: '#dc3545',
                    backgroundColor: 'rgba(220,53,69,0.1)',
                    tension: 0.4,
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } }
        }
    });
}

carregarAluno();
