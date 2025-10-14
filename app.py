"""
🎤 Audio Insights - Relatórios Inteligentes
Transcreve áudios, gera insights e envia relatório em PDF por e-mail.
Compatível com uso local e Streamlit Cloud.
"""

# ============================================================
# 🔧 IMPORTAÇÕES
# ============================================================
import streamlit as st
import os
import csv
import tempfile
from datetime import datetime
from pathlib import Path
from openai import OpenAI
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
# ✅ Compatibilidade entre Python 3.10 e 3.11+
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


# ============================================================
# ⚙️ CONFIGURAÇÃO INICIAL
# ============================================================
st.set_page_config(page_title="Audio Insights", page_icon="🎤", layout="wide")

# 📂 Diretórios
PASTA_RESULTADOS = Path("resultados")
PASTA_RESULTADOS.mkdir(exist_ok=True)
LOG_FILE = Path("log_usuarios.csv")

# ============================================================
# 🔒 CARREGAMENTO DE SEGREDOS (Cloud ou Local)
# ============================================================

def carregar_segredos():
    """Lê credenciais do Streamlit Cloud ou de um arquivo local (.streamlit/secrets.toml)."""
    try:
        # 🟢 Caso esteja no Streamlit Cloud
        openai_key = st.secrets["OPENAI_API_KEY"]
        smtp_email = st.secrets["SMTP_EMAIL"]
        smtp_senha = st.secrets["SMTP_SENHA"]
        smtp_servidor = st.secrets["SMTP_SERVIDOR"]
        smtp_porta = st.secrets["SMTP_PORTA"]
        origem = "Streamlit Cloud"
    except Exception:
        # 🟡 Fallback local
        try:
            caminho_local = Path(".streamlit/secrets.toml")
            if caminho_local.exists():
                with open(caminho_local, "rb") as f:
                    data = tomllib.load(f)
                openai_key = data.get("OPENAI_API_KEY")
                smtp_email = data.get("SMTP_EMAIL")
                smtp_senha = data.get("SMTP_SENHA")
                smtp_servidor = data.get("SMTP_SERVIDOR", "smtp.gmail.com")
                smtp_porta = data.get("SMTP_PORTA", 587)
                origem = "arquivo local"
            else:
                st.error("❌ Nenhum segredo encontrado. Configure no Streamlit Cloud ou crie .streamlit/secrets.toml.")
                st.stop()
        except Exception as e:
            st.error(f"❌ Erro ao carregar segredos locais: {e}")
            st.stop()

    return openai_key, smtp_email, smtp_senha, smtp_servidor, smtp_porta, origem


# 🔑 Carrega segredos automaticamente
OPENAI_API_KEY, SMTP_EMAIL, SMTP_SENHA, SMTP_SERVIDOR, SMTP_PORTA, origem_segredos = carregar_segredos()

# ============================================================
# 🔄 FUNÇÕES PRINCIPAIS
# ============================================================

def registrar_uso(usuario_nome, usuario_email, arquivo):
    """Registra cada uso do app para controle/cobrança."""
    novo = not LOG_FILE.exists()
    with open(LOG_FILE, "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        if novo:
            writer.writerow(["Data", "Hora", "Usuário", "Email", "Arquivo"])
        writer.writerow([
            datetime.now().strftime("%d/%m/%Y"),
            datetime.now().strftime("%H:%M:%S"),
            usuario_nome,
            usuario_email,
            arquivo
        ])

def transcrever_audio(audio_file):
    """Transcreve o áudio com Whisper."""
    import os
    from openai import OpenAI
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
    client = OpenAI()

    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(audio_file.name).suffix) as tmp:
        tmp.write(audio_file.getvalue())
        tmp_path = tmp.name
    with open(tmp_path, "rb") as audio:
        result = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio,
            language="pt"
        )
    os.unlink(tmp_path)
    return result.text

def analisar_com_ia(transcricao):
    """Analisa a transcrição com GPT-4."""
    import os
    from openai import OpenAI
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
    client = OpenAI()
    prompt = """
Você é um assistente especializado em análise de reuniões.
Extraia da transcrição:
1. RESUMO EXECUTIVO
2. PARTICIPANTES
3. TÓPICOS PRINCIPAIS
4. DECISÕES TOMADAS
5. AÇÕES E TAREFAS
6. PONTOS IMPORTANTES
7. PRÓXIMOS PASSOS
8. OBSERVAÇÕES
"""
    resp = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": transcricao}
        ],
        temperature=0.3
    )
    return resp.choices[0].message.content

def gerar_pdf(nome_arquivo, transcricao, analise, usuario_nome):
    """Cria o PDF do relatório."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_path = PASTA_RESULTADOS / f"relatorio_{usuario_nome}_{timestamp}.pdf"

    doc = SimpleDocTemplate(str(pdf_path), pagesize=A4)
    styles = getSampleStyleSheet()
    normal = ParagraphStyle("Normal", parent=styles["Normal"], fontSize=10, alignment=TA_JUSTIFY)
    title = ParagraphStyle("Title", parent=styles["Heading1"], alignment=TA_CENTER)

    story = [
        Paragraph("🎤 Relatório de Análise de Áudio", title),
        Spacer(1, 12),
        Paragraph(f"<b>Usuário:</b> {usuario_nome}", normal),
        Paragraph(f"<b>Arquivo:</b> {nome_arquivo}", normal),
        Paragraph(f"<b>Data:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}", normal),
        Spacer(1, 12),
        Paragraph("<b>🧠 Análise e Insights</b>", styles["Heading2"]),
        Paragraph(analise.replace("\n", "<br/>"), normal),
        PageBreak(),
        Paragraph("<b>📝 Transcrição Completa</b>", styles["Heading2"]),
        Paragraph(transcricao.replace("\n", "<br/>"), normal)
    ]
    doc.build(story)
    return str(pdf_path)

def enviar_email(destinatario, pdf_path, nome_arquivo):
    """Envia o relatório por e-mail."""
    msg = MIMEMultipart()
    msg["From"] = SMTP_EMAIL
    msg["To"] = destinatario
    msg["Subject"] = f"📊 Relatório de Análise - {nome_arquivo}"

    corpo = f"""
Olá!

Segue o relatório da sua análise de áudio 🎧

Arquivo: {nome_arquivo}
Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}

Atenciosamente,  
Audio Insights 🚀
"""

    msg.attach(MIMEText(corpo, "plain"))
    with open(pdf_path, "rb") as anexo:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(anexo.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f"attachment; filename={Path(pdf_path).name}")
        msg.attach(part)

    server = smtplib.SMTP(SMTP_SERVIDOR, SMTP_PORTA)
    server.starttls()
    server.login(SMTP_EMAIL, SMTP_SENHA)
    server.send_message(msg)
    server.quit()

# ============================================================
# 🧭 INTERFACE STREAMLIT
# ============================================================

def main():
    st.title("🎤 Audio Insights - Relatórios Inteligentes")
    st.markdown(f"🔐 Rodando com segredos de: **{origem_segredos}**")
    st.divider()

    usuario_nome = st.text_input("👤 Nome ou ID de Cadastro")
    email_destino = st.text_input("📧 Email para envio do relatório")
    audio_file = st.file_uploader("🎙️ Selecione o arquivo de áudio", type=["mp3", "wav", "m4a", "webm"])

    if st.button("🚀 Processar e Enviar"):
        if not usuario_nome or not email_destino or not audio_file:
            st.error("❌ Preencha todos os campos antes de continuar.")
            return

        with st.spinner("🎧 Transcrevendo áudio..."):
            transcricao = transcrever_audio(audio_file)
            st.success("✅ Transcrição concluída!")

        with st.spinner("🧠 Analisando conteúdo..."):
            analise = analisar_com_ia(transcricao)
            st.success("✅ Análise concluída!")

        with st.spinner("📄 Gerando relatório em PDF..."):
            pdf_path = gerar_pdf(audio_file.name, transcricao, analise, usuario_nome)
            st.success("✅ PDF gerado com sucesso!")

        with st.spinner("📨 Enviando relatório por e-mail..."):
            enviar_email(email_destino, pdf_path, audio_file.name)
            st.success(f"✅ Relatório enviado para {email_destino}!")

        registrar_uso(usuario_nome, email_destino, audio_file.name)
        st.balloons()

    st.markdown("---")
    st.caption("Desenvolvido por Clayton Pereira | Powered by OpenAI + Streamlit")


if __name__ == "__main__":
    main()
