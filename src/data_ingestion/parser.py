from datetime import datetime
from typing import List
from src.data_ingestion.schemas import LegalChunk
from src.data_ingestion.dgsi_scraper import scrape_dgsi_ruling
from src.data_ingestion.dre_scraper import scrape_dre_law

def parse_ruling(raw_text: str, doc_id: str, doc_date_str: str) -> List[LegalChunk]:
    processed_chunks = []
    paragraphs = raw_text.split('\n')
    current_role = "Report (Parties' Arguments)"
    
    try:
        clean_date_str = doc_date_str.replace('-', '/')
        doc_date = datetime.strptime(clean_date_str, "%d/%m/%Y").date()
    except ValueError:
        doc_date = None
        
    for paragraph in paragraphs:
        if not paragraph.strip():
            continue
            
        if "DECISÃO" in paragraph.upper() or "ACORDAM" in paragraph.upper():
            current_role = "Court's Opinion"
            continue
            
        chunk = LegalChunk(
            doc_id=doc_id,
            doc_type="Ruling",
            text=paragraph.strip(),
            rhetorical_role=current_role,
            valid_from=doc_date,
            valid_to=None
        )
        processed_chunks.append(chunk)
        
    return processed_chunks

def parse_law(raw_text: str, doc_id: str, doc_date_str: str) -> List[LegalChunk]:
    processed_chunks = []
    paragraphs = raw_text.split('\n')
    
    try:
        # A regex do scraper pode devolver YYYY-MM-DD ou DD-MM-YYYY
        if len(doc_date_str.split('-')[0]) == 4:
            doc_date = datetime.strptime(doc_date_str, "%Y-%m-%d").date()
        else:
            doc_date = datetime.strptime(doc_date_str, "%d-%m-%Y").date()
    except ValueError:
        doc_date = None
        
    for paragraph in paragraphs:
        # Ignora linhas muito curtas (ex: números isolados de artigos)
        if len(paragraph.strip()) < 15: 
            continue
            
        chunk = LegalChunk(
            doc_id=doc_id,
            doc_type="Legislation",
            text=paragraph.strip(),
            rhetorical_role="Law Body",
            valid_from=doc_date,
            valid_to=None
        )
        processed_chunks.append(chunk)
        
    return processed_chunks

if __name__ == "__main__":
    print("Testes aos módulos de parsing podem ser executados no vector_db.py")