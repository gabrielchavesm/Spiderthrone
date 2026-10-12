import hashlib
import uuid

from fastembed import SparseTextEmbedding, TextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, SparseVectorParams, VectorParams

from src.data_ingestion.dgsi_scraper import scrape_dgsi_ruling
from src.data_ingestion.dre_scraper import scrape_dre_law
from src.data_ingestion.parser import parse_law, parse_ruling
from src.data_ingestion.schemas import LegalChunk


def setup_qdrant_client() -> QdrantClient:
    client = QdrantClient(path="./qdrant_db")
    collection_name = "spiderthrone_legal"

    if not client.collection_exists(collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config={"dense": VectorParams(size=384, distance=Distance.COSINE)},
            sparse_vectors_config={"sparse": SparseVectorParams()},
        )
        print(f"Collection híbrida '{collection_name}' criada com sucesso!")
    return client


def index_legal_chunks(client: QdrantClient, chunks: list[LegalChunk]):
    dense_model = TextEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
    sparse_model = SparseTextEmbedding(model_name="Qdrant/bm25")
    collection_name = "spiderthrone_legal"

    texts = [chunk.text for chunk in chunks]
    dense_embeddings = list(dense_model.embed(texts))
    sparse_embeddings = list(sparse_model.embed(texts))

    points = []
    for i, (chunk, dense_vec, sparse_vec) in enumerate(
        zip(chunks, dense_embeddings, sparse_embeddings)
    ):
        payload = chunk.model_dump(mode="json")
        payload["valid_from_ts"] = (
            int(chunk.valid_from.strftime("%Y%m%d")) if chunk.valid_from else 0
        )

        # GERAÇÃO DE ID DETERMINÍSTICO (UPSERT INTELIGENTE)
        # Combina o URL da lei com o índice do bloco para gerar sempre o mesmo ID.
        # Se a lei for re-ingerida, o Qdrant substitui o bloco antigo em vez de duplicar.
        seed = f"{chunk.doc_id}_chunk_{i}".encode()
        deterministic_uuid = str(uuid.UUID(hashlib.md5(seed).hexdigest()))

        point = PointStruct(
            id=deterministic_uuid,
            vector={"dense": dense_vec.tolist(), "sparse": sparse_vec.as_object()},
            payload=payload,
        )
        points.append(point)

    client.upsert(collection_name=collection_name, points=points)


if __name__ == "__main__":
    url_dgsi = "https://www.dgsi.pt/jstj.nsf/954f0ce6ad9dd8b980256b5f003fa814/4a10f461894a769680258137004d63e9?OpenDocument"
    url_dre = "https://diariodarepublica.pt/dr/detalhe/decreto-lei/269-1998-566629"

    print("1. Scraping data from DGSI and DRE...")
    data_dgsi = scrape_dgsi_ruling(url_dgsi)
    data_dre = scrape_dre_law(url_dre)

    print("2. Parsing and validating...")
    chunks_dgsi = parse_ruling(
        data_dgsi["raw_text"],
        data_dgsi["metadata"]["source_url"],
        data_dgsi["metadata"]["date"],
    )
    chunks_dre = parse_law(
        data_dre["raw_text"],
        data_dre["metadata"]["source_url"],
        data_dre["metadata"]["date"],
    )

    all_chunks = chunks_dgsi + chunks_dre

    print("3. Connecting to Qdrant...")
    qdrant_client = setup_qdrant_client()

    print(f"4. Indexing {len(all_chunks)} combined chunks...")
    index_legal_chunks(qdrant_client, all_chunks)

    qdrant_client.close()
