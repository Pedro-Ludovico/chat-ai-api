# main.py
from fastapi import FastAPI
from pydantic import BaseModel
import asyncio
import inspect
import traceback
import re
import json

app = FastAPI()
agent = None

class Message(BaseModel):
    message: str

# importamos a função de criar agente, mas NÃO a chamamos agora
from agente.agent import criar_agente
# import da tool para chamada direta (pré-processamento / pós-processamento)
from agente.agent_tools import calcular

# ---------------------
# Helpers: detecção e pós-processamento
# ---------------------
math_detection_regex = re.compile(
    r"(\b(sqrt|raiz|raiz quadrad|raiz cúbica|pow|elevad|elevar|raiz)\b)|"  # keywords
    r"([0-9]+[.,]?[0-9]*\s*[\+\-\*/\^]\s*[0-9]+[.,]?[0-9]*)|"            # 2 + 2 or 3,14 * 2
    r"([0-9]+([.,][0-9]{3})*([.,][0-9]+)?)",                             # numbers with comma/point
    flags=re.IGNORECASE
)

def _extract_and_execute_tool_calls(text: str) -> str:
    """
    Detecta JSON de tool-calls no texto (ex.: "[{\"name\":\"calcular\",\"arguments\":{...}}]")
    ou prefixos como "[TOOL_CALLS]  [ ... ]", extrai a lista, executa as tools suportadas
    (hoje apenas 'calcular') e substitui o trecho pelo resultado.
    """
    if not text or not isinstance(text, str):
        return text

    # localizar a primeira lista JSON de objetos (procura por "[{")
    start = text.find('[{')
    end = text.rfind('}]')
    if start == -1 or end == -1 or end <= start:
        return text

    json_text = text[start:end+2]
    try:
        calls = json.loads(json_text)
    except Exception:
        # tentativa alternativa: extrair entre primeiro '[' e último ']'
        try:
            alt = text[text.find('['): text.rfind(']')+1]
            calls = json.loads(alt)
            json_text = alt
        except Exception:
            return text

    results = []
    for call in calls:
        if not isinstance(call, dict):
            continue
        name = call.get("name")
        args = call.get("arguments", {})
        if name == "calcular":
            expr = args.get("expressao") or args.get("expressao", "")
            try:
                tool_res = calcular(expr)
            except Exception as e:
                tool_res = f"Erro na tool calcular: {e}"
            results.append(str(tool_res))
        else:
            results.append(f"[Tool {name} não suportada]")

    replacement = " ".join(results).strip()
    final_text = text[:start] + replacement + text[end+2:]
    final_text = re.sub(r"\s{2,}", " ", final_text).strip()
    return final_text

def _extract_text_from_agent_response(resp) -> str:
    """
    Tenta extrair o texto principal de respostas estruturadas do agent.
    Retorna string com o conteúdo textual a ser exibido / pós-processado.
    """
    if resp is None:
        return ""

    # Se for string simples, devolve direto
    if isinstance(resp, str):
        return resp

    # Se for dicionário, tenta extrair padrões comuns do strands agent
    if isinstance(resp, dict):
        # Caso padrão: resp["message"]["content"] -> lista de dicts com 'text' ou 'toolUse'
        m = resp.get("message")
        if isinstance(m, dict):
            content = m.get("content")
            if isinstance(content, list) and content:
                # Prioriza o primeiro item com 'text'
                for c in content:
                    if isinstance(c, dict):
                        if "text" in c:
                            return c["text"]
                        # caso venha toolUse (antes de pos-processar)
                        if "toolUse" in c:
                            # stringify toolUse para pós-processamento
                            return json.dumps([c["toolUse"]])
                # fallback: stringify content
                return json.dumps(content)
            # fallback: se message for string
            if isinstance(m, str):
                return m
        # outras chaves comuns: 'response', 'result', 'output'
        for key in ("response", "result", "output"):
            if key in resp:
                val = resp[key]
                if isinstance(val, str):
                    return val
                if isinstance(val, dict):
                    return json.dumps(val)
        # fallback geral: stringify
        try:
            return json.dumps(resp)
        except Exception:
            return str(resp)

    # se for outro tipo (objeto custom), converte para string
    try:
        return str(resp)
    except Exception:
        return ""

# ---------------------
# Endpoint /chat principal
# ---------------------
@app.post("/chat")
async def chat(data: Message):
    global agent
    try:
        # --- checagem rápida de intenção matemática (pré-processamento) ---
        if math_detection_regex.search(data.message):
            try:
                tool_result = calcular(data.message)
                # se tool_result for objeto complexo, garanta string
                return {"response": str(tool_result)}
            except Exception as e:
                print("Erro ao chamar calcular diretamente (pré-process):", e)
                # cairá no fluxo padrão abaixo

        # cria o agente só na primeira requisição (evita falhas na importação)
        if agent is None:
            agent = criar_agente()

        # debug: mostra no terminal que tipo de objeto é e seus métodos públicos
        print("DEBUG agent type:", type(agent))
        print("DEBUG agent dir():", [name for name in dir(agent) if not name.startswith("_")])

        resp = None

        # 1) tenta agent.run(...)
        run_attr = getattr(agent, "run", None)
        if callable(run_attr):
            if inspect.iscoroutinefunction(run_attr):
                resp = await run_attr(data.message)
            else:
                loop = asyncio.get_running_loop()
                resp = await loop.run_in_executor(None, run_attr, data.message)
        else:
            # 2) tenta chamar o próprio agent como callable: agent(...)
            if callable(agent):
                loop = asyncio.get_running_loop()
                if inspect.iscoroutinefunction(agent):
                    resp = await agent(data.message)
                else:
                    resp = await loop.run_in_executor(None, agent, data.message)
            else:
                # 3) tenta nomes alternativos comuns
                for name in ("predict", "chat", "ask", "respond", "invoke", "run_agent", "invoke_async", "stream_async"):
                    fn = getattr(agent, name, None)
                    if callable(fn):
                        if inspect.iscoroutinefunction(fn):
                            resp = await fn(data.message)
                        else:
                            loop = asyncio.get_running_loop()
                            resp = await loop.run_in_executor(None, fn, data.message)
                        break

        # Se nada foi obtido, retorna debug
        if resp is None:
            agent_members = [name for name in dir(agent) if not name.startswith("_")]
            msg = "Nenhum método suportado encontrado para executar o Agent. Veja 'agent_dir' no retorno e no terminal."
            print(msg)
            return {"error": msg, "agent_dir": agent_members}

        # ---------------------
        # Pós-processamento: extrair texto e substituir tool-calls embutidas
        # ---------------------
        text_to_process = _extract_text_from_agent_response(resp)
        final_text = _extract_and_execute_tool_calls(text_to_process)

        # Se o texto final estiver vazio, fallback para string do resp
        if not final_text:
            final_text = _extract_text_from_agent_response(resp)

        return {"response": final_text}

    except Exception as e:
        tb = traceback.format_exc()
        print("ERRO NO /chat:\n", tb)
        return {"error": str(e), "trace": tb}


# -------------------------------------------------------------------
# Endpoint útil: resetar/recriar o agente quando ele travar
# -------------------------------------------------------------------
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
