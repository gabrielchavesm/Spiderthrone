import os
import re
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, Range, MatchValue, MatchText
from fastembed import TextEmbedding
from llm_failover import get_llm_response

# Carrega as variáveis do ficheiro .env para a memória de forma segura
load_dotenv()

def retrieve_context(query_text: str, target_date: str) -> str:
    client = QdrantClient(path="./qdrant_db")
    model = TextEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    query_vector = list(model.embed([query_text]))[0].tolist()
    target_date_ts = int(target_date.replace("-", ""))

    # Filtro cruzado base: Domínio de Direito do Trabalho + Validação Temporal
    temporal_and_domain_filter = Filter(
        must=[
            FieldCondition(
                key="domain",
                match=MatchValue(value="direito_trabalho")
            ),
            FieldCondition(
                key="valid_from_ts",
                range=Range(lte=target_date_ts)
            )
        ]
    )

    # 1. Pesquisa Vetorial Principal (Semântica) - Limitada a 12 para poupar tokens
    vector_response = client.query_points(
        collection_name="spiderthrone_legal",
        query=query_vector,
        query_filter=temporal_and_domain_filter,
        limit=12
    )
    
    # 2. Pesquisa Híbrida / Lexical: Detetar menções a números de artigos na pergunta (ex: "artigo 29", "artigo 12")
    keyword_hits = []
    query_lower = query_text.lower()
    article_match = re.search(r'artigo\s*(\d+)(?:\.?[º°])?(?:-([a-zA-Z]))?', query_lower)
    
    if article_match:
        art_num = article_match.group(1)
        # Tenta encontrar o artigo exato na base de dados através do payload
        try:
            scroll_res, _ = client.scroll(
                collection_name="spiderthrone_legal",
                scroll_filter=Filter(
                    must=[
                        FieldCondition(key="domain", match=MatchValue(value="direito_trabalho")),
                        FieldCondition(key="article", match=MatchText(text=art_num))
                    ]
                ),
                limit=3
            )
            keyword_hits.extend(scroll_res)
        except Exception:
            pass

    # 3. Combinar resultados eliminando duplicados (prioridade aos resultados lexicals/artigos exatos)
    seen_ids = set()
    combined_points = []
    
    for hit in keyword_hits:
        if hit.id not in seen_ids:
            seen_ids.add(hit.id)
            combined_points.append(hit)
            
    for hit in vector_response.points:
        if hit.id not in seen_ids:
            seen_ids.add(hit.id)
            combined_points.append(hit)
            
    # Garantir estritamente o limite máximo de 15 blocos (evita o erro 413 na Groq)
    final_hits = combined_points[:15]
    
    context_blocks = []
    for hit in final_hits:
        payload = hit.payload
        article_ref = payload.get('article', 'Artigo')
        role = payload.get('rhetorical_role', 'NORMA')
        text = payload.get('page_content', '')
        
        context_blocks.append(f"[{article_ref} | Função Retórica: {role}]\n{text}")
        
    client.close()
    
    return "\n\n---\n\n".join(context_blocks)

def generate_legal_answer(question: str, target_date: str):
    print("1. Recuperando legislação laboral (Pesquisa Híbrida)...")
    context = retrieve_context(question, target_date)
    
    if not context.strip():
        return "Não encontrei informação legal anterior a esta data para responder à sua questão."
        
    system_prompt = """
    És um assistente jurídico português altamente rigoroso especializado em Direito do Trabalho.
    A tua única função é responder à PERGUNTA DO ADVOGADO baseando-te EXCLUSIVAMENTE no CONTEXTO FORNECIDO (Código do Trabalho).
    
    REGRAS OBRIGATÓRIAS:
    1. Se o contexto não contiver a resposta, deves dizer APENAS: "Não encontrei informação suficiente na legislação e jurisprudência fornecidas para responder a esta questão." Não inventes.
    2. Cita sempre o artigo correspondente do Código do Trabalho.
    3. Nunca confundas os argumentos das partes (Report) com a decisão ou norma (Court's Opinion / Norma).
    """
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"CONTEXTO FORNECIDO:\n{context}\n\nPERGUNTA DO ADVOGADO: {question}"}
    ]

    print("2. Analisando o contexto com o LLM...\n")
    
    try:
        mensagem_ia = get_llm_response(messages=messages, temperature=0.0)
        return mensagem_ia.content
    except Exception as e:
        return str(e)

if __name__ == "__main__":
    # Teste prático de Direito do Trabalho no terminal
    pergunta = "O que diz o Código do Trabalho sobre a noção de contrato de trabalho?"
    data_do_caso = "2026-10-11"
    
    resposta = generate_legal_answer(pergunta, data_do_caso)
    
    print("\n" + "="*70)
    print("RESPOSTA DO ASSISTENTE JURÍDICO (DIREITO DO TRABALHO):")
    print("="*70)
    print(resposta)