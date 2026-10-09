from datetime import datetime, timedelta
from hashlib import sha256
from uuid import uuid4
from fastapi import HTTPException
from sqlalchemy import text
from app.models.notificacao import TentativaLogin
from app.services.notificacoes import notificar_bloqueio


def chave(email, ip):
    return sha256(f'{ip}:{email.strip().lower()}'.encode()).hexdigest()


def bloquear_chave(db, email, ip):
    # Serialize requests for the same identity across PostgreSQL workers.
    if db.get_bind().dialect.name == 'postgresql':
        numero = int(chave(email, ip)[:15], 16)
        db.execute(text('SELECT pg_advisory_xact_lock(:chave)'), {'chave': numero})


def verificar_bloqueio(db, email, ip):
    bloquear_chave(db, email, ip)
    item = db.get(TentativaLogin, chave(email, ip))
    if item and item.bloqueado_ate and item.bloqueado_ate > datetime.now():
        raise HTTPException(429, 'Muitas tentativas de login. Tente novamente em alguns minutos.')


def falhar(db, email, ip):
    bloquear_chave(db, email, ip)
    agora = datetime.now()
    item = db.get(TentativaLogin, chave(email, ip))
    if item is None:
        item = TentativaLogin(chave=chave(email, ip), tentativas=0, inicio=agora)
        db.add(item)
    if item.inicio < agora - timedelta(minutes=10) and (
        not item.bloqueado_ate or item.bloqueado_ate <= agora):
        item.tentativas = 0
        item.inicio = agora
        item.bloqueado_ate = None
    item.tentativas += 1
    if item.tentativas == 5:
        item.bloqueado_ate = agora + timedelta(minutes=10)
        notificar_bloqueio(db, email, ip, f'login:{uuid4().hex}')
    db.flush()


def limpar(db, email, ip):
    item = db.get(TentativaLogin, chave(email, ip))
    if item:
        db.delete(item)
        db.flush()
