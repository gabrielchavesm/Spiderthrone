import os
import json
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from src.rag_pipeline import retrieve_context
from src.llm_failover import get_llm_response
from src.redis_memory import get_session_history, save_session_history

load_dotenv()

app = FastAPI(title="Spiderthrone AG-UI API with Redis")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    question: str
    session_id: str

ferramentas_ui = [
    {
        "type": "function",
        "function": {
            "name": "mostrar_documento_legal",
            "description": "Usa esta ferramenta APENAS quando o utilizador pedir para ver a lei original, ler o acórdão, ou analisar o documento de base.",
            "parameters": {
                "type": "object",
                "properties": {
                    "titulo": {"type": "string", "description": "Ex: Decreto-Lei n.º 269/98 ou Acórdão do STJ"},
                    "data": {"type": "string", "description": "Data de validade do documento"},
                    "conteudo": {"type": "string", "description": "O excerto do texto legal em si"}
                },
                "required": ["titulo", "data", "conteudo"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mostrar_tabela_valores",
            "description": "Usa esta ferramenta APENAS quando o utilizador perguntar sobre valores, taxas de justiça, honorários ou montantes monetários.",
            "parameters": {
                "type": "object",
                "properties": {
                    "itens": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "descricao": {"type": "string", "description": "O que está a ser pago. Ex: Taxa de Injunção"},
                                "valor": {"type": "number", "description": "O valor em euros"}
                            }
                        }
                    }
                },
                "required": ["itens"]
            }
        }
    }
]

@app.post("/ag-ui-chat")
async def chat_endpoint(req: ChatRequest):
    if not req.session_id:
        raise HTTPException(status_code=400, detail="session_id é obrigatório para gerir a memória.")

    # 1. Carrega o histórico completo do Redis
    history = get_session_history(req.session_id)

    # 2. Recupera o contexto vetorial baseado na pergunta atual
    context = retrieve_context(req.question, target_date="2026-10-11") 
    
    system_prompt = """
    És o Spiderthrone, um assistente jurídico português avançado especializado em Direito do Trabalho com interface gerativa.
    Baseia-te EXCLUSIVAMENTE no contexto fornecido e lembra-te do histórico recente da conversa para manter a continuidade.
    """

    messages = [{"role": "system", "content": system_prompt}]
    
    # JANELA DESLIZANTE: Envia apenas as últimas 6 mensagens (3 interações) para evitar erros 413/429
    recent_history = history[-6:]
    for msg in recent_history:
        role = "assistant" if msg["role"] in ["ai", "assistant"] else "user"
        messages.append({"role": role, "content": msg["text"]})

    user_content = f"CONTEXTO DO QDRANT:\n{context}\n\nPERGUNTA DO ADVOGADO: {req.question}" if context.strip() else f"PERGUNTA DO ADVOGADO: {req.question}"
    messages.append({"role": "user", "content": user_content})

    try:
        mensagem_ia = get_llm_response(
            messages=messages, 
            tools=ferramentas_ui, 
            tool_choice="auto", 
            temperature=0.0
        )
        
        ai_response_text = ""
        widget_data = None

        if mensagem_ia.tool_calls:
            tool_call = mensagem_ia.tool_calls[0]
            widget_data = {
                "widget": tool_call.function.name,
                "widgetArgs": json.loads(tool_call.function.arguments)
            }
            ai_response_text = "Com base na legislação, aqui está o que pediu:"
        else:
            ai_response_text = mensagem_ia.content

        # Guarda no Redis
        history.append({"role": "user", "text": req.question})
        history.append({"role": "assistant", "text": ai_response_text})
        save_session_history(req.session_id, history)

        response_payload = {
            "role": "ai",
            "text": ai_response_text
        }
        if widget_data:
            response_payload.update(widget_data)

        return response_payload

    except Exception as e:
        return {"role": "ai", "text": f"Erro interno do servidor IA: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)