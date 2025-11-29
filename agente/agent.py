from strands import Agent
from strands.models.ollama import OllamaModel
from dotenv import load_dotenv
import os

from .agent_tools import calcular

# Carrega variáveis definidas em um arquivo .env (se existir)
load_dotenv()

def criar_agente():
    # Lê variáveis de ambiente (com defaults caso não estejam definidas)
    modelo = os.getenv("LLM_MODEL", "mistral")
    ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")

    # Cria o wrapper do modelo que se conecta ao servidor Ollama.
    llm = OllamaModel(
        host=ollama_host,
        model_id=modelo
    )

    # Prompt de sistema que orienta o comportamento do agente em relação ao uso da ferramenta 'calcular'.
    system_prompt = (
        "Você é um assistente útil com acesso a uma ferramenta chamada 'calcular'.\n"
        "Regras:\n"
        "1) Use a ferramenta 'calcular' SOMENTE se a mensagem contiver uma expressão matemática explícita\n"
        "   (exemplos: '2+2', '5 * (3+1)', 'sqrt(144)', 'raiz quadrada de 81', '2^10').\n"
        "2) Para perguntas gerais (história, datas, definições, curiosidades, opiniões, etc.), responda normalmente e não use ferramentas.\n"
        "3) Se houver ambiguidade, prefira primeiro responder de forma curta. Só então, se for claramente cálculo, invoque a ferramenta.\n"
        "4) Quando chamar a ferramenta, envie APENAS a expressão matemática (por exemplo: 'sqrt(144)' ou '2+2').\n"
    )

    # Instancia o Agent, passando o prompt, a lista de tools e o modelo LLM
    agente = Agent(
        system_prompt=system_prompt,
        tools=[calcular],
        model=llm
    )

    # Retorna o agente configurado para uso
    return agente
