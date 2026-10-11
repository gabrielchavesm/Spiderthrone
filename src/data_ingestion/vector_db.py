from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from fastembed import TextEmbedding
from src.data_ingestion.schemas import LegalChunk
from src.data_ingestion.dgsi_scraper import scrape_dgsi_ruling
from src.data_ingestion.dre_scraper import scrape_dre_law
from src.data_ingestion.parser import parse_ruling, parse_law

def setup_qdrant_client() -> QdrantClient:
    client = QdrantClient(path="./qdrant_db")
    collection_name = "legal_documents"

    if not client.collection_exists(collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE)
        )
        print(f"Collection '{collection_name}' created successfully!")
    return client

def index_legal_chunks(client: QdrantClient, chunks: list[LegalChunk]):
    print("Loading lightweight ONNX embedding model...")
    model = TextEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
    collection_name = "legal_documents"

    print("Converting text to vectors...")
    texts = [chunk.text for chunk in chunks]
    embeddings = list(model.embed(texts))
    
    points = []
    for i, (chunk, vector) in enumerate(zip(chunks, embeddings)):
        payload = chunk.model_dump(mode='json')
        
        if chunk.valid_from:
            payload['valid_from_ts'] = int(chunk.valid_from.strftime("%Y%m%d"))
        else:
            payload['valid_from_ts'] = 0

        point = PointStruct(
            id=i,
            vector=vector.tolist(),
            payload=payload
        )
        points.append(point)

    client.upsert(
        collection_name=collection_name,
        points=points
    )
    print(f"Successfully indexed {len(points)} chunks into Qdrant!")

if __name__ == "__main__":
    url_dgsi = "https://www.dgsi.pt/jstj.nsf/954f0ce6ad9dd8b980256b5f003fa814/4a10f461894a769680258137004d63e9?OpenDocument"
    url_dre = "https://diariodarepublica.pt/dr/detalhe/decreto-lei/269-1998-566629"

    print("1. Scraping data from DGSI and DRE...")
    data_dgsi = scrape_dgsi_ruling(url_dgsi)
    data_dre = scrape_dre_law(url_dre)

    print("2. Parsing and validating...")
    chunks_dgsi = parse_ruling(data_dgsi["raw_text"], data_dgsi["metadata"]["source_url"], data_dgsi["metadata"]["date"])
    chunks_dre = parse_law(data_dre["raw_text"], data_dre["metadata"]["source_url"], data_dre["metadata"]["date"])
    
    # Junta as duas listas de blocos numa única lista mestre
    all_chunks = chunks_dgsi + chunks_dre

    print("3. Connecting to Qdrant...")
    qdrant_client = setup_qdrant_client()

    print(f"4. Indexing {len(all_chunks)} combined chunks...")
    index_legal_chunks(qdrant_client, all_chunks)
    
    qdrant_client.close()