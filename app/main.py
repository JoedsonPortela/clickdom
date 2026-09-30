import base64
import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from .tratamento import ArquivoInvalido, tratar

MAX_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", 2 * 1024 * 1024))
STATIC = os.path.join(os.path.dirname(__file__), "static")

# Sem docs/openapi públicos: menos superfície de ataque.
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

CSP = ("default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
       "connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'")


@app.middleware("http")
async def cabecalhos_seguranca(request: Request, call_next):
    resp = await call_next(request)
    resp.headers["Content-Security-Policy"] = CSP
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Referrer-Policy"] = "no-referrer"
    resp.headers["Cache-Control"] = "no-store"
    resp.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
    return resp


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.post("/api/tratar")
async def api_tratar(request: Request):
    """Recebe o .txt como corpo bruto (sem multipart) e devolve o arquivo tratado.

    O arquivo vive só em memória durante a requisição. O nome do arquivo
    enviado pelo usuário nunca é usado no servidor.
    """
    declarado = request.headers.get("content-length")
    if declarado and declarado.isdigit() and int(declarado) > MAX_BYTES:
        raise HTTPException(413, "Arquivo maior que o limite permitido.")
    corpo = bytearray()
    async for parte in request.stream():
        corpo += parte
        if len(corpo) > MAX_BYTES:
            raise HTTPException(413, "Arquivo maior que o limite permitido.")
    try:
        r = tratar(bytes(corpo))
    except ArquivoInvalido as e:
        raise HTTPException(422, str(e))
    return JSONResponse({
        "arquivo_b64": base64.b64encode(r.conteudo).decode("ascii"),
        "linhas_entrada": r.linhas_entrada,
        "linhas_saida": r.linhas_saida,
        "blocos_corrigidos": r.blocos_corrigidos,
        "linhas_separadas": r.linhas_separadas,
        "detalhes": r.detalhes,
        "avisos": r.avisos,
    })


app.mount("/", StaticFiles(directory=STATIC, html=True), name="static")
