import csv
import os

from dotenv import load_dotenv

from src.data_ingestion.dgsi_scraper import scrape_dgsi_ruling
from src.data_ingestion.dre_scraper import scrape_dre_law
from src.data_ingestion.parser import parse_law, parse_ruling
from src.data_ingestion.vector_db import index_legal_chunks, setup_qdrant_client

load_dotenv()


def run_sync_ingestion():
    csv_filename = "dataset_spiderthrone_mass.csv"
    if not os.path.exists(csv_filename):
        print(f"Erro: O ficheiro '{csv_filename}' não foi encontrado.")
        return

    print(f"A carregar os links do ficheiro '{csv_filename}'...")
    with open(csv_filename, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        documents = list(reader)

    print(f"Total de documentos detetados para ingestão: {len(documents)}")

    # Estabelece a ligação única ao Qdrant para toda a sessão
    qdrant_client = setup_qdrant_client()

    for idx, doc in enumerate(documents, 1):
        url = doc["url"]
        doc_type = doc["type"]
        print("\n--------------------------------------------------")
        print(f"[{idx}/{len(documents)}] A processar ({doc_type}): {url}")
        print("--------------------------------------------------")

        try:
            if doc_type == "DRE":
                data = scrape_dre_law(url)
                chunks = parse_law(
                    data["raw_text"],
                    data["metadata"]["source_url"],
                    data["metadata"]["date"],
                )
            elif doc_type == "DGSI":
                data = scrape_dgsi_ruling(url)
                chunks = parse_ruling(
                    data["raw_text"],
                    data["metadata"]["source_url"],
                    data["metadata"]["date"],
                )
            else:
                print(f"   [AVISO] Tipo de documento desconhecido: {doc_type}")
                continue

            if chunks:
                index_legal_chunks(qdrant_client, chunks)
                print(f"   [SUCESSO] Indexados {len(chunks)} chunks com sucesso.")
            else:
                print("   [AVISO] Nenhum chunk gerado para este documento.")

        except Exception as e:
            print(f"   [ERRO CRÍTICO] Falha ao processar o URL: {e}")

    qdrant_client.close()
    print("\n=== INGESTÃO MASSIFICA CONCLUÍDA COM SUCESSO! ===")


if __name__ == "__main__":
    run_sync_ingestion()
