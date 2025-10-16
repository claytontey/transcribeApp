"""
🎤 Audio Insights - Relatórios Inteligentes
Transcreve áudios (inclui .ogg do WhatsApp), gera insights e envia PDF por e-mail.
Compatível com uso local e Streamlit Cloud (Python 3.13), sem dependência de PATH global do ffmpeg.
"""

# ============================================================
# 📦 IMPORTAÇÕES
# ============================================================
import os
import csv
import smtplib
import tempfile
from pathlib import Path
from datetime import datetime

import streamlit as st
from openai import OpenAI
import ffmpeg  # conversão/normalização de áudio

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER

# Integração opcional com Google Sheets
import gspread
from google.oauth2.service_account import Credentials

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

from shutil import which
import imageio_ffmpeg

# ============================================================
# ⚙️ CONFIGURAÇÃO INICIAL DO STREAMLIT (precisa ser a primeira chamada)
# ============================================================
st.set_page_config(page_title="Audio Insights", page_icon="🎤", layout="wide")

# ============================================================
# 🎬 CONFIGURAÇÃO DO FFMPEG (funciona local + Streamlit Cloud)
# ============================================================
ffmpeg_path = which("ffmpeg")

if not ffmpeg_path:
    try:
        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        os.environ["PATH"] += os.pathsep + os.path.dirname(ffmpeg_path)
        os.environ["IMAGEIO_FFMPEG_EXE"] = ffmpeg_path
        print(f"⚙️ ffmpeg configurado automaticamente em: {ffmpeg_path}")
    except Exception as e:
        st.error(f"❌ Não foi possível configurar o ffmpeg automaticamente: {e}")
        st.stop()
else:
    print(f"✅ ffmpeg encontrado: {ffmpeg_path}")

if not os.path.exists(ffmpeg_path):
    st.error(f"❌ ffmpeg não acessível em: {ffmpeg_path}")
    st.stop()
else:
    print("✅ ffmpeg funcional e acessível.")

# ============================================================
# 📂 PASTAS E LOGS
# ============================================================
PASTA_RESULTADOS = Path("resultados")
PASTA_RESULTADOS.mkdir(exist_ok=True)
LOG_FILE_LOCAL = Path("log_usuarios.csv")

# ============================================================
# 🔐 CARREGAMENTO DE SEGREDOS (Cloud ou Local)
# ============================================================
def carregar_segredos():
    """Carrega segredos do Streamlit Cloud ou do arquivo local .streamlit/secrets.toml"""
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
        import tomllib  # nativo no Python 3.11+
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

# ============================================================
# 🧰 FUNÇÕES UTILITÁRIAS
# ============================================================
def registrar_uso(usuario_nome: str, usuario_email: str, arquivo: str):
    """Registra uso no Google Sheets ou fallback local."""
    data = datetime.now().strftime("%d/%m/%Y")
    hora = datetime.now().strftime("%H:%M:%S")

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
            st.warning(f"⚠️ Falha ao registrar no Google Sheets: {e}. Salvando localmente...")

    novo = not LOG_FILE_LOCAL.exists()
    with open(LOG_FILE_LOCAL, "a", newline="", encoding="utf-8") as csvfile:
        w = csv.writer(csvfile)
        if novo:
            w.writerow(["Data", "Hora", "Usuário", "Email", "Arquivo"])
        w.writerow([data, hora, usuario_nome, usuario_email, arquivo])
    st.info("📝 Registro salvo em log_usuarios.csv (local).")

def transcrever_audio(audio_file):
    """Converte áudio para WAV mono 16kHz e transcreve via Whisper (aceita OGG do WhatsApp)."""
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)

        suffix = Path(audio_file.name).suffix or ".bin"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_in:
            tmp_in.write(audio_file.getvalue())
            in_path = tmp_in.name

        out_path = in_path.replace(Path(in_path).suffix, ".wav")

        (
            ffmpeg
            .input(in_path)
            .output(out_path, format="wav", acodec="pcm_s16le", ac=1, ar="16000")
            .overwrite_output()
            .run(quiet=True)
        )

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

        # ✅ Extrai o texto com segurança
        text = None
        if hasattr(tr, "text"):
            text = tr.text
        elif isinstance(tr, dict):
            text = tr.get("text")

        if not text or not str(text).strip():
            st.error("❌ A transcrição retornou resposta sem texto.")
            return None

        return text

    except FileNotFoundError:
        st.error("❌ ffmpeg não encontrado no sistema.")
        return None
    except Exception as e:
        st.error(f"❌ Erro na transcrição: {e}")
        return None


def analisar_com_ia(transcricao):
    """Analisa transcrição com GPT-4o-mini."""
    if not transcricao:
        st.error("⚠️ Transcrição vazia.")
        return None
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        prompt = (
            "Você é um assistente especializado em análise de reuniões.\n"
            "A partir da transcrição, gere um relatório com as seções:\n"
            "1) RESUMO EXECUTIVO\n2) PARTICIPANTES\n3) TÓPICOS PRINCIPAIS\n"
            "4) DECISÕES\n5) AÇÕES/TAREFAS\n6) PONTOS IMPORTANTES\n7) PRÓXIMOS PASSOS\n8) OBSERVAÇÕES.\n"
            "Formate em Markdown."
        )
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": transcricao}
            ],
            temperature=0.3
        )
        return resp.choices[0].message.content
    except Exception as e:
        st.error(f"❌ Erro na análise: {e}")
        return None

def gerar_pdf(nome_arquivo, transcricao, analise, usuario_nome):
    """Cria PDF com análise e transcrição."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_path = PASTA_RESULTADOS / f"relatorio_{usuario_nome}_{timestamp}.pdf"

    doc = SimpleDocTemplate(str(pdf_path), pagesize=A4)
    styles = getSampleStyleSheet()
    normal = ParagraphStyle("Normal10", parent=styles["Normal"], fontSize=10, alignment=TA_JUSTIFY)
    title = ParagraphStyle("Title", parent=styles["Heading1"], alignment=TA_CENTER)

    story = [
        Paragraph("🎤 Relatório de Análise de Áudio", title),
        Spacer(1, 12),
        Paragraph(f"<b>Usuário:</b> {usuario_nome}", normal),
        Paragraph(f"<b>Arquivo:</b> {nome_arquivo}", normal),
        Paragraph(f"<b>Data:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}", normal),
        Spacer(1, 16),
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
    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_EMAIL
        msg["To"] = destinatario
        msg["Subject"] = f"📊 Relatório - {nome_arquivo}"

        corpo = (
            "Olá!\n\nSegue o relatório da sua análise de áudio 🎧\n\n"
            f"Arquivo: {nome_arquivo}\nData: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
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
        st.error("❌ Falha de autenticação SMTP. Use 'senha de app' do Gmail (2FA).")
    except Exception as e:
        st.error(f"❌ Erro ao enviar e-mail: {e}")

# ============================================================
# 🧭 INTERFACE PRINCIPAL
# ============================================================
def main():
    st.title("🎤 Audio Insights - Relatórios Inteligentes")
    st.caption(f"🔐 Segredos carregados de: **{SECRETS['origem']}**")
    st.divider()

    # Inicializa o estado
    if "done" not in st.session_state:
        st.session_state.done = False

    if not st.session_state.done:
        # Formulário interativo
        with st.form("form_audio"):
            usuario_nome = st.text_input("👤 Nome ou ID de Cadastro")
            email_destino = st.text_input("📧 Email para envio do relatório")
            audio_file = st.file_uploader(
                "Selecione o arquivo de áudio",
                type=["mp3", "mp4", "mpeg", "mpga", "m4a", "wav", "webm", "ogg", "oga"],
                help="Formatos suportados: MP3, M4A, WAV, OGG (WhatsApp/Opus), WebM, etc."
            )

            submitted = st.form_submit_button("🚀 Processar e Enviar")

        if submitted:
            if not usuario_nome or not email_destino or not audio_file:
                st.error("❌ Preencha todos os campos antes de continuar.")
                return

            with st.spinner("🎧 Transcrevendo áudio..."):
                transcricao = transcrever_audio(audio_file)
                if not transcricao:
                    return
                st.success("✅ Transcrição concluída!")

            with st.spinner("🧠 Analisando conteúdo..."):
                analise = analisar_com_ia(transcricao)
                if not analise:
                    return
                st.success("✅ Análise concluída!")

            with st.spinner("📄 Gerando relatório em PDF..."):
                pdf_path = gerar_pdf(audio_file.name, transcricao, analise, usuario_nome)
                st.success("✅ PDF gerado!")

            with st.spinner("📨 Enviando relatório por e-mail..."):
                enviar_email(email_destino, pdf_path, audio_file.name)
                st.success(f"✅ Relatório enviado para {email_destino}!")

            registrar_uso(usuario_nome, email_destino, audio_file.name)

            # 🎉 Mensagem final
            st.balloons()
            st.success(f"🎉 Obrigado, {usuario_nome}! Seu relatório foi enviado com sucesso.")

            # Marca como concluído e limpa campos
            st.session_state.done = True
            st.rerun()

    else:
        # Tela pós-envio
        st.markdown("## 🙌 Obrigado por usar o Audio Insights!")
        st.info("Seu relatório foi enviado com sucesso e registrado.")
        if st.button("🔄 Novo envio"):
            # Reinicia o estado e recarrega
            st.session_state.clear()
            st.rerun()

    st.markdown("---")
    st.caption("Powered by Clayton Pereira + OpenAI")


if __name__ == "__main__":
    main()
