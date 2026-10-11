import os
from dotenv import load_dotenv
from openai import OpenAI

def list_available_models():
    load_dotenv()
    
    print("=== A VERIFICAR MODELOS DA GROQ ===")
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        try:
            client_groq = OpenAI(api_key=groq_key, base_url="https://api.groq.com/openai/v1")
            models = client_groq.models.list()
            for m in models.data:
                print(f"- {m.id}")
        except Exception as e:
            print(f"Erro ao contactar a Groq: {e}")
    else:
        print("Chave GROQ_API_KEY não encontrada no .env")

    print("\n=== A VERIFICAR MODELOS DO GEMINI ===")
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        try:
            client_gemini = OpenAI(api_key=gemini_key, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
            models = client_gemini.models.list()
            for m in models.data:
                print(f"- {m.id}")
        except Exception as e:
            print(f"Erro ao contactar o Gemini: {e}")
    else:
        print("Chave GEMINI_API_KEY não encontrada no .env")

if __name__ == "__main__":
    list_available_models()