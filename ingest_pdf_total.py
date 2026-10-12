import os
import re
import pypdf
from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer

DB_PATH = "./qdrant_db"
client = QdrantClient(path=DB_PATH)
collection_name = "spiderthrone_legal"

print("A carregar o modelo de embeddings...")
encoder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# Garantir coleção
collections = [c.name for c in client.get_collections().collections]
if collection_name not in collections:
    client.create_collection(
        collection_name=collection_name,
        vectors_config=models.VectorParams(
            size=encoder.get_embedding_dimension(),
            distance=models.Distance.COSINE
        )
    )

def parse_pdf_articles(pdf_path: str, domain: str, start_id: int):
    print(f"A ler e processar o PDF oficial: {pdf_path}...")
    if not os.path.exists(pdf_path):
        print(f"Aviso: O ficheiro {pdf_path} não foi encontrado.")
        return []

    reader = pypdf.PdfReader(pdf_path)
    full_text = ""
    for page in reader.pages:
        text = page.extract_text()
        if text:
            full_text += text + "\n"
            
    # Expressão regular para detetar artigos
    pattern = r"(Artigo\s+\d+(?:\.?[º°])?(?:-[A-Za-z]+)?[^\n]*)"
    splits = re.split(pattern, full_text)
    
    chunks = []
    current_id = start_id
    for i in range(1, len(splits), 2):
        article_title = splits[i].strip()
        article_body = splits[i+1].strip() if i+1 < len(splits) else ""
        
        if len(article_body) < 5:
            continue
            
        vector = encoder.encode(f"{article_title}\n{article_body}").tolist()
        
        chunks.append(
            models.PointStruct(
                id=current_id,
                vector=vector,
                payload={
                    "article": article_title,
                    "page_content": f"{article_title}\n{article_body}",
                    "domain": domain,
                    "valid_from_ts": 20090217,
                    "rhetorical_role": "NORMA"
                }
            )
        )
        current_id += 1
        
    print(f"-> {len(chunks)} artigos extraídos de {pdf_path}.")
    return chunks

# Definir os ficheiros a processar e os respetivos domínios e IDs iniciais
targets = [
    {"file": "codigo_trabalho.pdf", "domain": "direito_trabalho", "start_id": 10000},
    {"file": "codigo_civil.pdf", "domain": "direito_civil", "start_id": 30000},
    {"file": "codigo_processo_civil.pdf", "domain": "direito_processo_civil", "start_id": 50000},
]

all_points = []
for target in targets:
    points = parse_pdf_articles(target["file"], target["domain"], target["start_id"])
    all_points.extend(points)

if all_points:
    print(f"A injetar um total de {len(all_points)} artigos no Qdrant...")
    client.upsert(
        collection_name=collection_name,
        points=all_points
    )
    print("Sucesso absoluto! Todos os Códigos Core foram indexados no Qdrant.")
else:
    print("Nenhum artigo foi indexado. Verifique se os PDFs estão na pasta correta.")