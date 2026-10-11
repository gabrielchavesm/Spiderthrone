import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, Range
from fastembed import TextEmbedding
from src.llm_failover import get_llm_response

# Carrega as variáveis do ficheiro .env para a memória de forma segura
load_dotenv()

def retrieve_context(query_text: str, target_date: str) -> str:
    client = QdrantClient(path="./qdrant_db")
    model = TextEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    query_vector = list(model.embed([query_text]))[0].tolist()
    target_date_ts = int(target_date.replace("-", ""))

    temporal_filter = Filter(
        must=[
            FieldCondition(
                key="valid_from_ts",
                range=Range(lte=target_date_ts)
            )
        ]
    )

    response = client.query_points(
        collection_name="legal_documents",
        query=query_vector,
        query_filter=temporal_filter,
        limit=5
    )
    
    context_blocks = []
    for hit in response.points:
        source_type = hit.payload.get('doc_type', 'Documento')
        role = hit.payload.get('rhetorical_role', 'N/A')
        date = hit.payload.get('valid_from', 'N/A')
        text = hit.payload.get('text', '')
        
        context_blocks.append(f"[{source_type} | Função: {role} | Data: {date}]\n{text}")
        
    client.close()
    
    return "\n\n---\n\n".join(context_blocks)

def generate_legal_answer(question: str, target_date: str):
    print("1. Recuperando jurisprudência e legislação da base de dados...")
    context = retrieve_context(question, target_date)
    
    if not context.strip():
        return "Não encontrei informação legal anterior a esta data para responder à sua questão."
        
    system_prompt = """
    És um assistente jurídico português altamente rigoroso.
    A tua única função é responder à PERGUNTA DO ADVOGADO baseando-te EXCLUSIVAMENTE no CONTEXTO FORNECIDO (que contém Leis e Acórdãos).
    
    REGRAS OBRIGATÓRIAS:
    1. Se o contexto não contiver a resposta, deves dizer APENAS: "Não encontrei informação suficiente na legislação e jurisprudência fornecidas para responder a esta questão." Não inventes.
    2. Cita sempre se a informação vem da legislação ou do tribunal.
    3. Nunca confundas os argumentos das partes (Report) com a decisão (Court's Opinion).
    """
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"CONTEXTO FORNECIDO:\n{context}\n\nPERGUNTA DO ADVOGADO: {question}"}
    ]

    print("2. Analisando o contexto com o LLM...\n")
    
    try:
        # Chama o nosso novo Router que faz o failover automático
        mensagem_ia = get_llm_response(messages=messages, temperature=0.0)
        return mensagem_ia.content
    except Exception as e:
        return str(e)

if __name__ == "__main__":
    # Teste de barreira de alucinação no terminal
    pergunta = "Qual é a pena de prisão para o crime de burla informática segundo a lei portuguesa?"
    data_do_caso = "2026-10-11"
    
    resposta = generate_legal_answer(pergunta, data_do_caso)
    
    print("\n" + "="*70)
    print("RESPOSTA DO ASSISTENTE JURÍDICO:")
    print("="*70)
    print(resposta)