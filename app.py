"""
🎤 Audio Insights - Relatórios Inteligentes
Transcreve áudios (inclui .ogg do WhatsApp), gera insights e envia PDF por e-mail.
Compatível com uso local e Streamlit Cloud (Python 3.13), sem pydub.
"""

# =========================
# Imports
# =========================
import os
import csv
import smtplib
import tempfile
from pathlib import Path
from datetime import datetime

import streamlit as st
from openai import OpenAI
import ffmpeg  # conversão/normalização de áudio (sem pydub)

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER

# Google Sheets (opcional – com fallback para CSV local)
import gspread
from google.oauth2.service_account import Credentials

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

from shutil import which
import imageio_ffmpeg

# =========================
# Configuração de página
# =========================
# Verifica se o ffmpeg está acessível
if not which("ffmpeg"):
    ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
    st.info(f"⚙️ ffmpeg configurado automaticamente em: {ffmpeg_path}")
    
st.set_page_config(page_title="Audio Insights", page_icon="🎤", layout="wide")

# Pastas e arquivos
PASTA_RESULTADOS = Path("resultados")
PASTA_RESULTADOS.mkdir(exist_ok=True)
LOG_FILE_LOCAL = Path("log_usuarios.csv")  # fallback se Google Sheets falhar

# =========================
# Segredos (Cloud ou local)
# =========================
def carregar_segredos():
    """
    Carrega secrets do Streamlit Cloud (st.secrets) ou do arquivo local .streamlit/secrets.toml.
    Para uso local, basta criar esse arquivo com as chaves:
      OPENAI_API_KEY, SMTP_EMAIL, SMTP_SENHA, SMTP_SERVIDOR, SMTP_PORTA
    Opcional: bloco [google_service_account] + SHEET_ID para log no Google Sheets.
    """
    origem = "Streamlit Cloud"
    try:
        openai_key = st.secrets["OPENAI_API_KEY"]
        smtp_email = st.secrets["SMTP_EMAIL"]
        smtp_senha = st.secrets["SMTP_SENHA"]
        smtp_servidor = st.secrets.get("SMTP_SERVIDOR", "smtp.gmail.com")
        smtp_porta = int(st.secrets.get("SMTP_PORTA", 587))
        gs_creds = st.secrets.get("google_service_account", None)
        sheet_id = st.secrets.get("SHEET_ID", None)
    except Exception:
        origem = "arquivo local (.streamlit/secrets.toml)"
        import tomllib  # Python 3.11+ (se estiver em 3.10, use tomli e troque aqui)
        p = Path(".streamlit/secrets.toml")
        if not p.exists():
            st.error("❌ Nenhum segredo encontrado. Configure no Streamlit Cloud ou crie .streamlit/secrets.toml.")
            st.stop()
        with open(p, "rb") as f:
            data = tomllib.load(f)
        openai_key = data["OPENAI_API_KEY"]
        smtp_email = data["SMTP_EMAIL"]
        smtp_senha = data["SMTP_SENHA"]
        smtp_servidor = data.get("SMTP_SERVIDOR", "smtp.gmail.com")
        smtp_porta = int(data.get("SMTP_PORTA", 587))
        gs_creds = data.get("google_service_account", None)
        sheet_id = data.get("SHEET_ID", None)

    return {
        "origem": origem,
        "OPENAI_API_KEY": openai_key,
        "SMTP_EMAIL": smtp_email,
        "SMTP_SENHA": smtp_senha,
        "SMTP_SERVIDOR": smtp_servidor,
        "SMTP_PORTA": smtp_porta,
        "GS_CREDS": gs_creds,
        "SHEET_ID": sheet_id,
    }

SECRETS = carregar_segredos()
OPENAI_API_KEY = SECRETS["OPENAI_API_KEY"]
SMTP_EMAIL = SECRETS["SMTP_EMAIL"]
SMTP_SENHA = SECRETS["SMTP_SENHA"]
SMTP_SERVIDOR = SECRETS["SMTP_SERVIDOR"]
SMTP_PORTA = SECRETS["SMTP_PORTA"]
GS_CREDS = SECRETS["GS_CREDS"]
SHEET_ID = SECRETS["SHEET_ID"]

# =========================
# Utilidades
# =========================
def registrar_uso(usuario_nome: str, usuario_email: str, arquivo: str):
    """
    Registra o uso no Google Sheets (se configurado).
    Fallback: salva/append em CSV local (log_usuarios.csv).
    """
    data = datetime.now().strftime("%d/%m/%Y")
    hora = datetime.now().strftime("%H:%M:%S")

    # 1) Tenta Google Sheets se credenciais existirem
    if GS_CREDS and SHEET_ID:
        try:
            credentials = Credentials.from_service_account_info(
                GS_CREDS, scopes=["https://www.googleapis.com/auth/spreadsheets"]
            )
            client = gspread.authorize(credentials)
            sheet = client.open_by_key(SHEET_ID).sheet1
            sheet.append_row([data, hora, usuario_nome, usuario_email, arquivo])
            st.success("✅ Registro salvo no Google Sheets!")
            return
        except Exception as e:
            st.warning(f"⚠️ Falha ao registrar no Google Sheets: {e}. Vou salvar localmente.")

    # 2) Fallback: CSV local
    novo = not LOG_FILE_LOCAL.exists()
    with open(LOG_FILE_LOCAL, "a", newline="", encoding="utf-8") as csvfile:
        w = csv.writer(csvfile)
        if novo:
            w.writerow(["Data", "Hora", "Usuário", "Email", "Arquivo"])
        w.writerow([data, hora, usuario_nome, usuario_email, arquivo])
    st.info("📝 Registro salvo em log_usuarios.csv (local).")

def transcrever_audio(audio_file) -> str | None:
    """
    Converte QUALQUER áudio recebido para WAV mono 16kHz com ffmpeg e envia ao Whisper.
    Suporta: .ogg (WhatsApp/Opus), .mp3, .m4a, .wav, .webm, etc.
    """
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)

        # salva original
        suffix = Path(audio_file.name).suffix or ".bin"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_in:
            tmp_in.write(audio_file.getvalue())
            in_path = tmp_in.name

        # saída WAV padronizada
        out_path = in_path.replace(Path(in_path).suffix, ".wav")

        # conversão/normalização
        (
            ffmpeg
            .input(in_path)
            .output(
                out_path,
                format="wav",
                acodec="pcm_s16le",  # PCM 16-bit
                ac=1,                # mono
                ar="16000"           # 16 kHz
            )
            .overwrite_output()
            .run(quiet=True)
        )

        # transcrição
        with open(out_path, "rb") as f:
            tr = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                language="pt"
            )

        # limpeza
        try:
            os.unlink(in_path)
            os.unlink(out_path)
        except Exception:
            pass

        # diferentes formatos de retorno (compat com SDKs)
        if hasattr(tr, "text"):
            return tr.text
        if isinstance(tr, dict) and "text" in tr:
            return tr["text"]

        st.error("❌ A transcrição não retornou texto.")
        return None

    except FileNotFoundError as e:
        st.error("❌ ffmpeg não encontrado no sistema. No macOS: `brew install ffmpeg`.")
        return None
    except Exception as e:
        st.error(f"❌ Erro na transcrição: {e}")
        return None

def analisar_com_ia(transcricao: str) -> str | None:
    """Gera análise estruturada com GPT-4o-mini. Retorna markdown."""
    if not transcricao or not transcricao.strip():
        st.error("⚠️ Transcrição vazia. Não é possível analisar.")
        return None

    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        prompt = (
            "Você é um assistente especializado em análise de reuniões.\n"
            "A partir da transcrição, produza um relatório claro e objetivo com seções:\n"
            "1) RESUMO EXECUTIVO (2-3 parágrafos)\n"
            "2) PARTICIPANTES\n"
            "3) TÓPICOS PRINCIPAIS\n"
            "4) DECISÕES TOMADAS\n"
            "5) AÇÕES E TAREFAS (responsável e prazo se houver)\n"
            "6) PONTOS IMPORTANTES (datas/valores)\n"
            "7) PRÓXIMOS PASSOS\n"
            "8) OBSERVAÇÕES\n"
            "Formate em Markdown."
        )
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Transcrição:\n\n{transcricao}"}
            ],
            temperature=0.3
        )
        return resp.choices[0].message.content
    except Exception as e:
        st.error(f"❌ Erro na análise com IA: {e}")
        return None

def gerar_pdf(nome_arquivo: str, transcricao: str, analise: str, usuario_nome: str) -> str:
    """Gera um PDF profissional com a análise e a transcrição."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_path = PASTA_RESULTADOS / f"relatorio_{usuario_nome}_{timestamp}.pdf"

    doc = SimpleDocTemplate(str(pdf_path), pagesize=A4, leftMargin=48, rightMargin=48, topMargin=48, bottomMargin=36)
    styles = getSampleStyleSheet()
    normal = ParagraphStyle("Normal10", parent=styles["Normal"], fontSize=10, alignment=TA_JUSTIFY)
    title = ParagraphStyle("Title", parent=styles["Heading1"], alignment=TA_CENTER, fontSize=20)

    story = []
    story += [
        Paragraph("🎤 Relatório de Análise de Áudio", title),
        Spacer(1, 10),
        Paragraph(f"<b>Usuário:</b> {usuario_nome}", normal),
        Paragraph(f"<b>Arquivo:</b> {nome_arquivo}", normal),
        Paragraph(f"<b>Data:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}", normal),
        Spacer(1, 16),
        Paragraph("<b>🧠 Análise e Insights</b>", styles["Heading2"]),
        Paragraph(analise.replace("\n", "<br/>"), normal),
        PageBreak(),
        Paragraph("<b>📝 Transcrição Completa</b>", styles["Heading2"]),
        Paragraph(transcricao.replace("\n", "<br/>"), normal),
    ]
    doc.build(story)
    return str(pdf_path)

def enviar_email(destinatario: str, pdf_path: str, nome_arquivo: str):
    """Envia o PDF por e-mail usando SMTP (Gmail com 'senha de app')."""
    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_EMAIL
        msg["To"] = destinatario
        msg["Subject"] = f"📊 Relatório de Análise - {nome_arquivo}"

        corpo = (
            "Olá!\n\n"
            "Segue o relatório da sua análise de áudio 🎧\n\n"
            f"Arquivo: {nome_arquivo}\n"
            f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
            "Atenciosamente,\nClayton Pereira 🚀"
        )
        msg.attach(MIMEText(corpo, "plain"))

        with open(pdf_path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f"attachment; filename={Path(pdf_path).name}")
        msg.attach(part)

        server = smtplib.SMTP(SMTP_SERVIDOR, SMTP_PORTA)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_SENHA)
        server.send_message(msg)
        server.quit()
    except smtplib.SMTPAuthenticationError:
        st.error("❌ Falha na autenticação SMTP. Use 'senha de app' do Gmail (2FA).")
        raise
    except Exception as e:
        st.error(f"❌ Erro ao enviar e-mail: {e}")
        raise

# =========================
# UI
# =========================
def main():
    st.title("🎤 Audio Insights - Relatórios Inteligentes")
    st.caption(f"🔐 Segredos carregados de: **{SECRETS['origem']}**")
    st.divider()

    col1, col2 = st.columns([2, 1])
    with col1:
        usuario_nome = st.text_input("👤 Nome ou ID de Cadastro")
        email_destino = st.text_input("📧 Email para envio do relatório")
        audio_file = st.file_uploader(
            "Selecione o arquivo de áudio",
            type=["mp3", "mp4", "mpeg", "mpga", "m4a", "wav", "webm", "ogg", "oga"],
            help="Formatos suportados: MP3, M4A, WAV, OGG (WhatsApp/Opus), WebM, etc."
        )
        if audio_file:
            st.info(f"📦 Arquivo: {audio_file.name} • {(len(audio_file.getvalue())/1024/1024):.2f} MB")

    with col2:
        st.write(" ")
        processar = st.button("🚀 Processar e Enviar", use_container_width=True)

    if processar:
        if not usuario_nome or not email_destino or not audio_file:
            st.error("❌ Preencha Nome, Email e selecione um arquivo de áudio.")
            return

        # Transcrição
        with st.spinner("🎧 Transcrevendo áudio..."):
            transcricao = transcrever_audio(audio_file)
            if not transcricao:
                return
            st.success("✅ Transcrição concluída!")

        # Análise
        with st.spinner("🧠 Analisando conteúdo..."):
            analise = analisar_com_ia(transcricao)
            if not analise:
                return
            st.success("✅ Análise concluída!")

        # PDF
        with st.spinner("📄 Gerando relatório em PDF..."):
            pdf_path = gerar_pdf(audio_file.name, transcricao, analise, usuario_nome)
            st.success("✅ PDF gerado!")

        # E-mail
        with st.spinner("📨 Enviando relatório por e-mail..."):
            enviar_email(email_destino, pdf_path, audio_file.name)
            st.success(f"✅ Relatório enviado para {email_destino}!")

        # Log
        registrar_uso(usuario_nome, email_destino, audio_file.name)
        st.balloons()

    st.markdown("---")
    st.caption("Powered by Clayton Pereira + OpenAI")

if __name__ == "__main__":
    main()
