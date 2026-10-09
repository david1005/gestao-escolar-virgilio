from app.models.notificacao import PreferenciaNotificacao


TIPOS_CONFIGURAVEIS = ('ocorrencia_antiga', 'retorno_pendente', 'alteracao')


def preferencias_usuario(db, usuario_id):
    registro = db.get(PreferenciaNotificacao, usuario_id)
    return {tipo: getattr(registro, tipo) if registro else True for tipo in TIPOS_CONFIGURAVEIS}
