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

def parse_pdf_codigo_trabalho(pdf_path: str):
    reader = pypdf.PdfReader(pdf_path)
    full_text = ""
    for page in reader.pages:
        text = page.extract_text()
        if text:
            full_text += text + "\n"
            
    # Expressão regular melhorada para detetar todos os artigos no PDF oficial
    pattern = r"(Artigo\s+\d+(?:\.?[º°])?(?:-[A-Za-z]+)?[^\n]*)"
    splits = re.split(pattern, full_text)
    
    chunks = []
    for i in range(1, len(splits), 2):
        article_title = splits[i].strip()
        article_body = splits[i+1].strip() if i+1 < len(splits) else ""
        
        if len(article_body) < 5:
            continue
            
        chunks.append({
            "article": article_title,
            "page_content": f"{article_title}\n{article_body}",
            "domain": "direito_trabalho",
            "valid_from_ts": 20090217,
            "rhetorical_role": "NORMA"
        })
        
    return chunks

pdf_file = "codigo_trabalho.pdf"
if os.path.exists(pdf_file):
    print(f"A ler e processar diretamente o PDF oficial {pdf_file}...")
    articles = parse_pdf_codigo_trabalho(pdf_file)
    print(f"Encontrados {len(articles)} artigos no PDF. A vetorizar e injetar no Qdrant...")
    
    points = []
    for idx, item in enumerate(articles):
        vector = encoder.encode(item["page_content"]).tolist()
        points.append(
            models.PointStruct(
                id=idx + 20000, # ID único atualizado
                vector=vector,
                payload=item
            )
        )
    
    client.upsert(
        collection_name=collection_name,
        points=points
    )
    print(f"Sucesso absoluto! {len(points)} artigos extraídos do PDF foram indexados no Qdrant.")
else:
    print(f"Erro: O ficheiro {pdf_file} não foi encontrado na pasta.")