
from fastapi import FastAPI
from pydantic import BaseModel
import asyncio
import inspect
import traceback
import re
import json

# ---------- Inicialização básica ----------
app = FastAPI()
agent = None  # instância global do agente (reutilizada entre requisições)

# Modelo de entrada esperado pelo endpoint /chat
class Message(BaseModel):
    message: str

# Importa factory do agente e a função 'calcular' usada como "tool"
from agente.agent import criar_agente
from agente.agent_tools import calcular

# ---------- Detecção de expressões matemáticas ----------
math_detection_regex = re.compile(
    r"(\b(sqrt|raiz|raiz quadrad|raiz cúbica|pow|elevad|elevar|raiz)\b)|"  
    r"([0-9]+[.,]?[0-9]*\s*[\+\-\*/\^]\s*[0-9]+[.,]?[0-9]*)|"            
    r"([0-9]+([.,][0-9]{3})*([.,][0-9]+)?)",                             
    flags=re.IGNORECASE
)

# ---------- Função para detectar e executar tool-calls embutidas no texto ----------
def _extract_and_execute_tool_calls(text: str) -> str:
    """
    Detecta JSON de tool-calls no texto (ex.: "[{\"name\":\"calcular\",\"arguments\":{...}}]")
    ou prefixos como "[TOOL_CALLS]  [ ... ]", extrai a lista, executa as tools suportadas
    (hoje apenas 'calcular') e substitui o trecho pelo resultado.

    Retorna o texto com as tool-calls substituídas pelos resultados.
    Se nada for detectado / json inválido -> retorna o texto original.
    """
    if not text or not isinstance(text, str):
        return text

    # Busca uma sub-string que pareça um array JSON iniciando por '[{' e terminando por '}]'.
    
    start = text.find('[{')
    end = text.rfind('}]')
    if start == -1 or end == -1 or end <= start:
        return text

    json_text = text[start:end+2]
    try:
        calls = json.loads(json_text)
    except Exception:
        # Fallback: tenta extrair primeiro '[' até último ']' 
        try:
            alt = text[text.find('['): text.rfind(']')+1]
            calls = json.loads(alt)
            json_text = alt
        except Exception:
            # Se não conseguir decodificar JSON, retorna o texto original sem mexer
            return text

    results = []
    for call in calls:
        # garante que cada item seja um dict
        if not isinstance(call, dict):
            continue
        name = call.get("name")
        args = call.get("arguments", {})
        # hoje só existe a tool 'calcular' suportada aqui
        if name == "calcular":
            # pega a expressão (tenta por duas chaves diferentes, mas código atual tem redundância)
            expr = args.get("expressao") or args.get("expressao", "")
            try:
                tool_res = calcular(expr)
            except Exception as e:
                tool_res = f"Erro na tool calcular: {e}"
            results.append(str(tool_res))
        else:
            # qualquer tool não mapeada é retornada como texto informando não-suporte
            results.append(f"[Tool {name} não suportada]")

    replacement = " ".join(results).strip()
    # substitui o trecho JSON original pelo resultado concatenado
    final_text = text[:start] + replacement + text[end+2:]
    # limpa espaços duplicados e retorna
    final_text = re.sub(r"\s{2,}", " ", final_text).strip()
    return final_text

# ---------- Função para extrair texto de respostas do agent ----------
def _extract_text_from_agent_response(resp) -> str:
    """
    Recebe 'resp' que pode ser:
      - uma string simples
      - um dict com formatos variados (ex.: {'message': {'content': [...]}})
      - um dict com chaves como 'response', 'result', 'output'
      - outros objetos

    Objetivo: retornar uma string "limpa" que represente o conteúdo textual
    principal que será exibido ao usuário ou pós-processado.
    """
    if resp is None:
        return ""

    # Se já for string, retorna direto
    if isinstance(resp, str):
        return resp

    # Se for dict, tenta várias estratégias para achar o conteúdo
    if isinstance(resp, dict):
        # Caso típico: resp = {'message': {'content': [ ... ] } }
        m = resp.get("message")
        if isinstance(m, dict):
            content = m.get("content")
            if isinstance(content, list) and content:
                # percorre elementos do content buscando formatos conhecidos
                for c in content:
                    if isinstance(c, dict):
                        # formato com "text"
                        if "text" in c:
                            return c["text"]
                        # formato que indica uso de ferramenta (toolUse)
                        if "toolUse" in c:
                            # transforma numa string JSON (para ser reconhecido por _extract_and_execute_tool_calls)
                            return json.dumps([c["toolUse"]])
                # se não encontrou nada padronizado, retorna o content inteiro como JSON
                return json.dumps(content)
            # se m for string
            if isinstance(m, str):
                return m

        # tenta chaves alternativas comuns
        for key in ("response", "result", "output"):
            if key in resp:
                val = resp[key]
                if isinstance(val, str):
                    return val
                if isinstance(val, dict):
                    return json.dumps(val)

        # fallback: tenta serializar tudo como JSON
        try:
            return json.dumps(resp)
        except Exception:
            return str(resp)

    # para outros tipos, tenta converter pra string
    try:
        return str(resp)
    except Exception:
        return ""

# ---------- Endpoint principal /chat ----------
@app.post("/chat")
async def chat(data: Message):
    global agent
    try:
        # 1) Se a mensagem aparenta conter uma expressão matemática, tenta chamar 'calcular' diretamente
        #    (pré-processo rápido antes de envolver o agente).
        if math_detection_regex.search(data.message):
            try:
                tool_result = calcular(data.message)
                return {"response": str(tool_result)}
            except Exception as e:
                # log de erro mas segue processamento normal (não falha a requisição)
                print("Erro ao chamar calcular diretamente (pré-process):", e)

        # 2) Cria o agente se não existir (factory)
        if agent is None:
            agent = criar_agente()

        print("DEBUG agent type:", type(agent))
        print("DEBUG agent dir():", [name for name in dir(agent) if not name.startswith("_")])

        resp = None

        # 3) Tentativa de invocar o agente:
        #    - primeiro, tenta chamar 'run' se existir (método preferencial)
        #    - se for coroutine -> await, senão executa em executor (para evitar bloquear loop)
        run_attr = getattr(agent, "run", None)
        if callable(run_attr):
            if inspect.iscoroutinefunction(run_attr):
                resp = await run_attr(data.message)
            else:
                loop = asyncio.get_running_loop()
                resp = await loop.run_in_executor(None, run_attr, data.message)
        else:
            # 4) Se 'run' não existe, tenta se o próprio agent for chamável (callable)
            if callable(agent):
                loop = asyncio.get_running_loop()
                if inspect.iscoroutinefunction(agent):
                    resp = await agent(data.message)
                else:
                    resp = await loop.run_in_executor(None, agent, data.message)
            else:
                # 5) Finalmente, tenta uma lista de nomes de métodos comuns em agents
                for name in ("predict", "chat", "ask", "respond", "invoke", "run_agent", "invoke_async", "stream_async"):
                    fn = getattr(agent, name, None)
                    if callable(fn):
                        if inspect.iscoroutinefunction(fn):
                            resp = await fn(data.message)
                        else:
                            loop = asyncio.get_running_loop()
                            resp = await loop.run_in_executor(None, fn, data.message)
                        break

        # se nada foi executado, devolve erro com a lista de membros do agent 
        if resp is None:
            agent_members = [name for name in dir(agent) if not name.startswith("_")]
            msg = "Nenhum método suportado encontrado para executar o Agent. Veja 'agent_dir' no retorno e no terminal."
            print(msg)
            return {"error": msg, "agent_dir": agent_members}

        # 6) Extrai texto da resposta (suporta vários formatos)
        text_to_process = _extract_text_from_agent_response(resp)
        # 7) Executa tool-calls embutidas (se houver)
        final_text = _extract_and_execute_tool_calls(text_to_process)

        # fallback: se pós-processamento removeu o texto por algum motivo, tenta extrair novamente
        if not final_text:
            final_text = _extract_text_from_agent_response(resp)

        return {"response": final_text}

    except Exception as e:
        # Em caso de erro inesperado, retorna trace para debugging (pode vazar informação: atenção em produção)
        tb = traceback.format_exc()
        print("ERRO NO /chat:\n", tb)
        return {"error": str(e), "trace": tb}


# ---------- Endpoint para reset do agente ----------
@app.post("/reset")
async def reset():
    """
    Recria o agente do zero. Use quando o agente parar de responder ou ficar confuso.
    """
    global agent
    try:
        print("RESETANDO AGENTE...")
        agent = criar_agente()
        return {"status": "resetado com sucesso"}
    except Exception as e:
        return {"status": "erro", "detail": str(e)}
