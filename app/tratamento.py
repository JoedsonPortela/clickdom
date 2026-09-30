"""Regra de negócio: corrige o arquivo de importação Gestão Click -> Domínio.

Dentro de um bloco |6000|V| (várias partidas), cada linha |6100| deve ter apenas
UMA conta (débito OU crédito). Quando o Gestão Click rateia por centro de custo,
ele preenche as duas na mesma linha; aqui cada linha assim vira duas.

O módulo trata o conteúdo apenas como texto: nada é executado, interpolado em
comandos ou gravado em disco.
"""
import re
from dataclasses import dataclass, field

REGISTRO = re.compile(r"^\|\d{4}\|")


class ArquivoInvalido(ValueError):
    """Conteúdo que não parece um arquivo de importação do Domínio."""


@dataclass
class Resultado:
    conteudo: bytes
    linhas_entrada: int = 0
    linhas_saida: int = 0
    blocos_corrigidos: int = 0
    linhas_separadas: int = 0
    detalhes: list = field(default_factory=list)  # (linha_original, data, historico)
    avisos: list = field(default_factory=list)


def _valor(txt: str):
    try:
        return round(float(txt.replace(".", "").replace(",", ".")), 2)
    except ValueError:
        return None


def tratar(dados: bytes) -> Resultado:
    if b"\x00" in dados:
        raise ArquivoInvalido("O arquivo contém bytes nulos; não é um arquivo de texto.")
    if not dados.strip():
        raise ArquivoInvalido("O arquivo está vazio.")

    # latin-1 nunca falha e preserva todos os bytes na volta.
    texto = dados.decode("latin-1")
    eol = "\r\n" if "\r\n" in texto else "\n"
    linhas = texto.split(eol)
    sufixo_eol = bool(linhas) and linhas[-1] == ""
    if sufixo_eol:
        linhas.pop()

    if not linhas or not linhas[0].startswith("|0000|"):
        raise ArquivoInvalido("Arquivo não reconhecido: a primeira linha deve ser o registro |0000|.")
    for n, l in enumerate(linhas, 1):
        if not (REGISTRO.match(l) and l.endswith("|")):
            raise ArquivoInvalido(f"Linha {n} fora do layout esperado (|NNNN|...|).")

    res = Resultado(conteudo=b"", linhas_entrada=len(linhas))
    saida, em_v, bloco_tocado = [], False, False
    deb = cred = 0.0  # conferência por bloco V

    def fecha_bloco(n_linha):
        if em_v and abs(deb - cred) > 0.005:
            res.avisos.append(f"Bloco V encerrado antes da linha {n_linha}: débitos {deb:.2f} ≠ créditos {cred:.2f}.")

    for n, linha in enumerate(linhas, 1):
        c = linha.split("|")
        if c[1] == "6000":
            fecha_bloco(n)
            em_v = len(c) > 2 and c[2].strip() == "V"
            deb = cred = 0.0
            bloco_tocado = False
        elif c[1] == "6100" and len(c) > 5:
            d_conta, c_conta = c[3].strip(), c[4].strip()
            v = _valor(c[5]) or 0.0
            if em_v and d_conta and c_conta:
                a, b = c[:], c[:]
                a[4] = ""   # só débito
                b[3] = ""   # só crédito
                saida += ["|".join(a), "|".join(b)]
                res.linhas_separadas += 1
                res.detalhes.append({"linha": n, "data": c[2], "valor": c[5], "historico": c[7] if len(c) > 7 else ""})
                if not bloco_tocado:
                    res.blocos_corrigidos += 1
                    bloco_tocado = True
                deb += v; cred += v
                continue
            if em_v:
                if d_conta: deb += v
                if c_conta: cred += v
        saida.append(linha)
    fecha_bloco(len(linhas) + 1)

    res.linhas_saida = len(saida)
    res.conteudo = (eol.join(saida) + (eol if sufixo_eol else "")).encode("latin-1")
    return res
