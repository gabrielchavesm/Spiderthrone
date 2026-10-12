import os
import numpy as np
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, Range, Prefetch, FusionQuery, Fusion
from fastembed import TextEmbedding, SparseTextEmbedding
from src.llm_failover import get_llm_response

load_dotenv()

def validate_query_intent(question: str) -> bool:
    try:
        model = TextEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
        
        escopo_permitido = [
            "artigo do código civil",
            "processo civil e prazos judiciais",
            "direito do trabalho e contrato laboral",
            "obrigação de indemnização e responsabilidade civil",
            "direitos e obrigações patrimoniais",
            "injunção e obrigações pecuniárias",
            "acórdão e jurisprudência"
        ]
        
        query_vector = list(model.embed([question]))[0]
        anchor_vectors = list(model.embed(escopo_permitido))
        
        similaridades = [
            np.dot(query_vector, anchor) / (np.linalg.norm(query_vector) * np.linalg.norm(anchor))
            for anchor in anchor_vectors
        ]
        
        max_similarity = max(similaridades)
        print(f"   [NLP GUARD] Índice de aderência ao escopo jurídico: {max_similarity:.2f}")
        
        if max_similarity < 0.35:
            return False
            
        return True
    except Exception:
        return True

def retrieve_context(query_text: str, target_date: str) -> str:
    client = QdrantClient(path="./qdrant_db")
    dense_model = TextEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
    sparse_model = SparseTextEmbedding(model_name="Qdrant/bm25")
    
    query_dense_vector = list(dense_model.embed([query_text]))[0].tolist()
    query_sparse_vector = list(sparse_model.embed([query_text]))[0].as_object()
    
    target_date_ts = int(target_date.replace("-", ""))

    # Apenas filtro temporal - deixamos a precisão do tema para a pesquisa semântica/híbrida
    must_conditions = [
        FieldCondition(key="valid_from_ts", range=Range(lte=target_date_ts))
    ]
    
    hybrid_filter = Filter(must=must_conditions)

    response = client.query_points(
        collection_name="spiderthrone_legal",
        prefetch=[
            Prefetch(
                query=query_dense_vector,
                using="dense",
                filter=hybrid_filter,
                limit=8
            ),
            Prefetch(
                query=query_sparse_vector,
                using="sparse",
                filter=hybrid_filter,
                limit=8
            ),
        ],
        query=FusionQuery(fusion=Fusion.RRF),
        limit=8
    )
    
    results = response.points
    
    context_blocks = []
    for hit in results:
        payload = hit.payload
        # CORREÇÃO CRÍTICA: Mapeamento exato das chaves do schemas.py
        doc_id = payload.get('doc_id', 'Documento Oficial')
        role = payload.get('rhetorical_role', 'NORMA')
        text = payload.get('text', '') 
        
        # Só adiciona se efetivamente existir texto
        if text.strip():
            context_blocks.append(f"[{doc_id} | Função: {role}]\n{text}")
        
    client.close()
    
    return "\n\n---\n\n".join(context_blocks)

def generate_legal_answer(question: str, target_date: str):
    print("1. Validando intenção e escopo por NLP (Semantic Guard)...")
    if not validate_query_intent(question):
        print("   [NLP GUARD] Pergunta rejeitada por irrelevância semântica ao escopo jurídico indexado.")
        return "Não encontrei informação suficiente na legislação indexada para responder a esta questão."

    print("2. Recuperando legislação (Pesquisa Híbrida Nativa com Qdrant RRF)...")
    context = retrieve_context(question, target_date)
    
    if not context.strip():
        return "Não encontrei informação suficiente na legislação indexada para responder a esta questão."
        
    query_lower = question.lower()
    
    temas_proibidos = [
        "penal", "crime", "prisão", "pena", "liberdade condicional",
        "sociedades", "quotas", "csc", "estatutos de uma sociedade",
        "benefícios fiscais", "ebf", "imi", "imposto", "irc", "iva",
        "procedimento administrativo", "cpa"
        # NOTA: Retirei "requerimento" dos proibidos porque é muito usado em injunções
    ]
    
    for termo in temas_proibidos:
        if termo in query_lower:
            print(f"   [HARD GUARD] Termo restrito detetado ('{termo}').")
            return "A pergunta refere-se a matéria excluída ou não suportada nesta versão do sistema."

    print("3. Contexto validado com sucesso. A redigir resposta (LLM)...")
    
    messages = [
        {"role": "system", "content": "És um assistente jurídico estrito ao contexto. Responde detalhadamente em Markdown baseando-te APENAS no texto fornecido."},
        {"role": "user", "content": f"CONTEXTO FORNECIDO:\n{context}\n\nPERGUNTA: {question}"}
    ]
    
    try:
        mensagem_ia = get_llm_response(messages=messages, temperature=0.0)
        return mensagem_ia.content.strip()
    except Exception as e:
        return str(e)