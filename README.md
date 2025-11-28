# 🧠 API de Chat com Agente de IA  
Integração entre **FastAPI**, **Strands Agents SDK** e **Ollama** para criar um agente de IA capaz de:

- Responder perguntas gerais usando um modelo LLM local
- Detectar operações matemáticas automaticamente
- Utilizar uma Tool de Cálculo para resolver contas com segurança
- Manter lógica de pré-processamento e pós-processamento da mensagem

Este projeto foi desenvolvido para atender ao desafio técnico proposto pela empresa, demonstrando boas práticas, modularização e uso eficiente de ferramentas de IA locais.

---

# 🚀 Tecnologias Utilizadas

- Python 3.12+
- FastAPI
- Uvicorn
- Strands Agents SDK
- Ollama (modelo LLM local)
- Python-dotenv

---

# 📁 Estrutura do Projeto

📦 agente-chat/
├── main.py
├── requirements.txt
├── .env
├── README.md
├── README_EN.md
├── .gitignore
└── agente/
├── agent.py
└── agent_tools.py

---

## ▶️ Como executar o projeto 
 
Basta seguir os passos abaixo.

---

### 1) Baixar o projeto
1. Vá até o repositório no GitHub  
2. Clique no botão verde **Code**  
3. Clique em **Download ZIP**  
4. Extraia o arquivo ZIP em alguma pasta no seu computador

---

### 2) Instalar o Ollama

Baixe e instale o Ollama (necessário para rodar a IA local):  
👉 https://ollama.com/download

Depois abra o terminal e rode: 

"ollama run mistral" ou "ollama pull mistral"

Isso baixa o modelo de IA que o projeto usa.

---

### 3) Criar ambiente virtual e instalar dependências

Abra o PowerShell dentro da pasta do projeto:

cd C:\Users\Exemplo\agente-chat>

E execute:

#### Windows:
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

#### Linux/macOS:
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

---

### 4) Rodar o servidor FastAPI

No terminal:

uvicorn main:app --reload

A API ficará disponível em:

👉 http://localhost:8000  

Documentação automática (Swagger):  
👉 http://localhost:8000/docs

---

### 5) Iniciar o Ollama (necessário para o agente responder perguntas gerais)

O Ollama precisa estar rodando ANTES do FastAPI atender perguntas.

No PowerShell (OUTRO terminal):

ollama serve


E verifique se o modelo está disponível:

curl http://127.0.0.1:11434/v1/models

---

Se a porta 11434 estiver ocupada:

Checar se a porta 11434 está livre

netstat -ano | findstr 11434

Você deve ver algo como:

TCP 127.0.0.1:11434   LISTENING   <PID do Ollama>

❌ Se a porta estiver travada por outro processo:

Encontre o PID:

netstat -ano | findstr 11434


Finalize o processo:

taskkill /PID <PID> /F | <> <== alterar apenas dentro das chaves angulares


Inicie o Ollama novamente:

ollama serve


