import os
from openai import OpenAI

def get_llm_response(messages: list, tools: list = None, tool_choice: str = None, temperature: float = 0.0):
    llm_providers = [
        {
            "name": "Groq (Qwen 3.8 27B)",
            "api_key": os.getenv("GROQ_API_KEY"),
            "base_url": "https://api.groq.com/openai/v1",
            "model": "qwen/qwen3.8-27b"
        },
        {
            "name": "Groq (GPT-OSS 20B)",
            "api_key": os.getenv("GROQ_API_KEY"),
            "base_url": "https://api.groq.com/openai/v1",
            "model": "openai/gpt-oss-20b"
        },
        {
            "name": "Google Gemini (3.8 Flash)",
            "api_key": os.getenv("GEMINI_API_KEY"),
            "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
            "model": "models/gemini-3.8-flash"
        }
    ]

    for provider in llm_providers:
        if not provider["api_key"]:
            continue
            
        print(f"-> A tentar conectar a: {provider['name']}...")
        
        try:
            client = OpenAI(
                api_key=provider["api_key"],
                base_url=provider["base_url"]
            )
            
            kwargs = {
                "model": provider["model"],
                "temperature": temperature,
                "messages": messages
            }
            
            if tools:
                kwargs["tools"] = tools
                if tool_choice:
                    kwargs["tool_choice"] = tool_choice

            response = client.chat.completions.create(**kwargs)
            return response.choices[0].message
            
        except Exception as e:
            print(f"   [AVISO] Falha no {provider['name']}: {str(e)[:100]}...")

    raise Exception("ERRO CRÍTICO: Todos os modelos falharam ou não existem chaves de API configuradas no ficheiro .env.")