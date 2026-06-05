let anexoContextoAtual = null;

function garantirModalAnexos() {
    if (document.getElementById('modalAnexosContexto')) return;

    document.body.insertAdjacentHTML('beforeend', `
        <div class="modal fade" id="modalAnexosContexto" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header bg-primary text-white">
                        <h5 class="modal-title"><i class="bi bi-paperclip me-2"></i><span id="anexoModalTitulo">Anexos</span></h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="border rounded p-3 mb-3">
                            <label class="form-label fw-semibold">Adicionar documento</label>
                            <div class="input-group">
                                <input type="file" class="form-control" id="anexoContextoArquivo">
                                <button class="btn btn-primary" type="button" onclick="enviarAnexoContexto()">
                                    <i class="bi bi-upload me-1"></i>Anexar
                                </button>
                            </div>
                            <div class="form-text">PDF, imagens, Word. Tamanho maximo: 10 MB.</div>
                        </div>
                        <div class="table-responsive">
                            <table class="table table-hover align-middle mb-0">
                                <thead class="table-light">
                                    <tr>
                                        <th>Arquivo</th>
                                        <th>Enviado por</th>
                                        <th>Data</th>
                                        <th>Acoes</th>
                                    </tr>
                                </thead>
                                <tbody id="anexoContextoLista">
                                    <tr><td colspan="4" class="text-center text-muted">Carregando...</td></tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `);
}

function formatarDataAnexo(valor) {
    if (!valor) return '-';
    return new Date(valor).toLocaleString('pt-BR');
}

async function carregarAnexosContexto() {
    const tbody = document.getElementById('anexoContextoLista');
    const { entidade, entidadeId } = anexoContextoAtual;
    const res = await fetch(`/api/sistema/anexos?entidade=${entidade}&entidade_id=${entidadeId}`);
    const anexos = await res.json();

    if (!anexos.length) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">Nenhum anexo enviado.</td></tr>';
        return;
    }

    tbody.innerHTML = anexos.map(anexo => `
        <tr>
            <td><a href="${anexo.url}" target="_blank"><i class="bi bi-file-earmark me-1"></i>${anexo.nome_original}</a></td>
            <td>${anexo.enviado_por_nome || '-'}</td>
            <td>${formatarDataAnexo(anexo.criado_em)}</td>
            <td>
                <a class="btn btn-sm btn-outline-success me-1" href="${anexo.url}" target="_blank" title="Abrir">
                    <i class="bi bi-box-arrow-up-right"></i>
                </a>
                <button class="btn btn-sm btn-outline-danger" onclick="excluirAnexoContexto(${anexo.id})" title="Excluir">
                    <i class="bi bi-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

async function abrirAnexos(entidade, entidadeId, titulo) {
    garantirModalAnexos();
    anexoContextoAtual = { entidade, entidadeId };
    document.getElementById('anexoModalTitulo').textContent = titulo || 'Anexos';
    document.getElementById('anexoContextoArquivo').value = '';
    new bootstrap.Modal(document.getElementById('modalAnexosContexto')).show();
    await carregarAnexosContexto();
}

async function enviarAnexoPara(entidade, entidadeId, arquivo) {
    if (!arquivo) return null;
    const form = new FormData();
    form.append('entidade', entidade);
    form.append('entidade_id', entidadeId);
    form.append('arquivo', arquivo);
    const res = await fetch('/api/sistema/anexos', { method: 'POST', body: form });
    if (!res.ok) {
        const erro = await res.json();
        throw new Error(erro.detail || 'Erro ao enviar anexo.');
    }
    return res.json();
}

async function enviarAnexoContexto() {
    const arquivo = document.getElementById('anexoContextoArquivo').files[0];
    if (!arquivo) {
        alert('Selecione um arquivo.');
        return;
    }
    try {
        await enviarAnexoPara(anexoContextoAtual.entidade, anexoContextoAtual.entidadeId, arquivo);
        document.getElementById('anexoContextoArquivo').value = '';
        await carregarAnexosContexto();
    } catch (erro) {
        alert(erro.message);
    }
}

async function excluirAnexoContexto(id) {
    if (!confirm('Excluir este anexo?')) return;
    const res = await fetch(`/api/sistema/anexos/${id}`, { method: 'DELETE' });
    if (res.ok) {
        await carregarAnexosContexto();
    } else {
        const erro = await res.json();
        alert(erro.detail || 'Erro ao excluir anexo.');
    }
}
