#!/usr/bin/env python3
"""
Para cada URL da lista: tenta copiar o "Copy markdown" pela área de transferência.
Se a cópia não for capturada, baixa a versão .md da própria página.
Salva cada resultado em um arquivo .md.

Uso:
    pip install playwright
    python -m playwright install chromium
    python copiar_markdown.py urls.txt --out markdown
    python copiar_markdown.py urls.txt --out markdown --headed   # mostra o navegador
"""

import argparse
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

BOTAO = re.compile(r"copy markdown", re.IGNORECASE)

# Roda antes de qualquer script da página. Captura o texto copiado por qualquer um dos
# caminhos comuns: writeText, clipboard.write, execCommand('copy') ou evento 'copy'.
CAPTURE_SCRIPT = """
window.__copiado = null;

const guardar = (texto) => {
    if (texto && String(texto).trim()) { window.__copiado = String(texto); }
};

navigator.clipboard.writeText = (texto) => { guardar(texto); return Promise.resolve(); };

navigator.clipboard.write = async (itens) => {
    for (const item of itens) {
        if (item.types.includes('text/plain')) {
            guardar(await (await item.getType('text/plain')).text());
        }
    }
};

document.addEventListener('copy', (e) => {
    guardar(e.clipboardData ? e.clipboardData.getData('text/plain') : '');
}, true);

const copiarOriginal = document.execCommand.bind(document);
document.execCommand = (comando, ...resto) => {
    if (comando === 'copy') {
        const ativo = document.activeElement;
        const usaCampo = ativo && (ativo.tagName === 'TEXTAREA' || ativo.tagName === 'INPUT');
        guardar(usaCampo ? ativo.value : window.getSelection().toString());
    }
    return copiarOriginal(comando, ...resto);
};
"""


def ler_urls(caminho):
    urls = []
    for linha in Path(caminho).read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if linha and not linha.startswith("#"):
            urls.append(linha)
    return urls


def url_limpa(url):
    # remove o fragmento (#...) e a query (?...)
    return url.split("#")[0].split("?")[0].rstrip("/")


def nome_arquivo(url, usados):
    """Usa o último trecho do link. Se já existir, acrescenta o trecho anterior."""
    partes = [p for p in urlparse(url_limpa(url)).path.split("/") if p]
    candidatos = [
        partes[-1] if partes else "pagina",
        "-".join(partes[-2:]),
        "-".join(partes[-3:]),
    ]
    for candidato in candidatos:
        nome = re.sub(r"[^A-Za-z0-9._-]+", "-", candidato).strip("-") + ".md"
        if nome not in usados:
            usados.add(nome)
            return nome
    base = re.sub(r"[^A-Za-z0-9._-]+", "-", candidatos[-1]).strip("-")
    n = 2
    while f"{base}-{n}.md" in usados:
        n += 1
    nome = f"{base}-{n}.md"
    usados.add(nome)
    return nome


def encontrar_botao(pagina, espera_ms=15000):
    alvo = pagina.get_by_role("button", name=BOTAO).or_(pagina.get_by_text(BOTAO)).first
    try:
        alvo.wait_for(state="visible", timeout=espera_ms)
        return alvo
    except Exception:
        return None


def diagnostico(pagina):
    try:
        titulo = pagina.title()
        textos = (
            pagina.locator("button, a, [role=button]")
            .filter(has_text=re.compile("copy", re.IGNORECASE))
            .all_inner_texts()
        )
        return f"título={titulo!r}; elementos com 'copy'={textos[:8]}"
    except Exception as erro:
        return f"diagnóstico indisponível ({erro})"


def copiar_markdown(pagina):
    botao = encontrar_botao(pagina)
    if botao is None:
        raise RuntimeError("botão 'Copy markdown' não apareceu. " + diagnostico(pagina))
    botao.click(timeout=10000)
    try:
        pagina.wait_for_function("window.__copiado !== null", timeout=20000)
    except Exception:
        raise RuntimeError(
            "clique feito, mas o site não enviou texto à área de transferência. "
            + diagnostico(pagina)
        )
    return pagina.evaluate("window.__copiado")


def baixar_md(contexto, limpa):
    resposta = contexto.request.get(limpa + ".md", timeout=30000)
    if resposta.status != 200:
        raise RuntimeError(f"{limpa}.md respondeu HTTP {resposta.status}")
    texto = resposta.text()
    if texto.lstrip().lower().startswith(("<!doctype", "<html")):
        raise RuntimeError(f"{limpa}.md devolveu HTML, não markdown")
    return texto


def obter_markdown(contexto, pagina, limpa):
    """Retorna (texto, origem). Tenta a cópia pelo botão e, se falhar, o .md."""
    try:
        return copiar_markdown(pagina), "botão Copy markdown"
    except Exception as erro_copia:
        try:
            return baixar_md(contexto, limpa), "arquivo .md"
        except Exception as erro_md:
            raise RuntimeError(f"{erro_copia} | alternativa .md falhou: {erro_md}")


def main():
    ap = argparse.ArgumentParser(description="Salva o 'Copy markdown' de cada página em um .md")
    ap.add_argument("lista", help="arquivo .txt com uma URL por linha")
    ap.add_argument("--out", default="markdown", help="pasta de saída (padrão: markdown)")
    ap.add_argument("--headed", action="store_true", help="mostra o navegador enquanto roda")
    ap.add_argument("--pausa", type=float, default=1.0, help="segundos entre páginas (padrão: 1)")
    args = ap.parse_args()

    urls = ler_urls(args.lista)
    saida = Path(args.out)
    saida.mkdir(parents=True, exist_ok=True)

    usados = set()
    salvos = []
    falhas = []

    with sync_playwright() as p:
        navegador = p.chromium.launch(headless=not args.headed)
        contexto = navegador.new_context(locale="en-US", viewport={"width": 1280, "height": 900})
        contexto.add_init_script(CAPTURE_SCRIPT)
        pagina = contexto.new_page()

        for i, url in enumerate(urls, 1):
            limpa = url_limpa(url)
            nome = nome_arquivo(url, usados)
            origem_permissao = f"{urlparse(limpa).scheme}://{urlparse(limpa).netloc}"
            print(f"[{i}/{len(urls)}] {limpa}")
            try:
                try:
                    contexto.grant_permissions(
                        ["clipboard-read", "clipboard-write"], origin=origem_permissao
                    )
                except Exception:
                    pass
                pagina.goto(limpa, wait_until="domcontentloaded", timeout=60000)
                try:
                    pagina.wait_for_load_state("networkidle", timeout=10000)
                except Exception:
                    pass
                texto, origem = obter_markdown(contexto, pagina, limpa)
                if not texto or not texto.strip():
                    raise RuntimeError("o texto veio vazio")
                conteudo = f"Source: {limpa}\n\n{texto.strip()}\n"
                (saida / nome).write_text(conteudo, encoding="utf-8")
                salvos.append(nome)
                print(f"    salvo ({origem}): {saida / nome}")
            except Exception as erro:
                motivo = str(erro).splitlines()[0] if str(erro) else type(erro).__name__
                falhas.append((limpa, motivo))
                print(f"    falhou: {motivo}")
            time.sleep(args.pausa)

        navegador.close()

    print(f"\nSalvos: {len(salvos)} de {len(urls)}")
    if falhas:
        print("Não salvos:")
        for url, motivo in falhas:
            print(f"  - {url}\n    motivo: {motivo}")

    # Só falha o job se nada foi salvo. Com resultados parciais, o commit ainda acontece.
    sys.exit(0 if salvos else 1)


if __name__ == "__main__":
    main()
