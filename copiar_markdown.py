#!/usr/bin/env python3
"""
Para cada URL do docs.github.com da lista: baixa o corpo do artigo em markdown
pelo endpoint https://docs.github.com/api/article/body e salva em um arquivo .md.

URLs de outros sites (github.com, developer.hashicorp.com) são puladas.

Uso:
    python copiar_markdown.py urls.txt --out markdown
"""

import argparse
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

ENDPOINT = "https://docs.github.com/api/article/body?pathname="
HOST_PERMITIDO = "docs.github.com"


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


def baixar_corpo(url):
    caminho = urlparse(url_limpa(url)).path  # ex.: /en/enterprise-cloud@latest/admin/...
    alvo = ENDPOINT + urllib.parse.quote(caminho, safe="/@")
    requisicao = urllib.request.Request(alvo, headers={"User-Agent": "docs-markdown-script/1.0"})
    with urllib.request.urlopen(requisicao, timeout=60) as resposta:
        return resposta.read().decode("utf-8")


def main():
    ap = argparse.ArgumentParser(description="Salva o markdown de cada página do docs.github.com")
    ap.add_argument("lista", help="arquivo .txt com uma URL por linha")
    ap.add_argument("--out", default="markdown", help="pasta de saída (padrão: markdown)")
    ap.add_argument("--pausa", type=float, default=0.5, help="segundos entre páginas (padrão: 0.5)")
    args = ap.parse_args()

    urls = ler_urls(args.lista)
    saida = Path(args.out)
    saida.mkdir(parents=True, exist_ok=True)

    usados = set()
    salvos = []
    falhas = []

    for i, url in enumerate(urls, 1):
        limpa = url_limpa(url)
        print(f"[{i}/{len(urls)}] {limpa}")

        if urlparse(limpa).netloc != HOST_PERMITIDO:
            falhas.append((limpa, "não é docs.github.com; copie manualmente"))
            print("    pulada: não é docs.github.com")
            continue

        nome = nome_arquivo(url, usados)
        try:
            texto = baixar_corpo(limpa)
            if not texto.strip():
                raise RuntimeError("o corpo veio vazio")
            conteudo = f"Source: {limpa}\n\n{texto.strip()}\n"
            (saida / nome).write_text(conteudo, encoding="utf-8")
            salvos.append(nome)
            print(f"    salvo: {saida / nome}")
        except urllib.error.HTTPError as erro:
            falhas.append((limpa, f"HTTP {erro.code}"))
            print(f"    falhou: HTTP {erro.code}")
        except Exception as erro:
            motivo = str(erro).splitlines()[0] if str(erro) else type(erro).__name__
            falhas.append((limpa, motivo))
            print(f"    falhou: {motivo}")

        time.sleep(args.pausa)

    print(f"\nSalvos: {len(salvos)} de {len(urls)}")
    if falhas:
        print("Não salvos:")
        for url, motivo in falhas:
            print(f"  - {url}\n    motivo: {motivo}")

    # Só falha o job se nada foi salvo. Com resultados parciais, o commit ainda acontece.
    sys.exit(0 if salvos else 1)


if __name__ == "__main__":
    main()
