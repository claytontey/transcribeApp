"""
Audio Insights - Interface Web com Streamlit
Transcreve áudios, gera insights e envia PDF por email
"""

import streamlit as st
import os
import tempfile
from datetime import datetime
from pathlib import Path
from openai import OpenAI
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# Configuração da página
st.set_page_config(
    page_title="Audio Insights",
    page_icon="🎤",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Diretórios
PASTA_TEMP = Path("temp")
PASTA_RESULTADOS = Path("resultados")
PASTA_TEMP.mkdir(exist_ok=True)
PASTA_RESULTADOS.mkdir(exist_ok=True)


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


def transcrever_audio(audio_file, api_key: str) -> str:
    """Transcreve áudio usando Whisper"""
    try:
        client = OpenAI(api_key=api_key)
        
        # Salva arquivo temporariamente
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(audio_file.name).suffix) as tmp_file:
            tmp_file.write(audio_file.getvalue())
            tmp_path = tmp_file.name
        
        # Transcreve
        with open(tmp_path, "rb") as audio:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio,
                language="pt"
            )
        
        # Remove arquivo temporário
        os.unlink(tmp_path)
        
        return transcription.text
    
    except Exception as e:
        st.error(f"Erro na transcrição: {str(e)}")
        return None


def analisar_com_ia(transcricao: str, api_key: str) -> str:
    """Analisa transcrição com GPT-4"""
    try:
        client = OpenAI(api_key=api_key)
        
        prompt_sistema = """
Você é um assistente especializado em analisar conversas e reuniões.

Analise a transcrição fornecida e extraia os seguintes insights:

1. **RESUMO EXECUTIVO** (2-3 parágrafos)
   - Contexto geral da conversa
   - Objetivo principal
   - Conclusão geral

2. **PARTICIPANTES**
   - Liste todas as pessoas mencionadas

3. **TÓPICOS PRINCIPAIS**
   - Liste os principais assuntos discutidos
   - Ordene por importância

4. **DECISÕES TOMADAS**
   - O que foi decidido
   - Quem aprovou
   - Impacto esperado

5. **AÇÕES E TAREFAS**
   - Tarefa específica
   - Responsável (se mencionado)
   - Prazo (se mencionado)
   - Prioridade (alta/média/baixa)

6. **PONTOS IMPORTANTES**
   - Informações críticas mencionadas
   - Números, datas, valores relevantes
   - Compromissos assumidos

7. **PRÓXIMOS PASSOS**
   - O que precisa ser feito após esta conversa
   - Sequência de ações recomendada

8. **OBSERVAÇÕES**
   - Pontos que merecem atenção
   - Riscos identificados
   - Oportunidades mencionadas

Seja objetivo, claro e organize as informações de forma estruturada.
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
        st.error(f"Erro na análise: {str(e)}")
        return None


def gerar_pdf(nome_arquivo: str, transcricao: str, analise: str) -> str:
    """Gera PDF profissional com a análise"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_base = Path(nome_arquivo).stem
    pdf_filename = f"analise_{nome_base}_{timestamp}.pdf"
    pdf_path = PASTA_RESULTADOS / pdf_filename
    
    # Cria documento PDF
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18
    )
    
    # Estilos
    styles = getSampleStyleSheet()
    
    # Estilo customizado para título
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor='#1f77b4',
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    # Estilo para subtítulos
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=16,
        textColor='#2c3e50',
        spaceAfter=12,
        spaceBefore=12
    )
    
    # Estilo para texto normal
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_JUSTIFY,
        spaceAfter=12
    )
    
    # Conteúdo do PDF
    story = []
    
    # Título
    story.append(Paragraph("📊 Análise de Reunião", title_style))
    story.append(Spacer(1, 12))
    
    # Informações do arquivo
    info_text = f"""
    <b>Arquivo Original:</b> {nome_arquivo}<br/>
    <b>Data da Análise:</b> {datetime.now().strftime("%d/%m/%Y às %H:%M")}<br/>
    <b>Gerado por:</b> Audio Insights
    """
    story.append(Paragraph(info_text, normal_style))
    story.append(Spacer(1, 20))
    
    # Linha separadora
    story.append(Paragraph("_" * 100, normal_style))
    story.append(Spacer(1, 20))
    
    # Análise e Insights
    story.append(Paragraph("🧠 ANÁLISE E INSIGHTS", subtitle_style))
    story.append(Spacer(1, 12))
    
    # Processa a análise (converte markdown para PDF)
    for linha in analise.split('\n'):
        if linha.strip():
            # Títulos
            if linha.startswith('###'):
                texto = linha.replace('###', '').strip()
                story.append(Paragraph(f"<b>{texto}</b>", subtitle_style))
            elif linha.startswith('##'):
                texto = linha.replace('##', '').strip()
                story.append(Paragraph(f"<b>{texto}</b>", subtitle_style))
            elif linha.startswith('#'):
                texto = linha.replace('#', '').strip()
                story.append(Paragraph(f"<b>{texto}</b>", title_style))
            # Listas
            elif linha.startswith('- ') or linha.startswith('* '):
                texto = linha[2:].strip()
                story.append(Paragraph(f"• {texto}", normal_style))
            # Texto normal
            else:
                # Remove markdown bold
                texto = linha.replace('**', '<b>').replace('**', '</b>')
                story.append(Paragraph(texto, normal_style))
        else:
            story.append(Spacer(1, 6))
    
    # Nova página para transcrição
    story.append(PageBreak())
    story.append(Paragraph("📝 TRANSCRIÇÃO COMPLETA", subtitle_style))
    story.append(Spacer(1, 12))
    
    # Adiciona transcrição em parágrafos
    paragrafos = transcricao.split('\n\n')
    for paragrafo in paragrafos:
        if paragrafo.strip():
            story.append(Paragraph(paragrafo.strip(), normal_style))
            story.append(Spacer(1, 6))
    
    # Rodapé
    story.append(Spacer(1, 20))
    story.append(Paragraph("_" * 100, normal_style))
    footer_text = "<i>Documento gerado automaticamente por Audio Insights | Powered by OpenAI</i>"
    story.append(Paragraph(footer_text, normal_style))
    
    # Gera PDF
    doc.build(story)
    
    return str(pdf_path)


def enviar_email(destinatario: str, pdf_path: str, nome_arquivo: str, smtp_config: dict):
    """Envia PDF por email"""
    try:
        # Cria mensagem
        msg = MIMEMultipart()
        msg['From'] = smtp_config['email']
        msg['To'] = destinatario
        msg['Subject'] = f"📊 Análise de Reunião - {nome_arquivo}"
        
        # Corpo do email
        corpo = f"""
Olá!

Sua análise de reunião está pronta! 🎉

Arquivo analisado: {nome_arquivo}
Data: {datetime.now().strftime("%d/%m/%Y às %H:%M")}

O PDF com a transcrição completa e os insights está anexo.

---
Este email foi gerado automaticamente pelo Audio Insights.
Powered by OpenAI Whisper + GPT-4
"""
        
        msg.attach(MIMEText(corpo, 'plain'))
        
        # Anexa PDF
        with open(pdf_path, 'rb') as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
        
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename= {Path(pdf_path).name}'
        )
        msg.attach(part)
        
        # Envia email
        server = smtplib.SMTP(smtp_config['servidor'], smtp_config['porta'])
        server.starttls()
        server.login(smtp_config['email'], smtp_config['senha'])
        server.send_message(msg)
        server.quit()
        
        return True
    
    except Exception as e:
        st.error(f"Erro ao enviar email: {str(e)}")
        return False


def main():
    """Função principal da aplicação"""
    
    inicializar_sessao()
    
    # Header
    st.title("🎤 Audio Insights")
    st.markdown("### Transcreva reuniões e receba insights por email")
    st.markdown("---")
    
    # Sidebar - Configurações
    with st.sidebar:
        st.header("⚙️ Configurações")
        
        # OpenAI API Key
        openai_key = st.text_input(
            "OpenAI API Key",
            type="password",
            help="Sua chave de API da OpenAI"
        )
        
        st.markdown("---")
        
        # Configurações de Email
        st.subheader("📧 Configuração de Email")
        
        smtp_servidor = st.text_input(
            "Servidor SMTP",
            value="smtp.gmail.com",
            help="Ex: smtp.gmail.com, smtp.outlook.com"
        )
        
        smtp_porta = st.number_input(
            "Porta SMTP",
            value=587,
            help="Geralmente 587 para TLS"
        )
        
        email_remetente = st.text_input(
            "Seu Email (Remetente)",
            help="Email que enviará os PDFs"
        )
        
        senha_email = st.text_input(
            "Senha do Email",
            type="password",
            help="Senha de app ou senha do email"
        )
        
        st.markdown("---")
        st.markdown("💡 **Dica:** Para Gmail, use uma [senha de app](https://support.google.com/accounts/answer/185833)")
    
    # Área principal
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📁 Upload do Áudio")
        
        audio_file = st.file_uploader(
            "Selecione o arquivo de áudio",
            type=['mp3', 'mp4', 'mpeg', 'mpga', 'm4a', 'wav', 'webm'],
            help="Formatos suportados: MP3, M4A, WAV, WebM"
        )
        
        if audio_file:
            st.success(f"✅ Arquivo carregado: {audio_file.name}")
            
            # Mostra informações do arquivo
            file_size = len(audio_file.getvalue()) / (1024 * 1024)
            st.info(f"📊 Tamanho: {file_size:.2f} MB")
            
            # Player de áudio
            st.audio(audio_file)
    
    with col2:
        st.subheader("📧 Email de Destino")
        
        email_destino = st.text_input(
            "Digite seu email",
            placeholder="seu@email.com",
            help="O PDF será enviado para este email"
        )
        
        if email_destino:
            st.success(f"✅ Email: {email_destino}")
    
    st.markdown("---")
    
    # Botão de processar
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    
    with col_btn2:
        processar = st.button(
            "🚀 Processar e Enviar por Email",
            type="primary",
            use_container_width=True
        )
    
    # Processamento
    if processar:
        # Validações
        if not openai_key:
            st.error("❌ Por favor, insira sua OpenAI API Key na barra lateral")
            return
        
        if not audio_file:
            st.error("❌ Por favor, faça upload de um arquivo de áudio")
            return
        
        if not email_destino:
            st.error("❌ Por favor, insira o email de destino")
            return
        
        if not email_remetente or not senha_email:
            st.error("❌ Por favor, configure o email remetente na barra lateral")
            return
        
        # Processa
        with st.spinner("🎤 Transcrevendo áudio..."):
            transcricao = transcrever_audio(audio_file, openai_key)
            
            if not transcricao:
                return
            
            st.session_state.transcricao = transcricao
            st.success("✅ Transcrição concluída!")
        
        with st.spinner("🧠 Analisando com IA..."):
            analise = analisar_com_ia(transcricao, openai_key)
            
            if not analise:
                return
            
            st.session_state.analise = analise
            st.success("✅ Análise concluída!")
        
        with st.spinner("📄 Gerando PDF..."):
            pdf_path = gerar_pdf(audio_file.name, transcricao, analise)
            st.session_state.pdf_path = pdf_path
            st.success("✅ PDF gerado!")
        
        with st.spinner("📧 Enviando por email..."):
            smtp_config = {
                'servidor': smtp_servidor,
                'porta': smtp_porta,
                'email': email_remetente,
                'senha': senha_email
            }
            
            sucesso = enviar_email(email_destino, pdf_path, audio_file.name, smtp_config)
            
            if sucesso:
                st.success(f"✅ Email enviado com sucesso para {email_destino}!")
                st.balloons()
                st.session_state.processado = True
            else:
                st.error("❌ Erro ao enviar email. Verifique as configurações SMTP.")
    
    # Mostra resultados se já processou
    if st.session_state.processado:
        st.markdown("---")
        st.subheader("📊 Resultados")
        
        # Tabs para visualização
        tab1, tab2, tab3 = st.tabs(["📝 Transcrição", "🧠 Análise", "📄 Download PDF"])
        
        with tab1:
            st.text_area(
                "Transcrição Completa",
                value=st.session_state.transcricao,
                height=400
            )
        
        with tab2:
            st.markdown(st.session_state.analise)
        
        with tab3:
            if st.session_state.pdf_path:
                with open(st.session_state.pdf_path, 'rb') as pdf_file:
                    st.download_button(
                        label="📥 Baixar PDF",
                        data=pdf_file,
                        file_name=Path(st.session_state.pdf_path).name,
                        mime="application/pdf",
                        use_container_width=True
                    )
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: gray;'>"
        "Desenvolvido com ❤️ | Powered by Clayton and OpenAI"
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()

