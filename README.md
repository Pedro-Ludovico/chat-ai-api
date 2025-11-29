# 🧠 API de Chat com Agente de IA  

Integração entre **FastAPI**, **Strands Agents SDK** e **Ollama** para criar um agente de IA capaz de:

- Responder perguntas gerais usando um modelo LLM local  
- Detectar operações matemáticas automaticamente  
- Utilizar uma Tool de Cálculo para resolver contas com segurança  
- Manter lógica de pré-processamento e pós-processamento da mensagem  

---

# 🚀 Tecnologias Utilizadas

- Python 3.12+  
- FastAPI  
- Uvicorn  
- Strands Agents SDK  
- Ollama  
- Python-dotenv  

---

# 📁 Estrutura do Projeto

```
📦 agente-chat/
├── main.py
├── requirements.txt
├── .env
├── README.md
├── .gitignore
└── agente/
    ├── agent.py
    └── agent_tools.py
```

---

# ▶️ Como executar o projeto

## 2) Instalar o Ollama

Baixe e instale o Ollama:  
👉 https://ollama.com/download

Após instalar, execute no PowerShell:

```
ollama pull mistral
```

---

## 3) Criar ambiente virtual e instalar dependências

Entre na pasta do projeto ainda no PowerShell:

```
cd C:\Users\SeuUsuario\agente-chat
```

### Windows:
```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Linux/macOS:
```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 4) Iniciar o servidor FastAPI

```
uvicorn main:app --reload
```

A API ficará em:

http://localhost:8000  
http://localhost:8000/docs  

---

## 5) Iniciar o servidor do Ollama

O Ollama precisa estar rodando (Abra um novo PowerShell):

```
ollama serve
```

Verifique se o modelo está disponível:

```
curl http://127.0.0.1:11434/v1/models
```

---

# 🚨 Problemas comuns com a porta 11434

Verificar se a porta está ocupada:

```
netstat -ano | findstr 11434
```

Se aparecer:

```
TCP 127.0.0.1:11434   LISTENING   <PID>
```

Outro processo está usando a porta.

---

## ✔️ Como resolver

Mate o processo pela PID:

```
taskkill /PID <PID> /F
```

Depois reinicie o Ollama:

```
ollama serve
```

---

### 📌Reset

Aperte o Reset quando precisar reiniciar o agente, ele pode travar caso não entenda sua pergunta.
