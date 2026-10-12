import json
import os

from src.data_ingestion.dre_scraper import scrape_dre_law
from src.data_ingestion.parser import parse_law
from src.data_ingestion.vector_db import index_legal_chunks, setup_qdrant_client

# Manifesto dos códigos monitorizados de relevância estrutural
LEGAL_MONITOR_TARGETS = [
    {
        "nome": "Codigo_Civil",
        "url": "https://diariodarepublica.pt/dr/detalhe/decreto-lei/47344-1966-473130",  # Exemplo de link oficial
        "tipo": "DRE",
    },
    {
        "nome": "Codigo_Trabalho",
        "url": "https://diariodarepublica.pt/dr/detalhe/lei/7-2009-547342",
        "tipo": "DRE",
    },
]

REGISTRY_FILE = "legal_registry.json"


def carregar_registo():
    if os.path.exists(REGISTRY_FILE):
        with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def guardar_registo(registo):
    with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
        json.dump(registo, f, indent=4, ensure_ascii=False)


def verificar_e_atualizar_corpus():
    print("=== A VERIFICAR ALTERAÇÕES NOS CÓDIGOS DE BASE (CIVIL, TRABALHO, ETC.) ===")
    registo_atual = carregar_registo()
    qdrant_client = setup_qdrant_client()

    atualizacoes_feitas = False

    for alvo in LEGAL_MONITOR_TARGETS:
        nome = alvo["nome"]
        url = alvo["url"]
        print(f"\nA verificar estado de: {nome}...")

        try:
            # Executa o scraper do DRE (igual ao que usou na ingestão massiva)
            dados_recolhidos = scrape_dre_law(url)
            novo_titulo = dados_recolhidos["metadata"]["law_title"]
            texto_bruto = dados_recolhidos["raw_text"]

            # Cria uma assinatura simples baseada no tamanho do texto ou data do documento
            assinatura_atual = (
                f"{len(texto_bruto)}_{dados_recolhidos['metadata']['date']}"
            )

            if registo_atual.get(nome) != assinatura_atual:
                print(
                    f"   [ALTERAÇÃO DETETADA] O diploma '{nome}' foi atualizado ou revisto oficialmente!"
                )

                # Faz o parse semântico estruturado dos artigos atualizados
                chunks = parse_law(
                    texto_bruto, url, dados_recolhidos["metadata"]["date"]
                )

                if chunks:
                    # Ingestão automática/upsert inteligente no Qdrant da pipeline
                    index_legal_chunks(qdrant_client, chunks)
                    print(
                        f"   [SUCESSO] Reindexados {len(chunks)} chunks atualizados para {nome}."
                    )

                # Atualiza o registo de controlo
                registo_atual[nome] = assinatura_atual
                atualizacoes_feitas = True
            else:
                print(f"   [ESTÁVEL] Nenhuma alteração detetada em {nome}.")

        except Exception as e:
            print(f"   [ERRO] Falha ao verificar o código {nome}: {e}")

    qdrant_client.close()

    if atualizacoes_feitas:
        guardar_registo(registo_atual)
        print("\n=== REGISTO LEGISLATIVO ATUALIZADO COM SUCESSO ===")
    else:
        print("\n=== CORPUS JURÍDICO TOTALMENTE ATUALIZADO (SEM MUDANÇAS) ===")


if __name__ == "__main__":
    verificar_e_atualizar_corpus()
