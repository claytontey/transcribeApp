"""
Audio Insights - Interface Web com Streamlit
Transcreve áudios, gera insights e envia PDF por email
"""

# ============================================================
# 🔧 IMPORTAÇÕES E CONFIGURAÇÃO INICIAL
# ============================================================

import streamlit as st

# ⚙️ Configuração da página (DEVE SER a primeira chamada Streamlit)
st.set_page_config(
    page_title="Audio Insights",
    page_icon="🎤",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# 🧩 IMPORTAÇÕES PADRÃO
# ============================================================

import os
import tempfile
from datetime import datetime
from pathlib import Path
from openai import OpenAI
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# ============================================================
# 📁 DIRETÓRIOS PADRÃO
# ============================================================

PASTA_TEMP = Path("temp")
PASTA_RESULTADOS = Path("resultados")
PASTA_TEMP.mkdir(exist_ok=True)
PASTA_RESULTADOS.mkdir(exist_ok=True)

# ============================================================
# 🔄 FUNÇÕES AUXILIARES DE SESSÃO
# ============================================================

def inicializar_sessao():
    """Inicializa variáveis de sessão"""
    if 'processado' not in st.session_state:
        st.session_state.processado = False
    if 'transcricao' not in st.session_state:
        st.session_state.transcricao = ""
    if 'analise' not in st.session_state:
        st.session_state.analise = ""
    if 'pdf_path' not in st.session_state:
        st.session_state.pdf_path = None


# ============================================================
# 🎙️ FUNÇÃO DE TRANSCRIÇÃO DE ÁUDIO
# ============================================================

def transcrever_audio(audio_file, api_key: str) -> str:
    """Transcreve áudio usando Whisper"""
    try:
        client = OpenAI(api_key=api_key)

        # Salva arquivo temporário
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(audio_file.name).suffix) as tmp_file:
            tmp_file.write(audio_file.getvalue())
            tmp_path = tmp_file.name

        # Transcreve o áudio
        with open(tmp_path, "rb") as audio:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio,
                language="pt"
            )

        os.unlink(tmp_path)
        return transcription.text

    except Exception as e:
        st.error(f"❌ Erro na transcrição: {str(e)}")
        return None


# ============================================================
# 🧠 FUNÇÃO DE ANÁLISE COM GPT-4
# ============================================================

def analisar_com_ia(transcricao: str, api_key: str) -> str:
    """Analisa transcrição com GPT-4"""
    try:
        client = OpenAI(api_key=api_key)

        prompt_sistema = """
Você é um assistente especializado em analisar conversas e reuniões.
Analise a transcrição fornecida e extraia os seguintes insights estruturados:
1. RESUMO EXECUTIVO
2. PARTICIPANTES
3. TÓPICOS PRINCIPAIS
4. DECISÕES TOMADAS
5. AÇÕES E TAREFAS
6. PONTOS IMPORTANTES
7. PRÓXIMOS PASSOS
8. OBSERVAÇÕES
"""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": f"Transcrição:\n\n{transcricao}"}
            ],
            temperature=0.3
        )

        return response.choices[0].message.content

    except Exception as e:
        st.error(f"❌ Erro na análise: {str(e)}")
        return None

# ... (restante das funções gerar_pdf, enviar_email, etc.)

def main():
    """Função principal da aplicação"""
    # toda a interface Streamlit vai aqui:
    # - título
    # - upload de áudio
    # - inputs de email
    # - botão processar
    # - exibição dos resultados
    pass  # (ou seu conteúdo completo)

if __name__ == "__main__":
    main()
