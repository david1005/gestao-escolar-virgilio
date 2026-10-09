SECURITY_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'self'; "
        "base-uri 'self'; "
        "connect-src 'self'; "
        "font-src 'self' data:; "
        "form-action 'self'; "
        "frame-ancestors 'none'; "
        "img-src 'self' data: blob:; "
        "object-src 'none'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'"
    ),
    "Permissions-Policy": "camera=(), geolocation=(), microphone=()",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
}


def configuracao_documentacao(producao: bool) -> dict:
    if producao:
        return {"docs_url": None, "redoc_url": None, "openapi_url": None}
    return {"docs_url": "/docs", "redoc_url": "/redoc", "openapi_url": "/openapi.json"}


def aplicar_cabecalhos_seguranca(response, producao: bool, caminho: str) -> None:
    for nome, valor in SECURITY_HEADERS.items():
        response.headers[nome] = valor

    if producao:
        response.headers["Strict-Transport-Security"] = "max-age=31536000"

    if not caminho.startswith("/static/"):
        response.headers.setdefault("Cache-Control", "no-store")
