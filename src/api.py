import os
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from src.rag_pipeline import retrieve_context
from src.llm_failover import get_llm_response

load_dotenv()

# 1. Configuração do Servidor Web
app = FastAPI(title="Spiderthrone AG-UI API")

# Permite que o frontend React comunique com o backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    question: str

# 2. Definição das Tools (Widgets)
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

# 3. Endpoint Principal
@app.post("/ag-ui-chat")
async def chat_endpoint(req: ChatRequest):
    context = retrieve_context(req.question, target_date="2026-10-11") 
    
    if not context.strip():
        return {"role": "ai", "text": "Não encontrei informação legal suficiente na base de dados para responder a esta questão."}

    system_prompt = """
    És o Spiderthrone, um assistente jurídico português avançado com interface gerativa.
    Baseia-te EXCLUSIVAMENTE no contexto fornecido.
    
    REGRAS DE INTERFACE:
    - Se a pergunta for genérica, responde com texto normal, citando as fontes.
    - Se o utilizador quiser ver a lei/acórdão, CHAMA A FERRAMENTA 'mostrar_documento_legal'.
    - Se a pergunta for sobre valores monetários ou taxas, CHAMA A FERRAMENTA 'mostrar_tabela_valores'.
    """

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"CONTEXTO DO QDRANT:\n{context}\n\nPERGUNTA DO ADVOGADO: {req.question}"}
    ]

    try:
        # Passa as ferramentas (Widgets) para o Router. Ele lida com as tentativas e quedas.
        mensagem_ia = get_llm_response(
            messages=messages, 
            tools=ferramentas_ui, 
            tool_choice="auto", 
            temperature=0.0
        )
        
        if mensagem_ia.tool_calls:
            tool_call = mensagem_ia.tool_calls[0]
            nome_do_widget = tool_call.function.name
            argumentos = json.loads(tool_call.function.arguments)
            
            return {
                "role": "ai",
                "text": "Com base na jurisprudência, aqui está o que pediu:",
                "widget": nome_do_widget,
                "widgetArgs": argumentos
            }
            
        return {
            "role": "ai",
            "text": mensagem_ia.content
        }

    except Exception as e:
        return {"role": "ai", "text": f"Erro interno do servidor IA: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    # Arranca o servidor na porta 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)