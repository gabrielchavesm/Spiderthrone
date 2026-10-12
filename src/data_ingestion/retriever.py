from fastembed import TextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, Range


def search_legal_documents(query_text: str, target_date: str):
    client = QdrantClient(path="./qdrant_db")
    model = TextEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")

    query_vector = list(model.embed([query_text]))[0].tolist()

    target_date_ts = int(target_date.replace("-", ""))

    temporal_filter = Filter(
        must=[FieldCondition(key="valid_from_ts", range=Range(lte=target_date_ts))]
    )

    # Nova API do Qdrant: query_points em vez de search
    response = client.query_points(
        collection_name="legal_documents",
        query=query_vector,
        query_filter=temporal_filter,
        limit=3,
    )

    # Extrai a lista de resultados da resposta
    results = response.points

    print(f"\n--- Search: '{query_text}' | Time Context: {target_date} ---")

    if not results:
        print("No relevant documents found.")

    for hit in results:
        print(f"\n[Score: {hit.score:.4f} | Date: {hit.payload.get('valid_from')}]")
        print(f"Role: {hit.payload.get('rhetorical_role')}")
        print(f"Text: {hit.payload.get('text')[:150]}...")

    client.close()


if __name__ == "__main__":
    question = "O que acontece à compensação de créditos e à reconvenção num procedimento de injunção?"

    print(">>> SCENARIO A: Searching in 2018")
    search_legal_documents(question, "2018-01-01")

    print("\n>>> SCENARIO B: Searching in 2016")
    search_legal_documents(question, "2016-01-01")
