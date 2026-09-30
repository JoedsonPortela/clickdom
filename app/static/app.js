"use strict";
const $ = (id) => document.getElementById(id);
const MAX = 2 * 1024 * 1024;
let blob = null, nomeSaida = "importacao-tratada.txt";

function erro(msg) { const e = $("erro"); e.textContent = msg; e.hidden = !msg; }

// Cria células só com textContent: conteúdo do arquivo nunca vira HTML.
function linha(valores) {
  const tr = document.createElement("tr");
  for (const v of valores) { const td = document.createElement("td"); td.textContent = v; tr.appendChild(td); }
  return tr;
}

async function enviar(file) {
  erro(""); $("resultado").hidden = true;
  if (!file) return;
  if (!/\.txt$/i.test(file.name)) return erro("Envie um arquivo .txt.");
  if (file.size > MAX) return erro("Arquivo maior que 2 MB.");
  try {
    const r = await fetch("/api/tratar", { method: "POST", headers: { "Content-Type": "application/octet-stream" }, body: file });
    const j = await r.json().catch(() => ({}));
    if (!r.ok) return erro(typeof j.detail === "string" ? j.detail : "Não foi possível tratar o arquivo.");

    const bin = Uint8Array.from(atob(j.arquivo_b64), (c) => c.charCodeAt(0));
    blob = new Blob([bin], { type: "text/plain;charset=iso-8859-1" });
    nomeSaida = file.name.replace(/\.txt$/i, "").replace(/[^\w.\- ]+/g, "_") + " - TRATADO.txt";

    $("m-blocos").textContent = j.blocos_corrigidos;
    $("m-linhas").textContent = j.linhas_separadas;
    $("m-total").textContent = j.linhas_saida;
    $("nada").hidden = j.linhas_separadas > 0;
    const av = $("avisos"); av.replaceChildren();
    for (const a of j.avisos) { const li = document.createElement("li"); li.textContent = a; av.appendChild(li); }
    const tb = document.querySelector("#tabela tbody"); tb.replaceChildren();
    for (const d of j.detalhes) tb.appendChild(linha([d.linha, d.data, d.valor, d.historico]));
    $("tabela").hidden = j.detalhes.length === 0;
    $("resultado").hidden = false;
  } catch { erro("Falha de comunicação com o servidor."); }
}

const drop = $("drop"), input = $("file");
drop.addEventListener("click", () => input.click());
drop.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); input.click(); } });
input.addEventListener("change", () => { enviar(input.files[0]); input.value = ""; });
for (const ev of ["dragenter", "dragover"]) drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.add("over"); });
for (const ev of ["dragleave", "drop"]) drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.remove("over"); });
drop.addEventListener("drop", (e) => enviar(e.dataTransfer.files[0]));

$("baixar").addEventListener("click", () => {
  if (!blob) return;
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob); a.download = nomeSaida;
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
});
