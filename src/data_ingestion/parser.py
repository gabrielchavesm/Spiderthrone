import re
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
    """
    Parser semântico estruturado para legislação portuguesa.
    Identifica a hierarquia (Artigos, Números e Alíneas) para nunca separar 
    um preceito do seu contexto essencial.
    """
    processed_chunks = []
    
    try:
        if len(doc_date_str.split('-')[0]) == 4:
            doc_date = datetime.strptime(doc_date_str, "%Y-%m-%d").date()
        else:
            doc_date = datetime.strptime(doc_date_str, "%d-%m-%Y").date()
    except ValueError:
        doc_date = None

    # Expressão regular para detetar o início de um artigo (ex: "Artigo 562.º", "Artigo 12.º-A")
    article_pattern = re.compile(r'(Artigo\s+\d+[\.º°]?(?:-[A-Za-z])?)', re.IGNORECASE)
    
    # Divide o texto bruto com base na estrutura dos artigos
    splits = article_pattern.split(raw_text)
    
    current_article = "Disposições Gerais"
    current_text_buffer = []

    for i in range(1, len(splits), 2):
        art_title = splits[i].strip()
        art_content = splits[i+1].strip() if (i + 1) < len(splits) else ""
        
        full_article_text = f"{art_title}\n{art_content}"
        
        if len(full_article_text.strip()) > 20:
            chunk = LegalChunk(
                doc_id=doc_id,
                doc_type="Legislation",
                text=full_article_text.strip(),
                rhetorical_role="Law Article (Semantic Chunk)",
                valid_from=doc_date,
                valid_to=None
            )
            processed_chunks.append(chunk)

    # Plano de contingência caso o regex não apanhe artigos explícitos
    if not processed_chunks:
        paragraphs = raw_text.split('\n')
        for paragraph in paragraphs:
            if len(paragraph.strip()) > 30:
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
    print("Módulo de parsing semântico hierárquico pronto.")