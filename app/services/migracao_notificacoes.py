from sqlalchemy import inspect, text


def migrar_criadores(engine):
    inspector = inspect(engine)
    with engine.begin() as conn:
        for tabela, entidade in [('registros', 'registro'), ('ocorrencias', 'ocorrencia')]:
            if 'criado_por_id' not in {c['name'] for c in inspector.get_columns(tabela)}:
                conn.execute(text(f'ALTER TABLE {tabela} ADD COLUMN criado_por_id INTEGER'))
            # Audit evidence identifies the creator; names alone are not reliable.
            conn.execute(text(f'''
                UPDATE {tabela} SET criado_por_id = (
                    SELECT usuario_id FROM auditoria
                    WHERE entidade = :entidade AND entidade_id = {tabela}.id
                        AND acao = 'criou' AND usuario_id IS NOT NULL
                    ORDER BY criado_em, id LIMIT 1
                ) WHERE criado_por_id IS NULL
            '''), {'entidade': entidade})
