# ClickDom

Corrige o arquivo de importação Gestão Click → Domínio (blocos `|6000|V|` com débito e crédito na mesma linha `|6100|`).

## Rodar local
    pip install -r requirements.txt && uvicorn app.main:app --port 8000
    python3 tests/test_tratamento.py

## Deploy (Portainer / Docker Swarm)
1. Envie esta pasta ao servidor e construa a imagem no nó manager:

       docker build -t clickdom:1.0 .

2. Portainer → Stacks → Add stack → Web editor → cole o `docker-compose.yml`.
3. Para atualizar: construa `clickdom:1.1`, altere a tag na stack e faça *Update the stack*.

## Segurança
- Upload como corpo bruto, em memória; nada é gravado em disco e o nome do arquivo do usuário nunca é usado no servidor.
- Limite de 2 MB (app + Traefik), rate limit no Traefik, validação estrita do layout (`|NNNN|...|`), rejeição de binários.
- Conteúdo exibido só via `textContent` (sem XSS); CSP restritiva, sem scripts inline; docs/OpenAPI desativados.
- Container não-root, filesystem somente leitura, `cap_drop: ALL`, `no-new-privileges`, limites de CPU/memória.
- Sem banco de dados, shell ou subprocessos → sem superfície de SQL/command injection.
