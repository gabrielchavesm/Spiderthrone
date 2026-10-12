import os
from celery import Celery
from dotenv import load_dotenv
from src.data_ingestion.dgsi_scraper import scrape_dgsi_ruling
from src.data_ingestion.dre_scraper import scrape_dre_law
from src.data_ingestion.parser import parse_ruling, parse_law
from src.data_ingestion.vector_db import setup_qdrant_client, index_legal_chunks

load_dotenv()

REDIS_URL = f"redis://{os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', 6379)}/1"

app = Celery('spiderthrone_ingestion', broker=REDIS_URL)

@app.task(bind=True, max_retries=3)
def task_ingest_document(self, url: str, doc_type: str):
    """
    Tarefa assíncrona que faz scrape, parse e indexa um documento.
    O doc_type deve ser 'DRE' ou 'DGSI'.
    """
    try:
        if doc_type == 'DRE':
            data = scrape_dre_law(url)
            chunks = parse_law(data["raw_text"], data["metadata"]["source_url"], data["metadata"]["date"])
        elif doc_type == 'DGSI':
            data = scrape_dgsi_ruling(url)
            chunks = parse_ruling(data["raw_text"], data["metadata"]["source_url"], data["metadata"]["date"])
        else:
            raise ValueError("Tipo de documento inválido.")

        qdrant_client = setup_qdrant_client()
        index_legal_chunks(qdrant_client, chunks)
        qdrant_client.close()
        
        return f"Sucesso: {url} ingerido com {len(chunks)} chunks."
    
    except Exception as exc:
        # Se o site da DRE/DGSI falhar, o Celery tenta novamente mais tarde
        raise self.retry(exc=exc, countdown=60)