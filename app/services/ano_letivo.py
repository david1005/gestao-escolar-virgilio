from datetime import date

from sqlalchemy.orm import Session

from app.models.sistema import AnoLetivo


def obter_ano_letivo_ativo(db: Session) -> AnoLetivo:
    ano = db.query(AnoLetivo).filter(AnoLetivo.ativo == True).first()
    if ano:
        return ano

    hoje = date.today()
    ano = AnoLetivo(
        nome=f"Ano Letivo {hoje.year}",
        ano=hoje.year,
        data_inicio=date(hoje.year, 1, 1),
        data_fim=date(hoje.year, 12, 31),
        ativo=True,
    )
    db.add(ano)
    db.flush()
    return ano


def buscar_ano_letivo_por_numero(db: Session, numero: int | None) -> AnoLetivo | None:
    if not numero:
        return None
    return db.query(AnoLetivo).filter(AnoLetivo.ano == numero).first()
