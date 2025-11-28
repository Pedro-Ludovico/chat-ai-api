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
├── .gitignore
└── agente/
├── agent.py
└── agent_tools.py

yaml
Copiar código

---

# ▶️ Como executar o projeto (VERSÃO SIMPLES - baixar ZIP)

Siga os passos abaixo.

## 1) Baixar o projeto
1. Acesse o repositório no GitHub  
2. Clique no botão verde **Code**  
3. Clique em **Download ZIP**  
4. Extraia o arquivo em alguma pasta no seu computador  

---

## 2) Instalar o Ollama

-Baixe e instale o Ollama:  
-👉 https://ollama.com/download

-Após instalar, abra um terminal no PowerShell e execute:


-ollama pull mistral


---

3) Criar ambiente virtual e instalar dependências
Abra o PowerShell dentro da pasta do projeto extraído:

-cd C:\Users\SeuUsuario\agente-chat

-Windows:

-python -m venv .venv
-.\.venv\Scripts\Activate.ps1
-pip install -r requirements.txt

-Linux/macOS:

-python -m venv .venv
-source .venv/bin/activate
-pip install -r requirements.txt


---


4) Iniciar o servidor FastAPI
No terminal (após ativar o .venv):

-uvicorn main:app --reload

-A API ficará disponível em:

-👉 http://localhost:8000
-👉 http://localhost:8000/docs (Swagger UI)


---


5) Iniciar o servidor do Ollama
-⚠️ O Ollama precisa estar rodando antes de fazer perguntas gerais ao agente.

-Abra outro terminal e execute:

-ollama serve

-Verifique se o modelo está disponível:

-curl http://127.0.0.1:11434/v1/models


---


🚨 Problemas comuns com a porta 11434
-❗ Se o Ollama der erro de porta ocupada
-Verifique a porta:

-netstat -ano | findstr 11434

-Se aparecer algo assim:

-TCP 127.0.0.1:11434   LISTENING   <PID>

-Então outro processo está usando a porta.

-✔️ Como resolver
-Pegue o PID exibido

-Finalize o processo:

-taskkill /PID <PID> /F

-Inicie o Ollama novamente:

-ollama serve
