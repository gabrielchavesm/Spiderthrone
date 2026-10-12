import logging
import os
import time

from langfuse import get_client
from langfuse.openai import OpenAI

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("Spiderthrone-Langfuse")


def get_llm_response(
    messages: list,
    tools: list = None,
    tool_choice: str = None,
    temperature: float = 0.0,
):
    # Inicializa o cliente do Langfuse para garantir a ligação autenticada
    langfuse = get_client()

    llm_providers = [
        {
            "name": "Groq Principal (Qwen 3.8 27B)",
            "api_key": os.getenv("GROQ_API_KEY"),
            "base_url": "https://api.groq.com/openai/v1",
            "model": "qwen/qwen3.8-27b",
        },
        {
            "name": "Groq Secundário (Qwen 3.8 27B)",
            "api_key": os.getenv("SECOND_GROQ_API_KEY"),
            "base_url": "https://api.groq.com/openai/v1",
            "model": "qwen/qwen3.8-27b",
        },
        {
            "name": "Groq Principal (GPT-OSS 20B)",
            "api_key": os.getenv("GROQ_API_KEY"),
            "base_url": "https://api.groq.com/openai/v1",
            "model": "openai/gpt-oss-20b",
        },
        {
            "name": "Groq Secundário (GPT-OSS 20B)",
            "api_key": os.getenv("SECOND_GROQ_API_KEY"),
            "base_url": "https://api.groq.com/openai/v1",
            "model": "openai/gpt-oss-20b",
        },
        {
            "name": "Google Gemini (3.8 Flash)",
            "api_key": os.getenv("GEMINI_API_KEY"),
            "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
            "model": "models/gemini-3.8-flash",
        },
    ]

    trace_id = f"trace-spiderthrone-{int(time.time() * 1000)}"
    logger.info(
        f"[{trace_id}] A iniciar cadeia de failover com observabilidade Langfuse..."
    )

    for index, provider in enumerate(llm_providers):
        if not provider["api_key"]:
            continue

        start_time = time.time()
        logger.info(
            f"[{trace_id}] -> Tentativa Nível {index + 1}: {provider['name']} ({provider['model']})..."
        )

        try:
            # Usa o wrapper do Langfuse para a OpenAI para capturar automaticamente o trace
            client = OpenAI(api_key=provider["api_key"], base_url=provider["base_url"])

            kwargs = {
                "model": provider["model"],
                "temperature": temperature,
                "messages": messages,
            }

            if tools:
                kwargs["tools"] = tools
                if tool_choice:
                    kwargs["tool_choice"] = tool_choice

            response = client.chat.completions.create(**kwargs)
            duration = round((time.time() - start_time) * 1000, 2)

            logger.info(
                f"[{trace_id}] [SUCESSO] Nível {index + 1} ({provider['name']}) respondeu em {duration}ms."
            )
            return response.choices[0].message

        except Exception as e:
            duration = round((time.time() - start_time) * 1000, 2)
            logger.error(
                f"[{trace_id}] [FAILOVER ATIVO] Falha no Nível {index + 1} ({provider['name']}) após {duration}ms. Erro: {str(e)[:100]}..."
            )

    logger.critical(f"[{trace_id}] ERRO CRÍTICO: Todos os níveis do failover falharam.")
    raise Exception(
        "ERRO CRÍTICO: Todos os modelos falharam ou não existem chaves de API válidas configuradas no ficheiro .env."
    )
