from strands import tool
import math
import re

# Funções do math que permitimos expor na expression
_ALLOWED_FUNCS = {
    "sqrt": math.sqrt,
    "pow": pow,
    "abs": abs,
    "round": round,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    # adicione mais se precisar
}

# Conjunto de caracteres permitidos na expressão final
_ALLOWED_CHARS = set("0123456789+-*/().eE% ")

def _normalize_text_to_expr(text: str) -> str:
    """
    Tenta converter uma frase natural para uma expressão matemática.
    Exemplos:
      "raiz quadrada de 144" -> "sqrt(144)"
      "Qual é sqrt(144)?" -> "sqrt(144)"
      "2^8" -> "2**8"
    """
    txt = text.lower().strip()

    # remover pontuação comum que atrapalha (exceto parênteses)
    txt = re.sub(r"[?,;:]", " ", txt)

    # traduzir "raiz quadrada de 144" -> "sqrt(144)"
    m = re.search(r"raiz\s+quadrad[ae]\s+de\s+([0-9]+(?:\.[0-9]+)?)", txt)
    if m:
        return f"sqrt({m.group(1)})"

    # traduzir "raiz cubica de 27" -> "pow(27, 1/3)" (suporte básico)
    m2 = re.search(r"raiz\s+cubic[ae]\s+de\s+([0-9]+(?:\.[0-9]+)?)", txt)
    if m2:
        return f"pow({m2.group(1)}, 1/3)"

    # permitir expressões já no formato sqrt(144) ou pow(2,3)
    if "sqrt" in txt or "pow" in txt:
        # extrai só a parte com parênteses e nomes
        return txt

    # substituir '^' por '**'
    txt = txt.replace("^", "**")

    # extrair apenas números e operadores (caso o usuário escreva "quanto é 2 * 3")
    # primeiro tentamos encontrar algo que pareça uma expressão matemática inteira
    expr_match = re.search(r"([0-9\.\s\+\-\*/\^\%\(\)eE]+)", txt)
    if expr_match:
        expr = expr_match.group(1).strip()
        # converter ^ -> **
        expr = expr.replace("^", "**")
        return expr

    # se nada foi reconhecido, devolve string vazia para sinalizar falha
    return ""

@tool
def calcular(expressao: str) -> str:
    """
    Tool segura para avaliar expressões matemáticas.
    Recebe uma string (pode ser em linguagem natural) e tenta retornar o resultado.
    Em caso de erro, retorna uma mensagem explicativa.
    """
    try:
        if not expressao or not isinstance(expressao, str):
            return "Expressão vazia ou inválida."

        # primeiro, tente normalizar frases em português para uma expressão
        expr = _normalize_text_to_expr(expressao)

        if not expr:
            # como fallback, remove palavras e tenta extrair uma expressão "numérica"
            expr = ''.join(ch for ch in expressao if ch.isdigit() or ch in "+-*/().eE%^ ")
            expr = expr.replace("^", "**")
            expr = expr.strip()

        # após normalização, garanta que a expressão contenha apenas caracteres permitidos ou nomes de função
        # permitimos também letras que compõem nomes de funções conhecidas (sqrt, pow, sin, etc.)
        tokens_alpha = re.findall(r"[A-Za-z_]+", expr)
        for t in tokens_alpha:
            if t not in _ALLOWED_FUNCS:
                return "Função não permitida ou expressão inválida. Exemplos válidos: '2+2', '5 * (8+2)', 'sqrt(144)', 'raiz quadrada de 144'."

        # filtrar caracteres finais permitidos
        filtered = ''.join(ch for ch in expr if ch in _ALLOWED_CHARS or ch.isalpha())
        if not filtered:
            return "Não foi possível interpretar a expressão. Tente algo como: '2+2', 'sqrt(144)' ou 'raiz quadrada de 144'."

        # Avaliar de forma segura: eval com __builtins__ desligado e funções permitidas
        result = eval(filtered, {"__builtins__": None}, _ALLOWED_FUNCS)
        # formata resultado para string (remove .0 de inteiros)
        if isinstance(result, float) and result.is_integer():
            result = int(result)
        return str(result)
    except Exception as e:
        return f"Erro ao calcular: {e}"
