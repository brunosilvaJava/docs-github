#!/usr/bin/env python3
"""
Para cada URL da lista: abre a página, clica em "Copy markdown",
captura o texto copiado e salva em um arquivo .md.

Uso:
    pip install playwright
    python -m playwright install chromium
    python copiar_markdown.py urls.txt --out markdown
    python copiar_markdown.py urls.txt --out markdown --headed   # mostra o navegador
"""

import argparse
import re
import time
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

BUTTON_TEXT = "Copy markdown"

# Roda antes de qualquer script da página. Guarda o texto que o site envia
# ao clipboard, para ler o valor mesmo sem permissão de leitura da área de transferência.
CAPTURE_SCRIPT = """
window.__copiado = null;
navigator.clipboard.writeText = (texto) => {
    window.__copiado = String(texto);
    return Promise.resolve();
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


def copiar_markdown(pagina):
    botao = pagina.get_by_role("button", name=BUTTON_TEXT).first
    if botao.count() == 0:
        botao = pagina.get_by_text(BUTTON_TEXT, exact=True).first
    botao.wait_for(state="visible", timeout=20000)
    botao.click()
    try:
        pagina.wait_for_function("window.__copiado !== null", timeout=5000)
        return pagina.evaluate("window.__copiado")
    except Exception:
        # Se o site não usou writeText, tenta a área de transferência do navegador
        return pagina.evaluate("navigator.clipboard.readText()")


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
        contexto = navegador.new_context(locale="en-US")
        contexto.add_init_script(CAPTURE_SCRIPT)
        pagina = contexto.new_page()

        for i, url in enumerate(urls, 1):
            limpa = url_limpa(url)
            nome = nome_arquivo(url, usados)
            print(f"[{i}/{len(urls)}] {limpa}")
            try:
                pagina.goto(limpa, wait_until="domcontentloaded", timeout=60000)
                texto = copiar_markdown(pagina)
                if not texto or not texto.strip():
                    raise RuntimeError("o texto copiado veio vazio")
                conteudo = f"Source: {limpa}\n\n{texto.strip()}\n"
                (saida / nome).write_text(conteudo, encoding="utf-8")
                salvos.append(nome)
                print(f"    salvo: {saida / nome}")
            except Exception as erro:
                motivo = str(erro).splitlines()[0] if str(erro) else type(erro).__name__
                falhas.append((limpa, motivo))
                print(f"    falhou: {motivo}")
            time.sleep(args.pausa)

        navegador.close()

    print(f"\nSalvos: {len(salvos)} de {len(urls)}")
    if falhas:
        print("Não salvos (copie esses manualmente):")
        for url, motivo in falhas:
            print(f"  - {url}\n    motivo: {motivo}")


if __name__ == "__main__":
    main()
