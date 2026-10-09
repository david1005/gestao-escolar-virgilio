const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

const source = fs.readFileSync(path.join(__dirname, '../static/js/registros.js'), 'utf8');
const security = fs.readFileSync(path.join(__dirname, '../static/js/security.js'), 'utf8');
const tabela = {innerHTML: ''};
const context = vm.createContext({
    window: {fetch: async () => ({ok: true})},
    document: {cookie: '', getElementById: id => id === 'tabelaRegistros' ? tabela : {value: '25'}},
    paginaAtualRegistros: 1, perfilUsuario: 'diretor_turma',
    getNomeAluno: () => 'Aluno', getTurmaAluno: () => 'Turma',
    atualizarInfoPaginacaoRegistros: () => {},
    formatarDataRegistro: () => '09/10/2026',
    ehSaidaAntecipada: tipo => tipo !== 'Atraso'
});
vm.runInContext(security, context);
vm.runInContext(source.slice(source.indexOf('function descricaoRetorno('), source.indexOf('function formatarDataRegistro(')), context);
vm.runInContext(source.slice(source.indexOf('function renderizarRegistros('), source.indexOf('function atualizarInfoPaginacaoRegistros(')), context);

context.renderizarRegistros([{id: 1, aluno_id: 1, tipo: 'Saida', tipo_saida: 'temporaria',
    status_retorno: 'Pendente', aula: 5, aula_retorno_prevista: 6}]);
assert.ok(tabela.innerHTML.includes('<span class="badge bg-info text-dark">Pendente</span>'));
assert.ok(!tabela.innerHTML.includes('&lt;span'));

const ataque = '<img src=x onerror=alert(1)>';
const html = context.descricaoRetorno({tipo: 'Saida', tipo_saida: 'temporaria',
    status_retorno: ataque, aula_retorno_prevista: ataque, aula_retorno_real: ataque});
assert.ok(!html.includes('<img'));
assert.ok(html.includes('&lt;img'));
assert.equal(context.descricaoRetorno({tipo: 'Atraso'}), '-');
assert.equal(context.descricaoRetorno({tipo: 'Saida', tipo_saida: 'definitiva'}),
    '<span class="badge bg-secondary">Não retorna</span>');
console.log('Retorno: badges renderizados e valores maliciosos escapados: OK');
