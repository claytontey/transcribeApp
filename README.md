# 🎤 Audio Insights - Interface Web com Streamlit

Interface web moderna para transcrever áudios, gerar insights e enviar PDFs por email.

---

## ✨ Características

- 🌐 **Interface Web Moderna**: Bonita e fácil de usar
- 📤 **Upload de Áudio**: Arraste e solte ou selecione
- 🎧 **Player Integrado**: Ouça o áudio antes de processar
- 📊 **Análise Completa**: Transcrição + Insights com IA
- 📄 **PDF Profissional**: Documento formatado e organizado
- 📧 **Envio Automático**: Receba o PDF por email
- 💾 **Download Direto**: Baixe o PDF na hora também

---

## 📋 Requisitos

- Python 3.8+
- Conta OpenAI (API Key)
- Email configurado para envio (Gmail, Outlook, etc.)

---

## 🚀 Instalação

### 1. Instalar Dependências

```bash
pip install -r requirements.txt
```

Isso instala:
- `streamlit` - Framework web
- `openai` - API da OpenAI
- `reportlab` - Geração de PDF

### 2. Executar a Aplicação

```bash
streamlit run app.py
```

A aplicação abrirá automaticamente no navegador em `http://localhost:8501`

---

## 💻 Como Usar

### Passo 1: Configurar na Barra Lateral

#### OpenAI API Key
1. Acesse [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Crie uma nova chave
3. Cole na barra lateral

#### Configurações de Email

**Para Gmail:**
- Servidor SMTP: `smtp.gmail.com`
- Porta: `587`
- Email: seu email do Gmail
- Senha: **Senha de app** (não a senha normal!)
  - Gere em: [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)

**Para Outlook/Hotmail:**
- Servidor SMTP: `smtp-mail.outlook.com`
- Porta: `587`
- Email: seu email do Outlook
- Senha: senha normal do Outlook

**Para outros provedores:**
- Consulte a documentação do seu provedor de email

### Passo 2: Fazer Upload do Áudio

1. Clique em "Browse files" ou arraste o arquivo
2. Formatos aceitos: MP3, M4A, WAV, WebM
3. Tamanho máximo: 25 MB

### Passo 3: Inserir Email de Destino

Digite o email onde você quer receber o PDF.

### Passo 4: Processar

Clique em "🚀 Processar e Enviar por Email"

**O que acontece:**
1. ⏱️ Transcrição (~30 segundos)
2. ⏱️ Análise com IA (~20 segundos)
3. ⏱️ Geração do PDF (~5 segundos)
4. ⏱️ Envio por email (~5 segundos)

**Total: ~1 minuto**

### Passo 5: Visualizar e Baixar

Após processar, você pode:
- Ver a transcrição completa
- Ler a análise
- Baixar o PDF diretamente

---

## 📄 Conteúdo do PDF

O PDF gerado contém:

### Página 1: Análise e Insights
- 📊 Resumo Executivo
- 👥 Participantes
- 📋 Tópicos Principais
- ✅ Decisões Tomadas
- ✏️ Ações e Tarefas
- ⚠️ Pontos Importantes
- ➡️ Próximos Passos
- 💡 Observações

### Página 2+: Transcrição Completa
- Texto integral do áudio

**Formatação profissional** com cores, espaçamento e organização.

---

## 🔐 Segurança e Privacidade

### Dados Locais
- Áudios são processados localmente
- Arquivos temporários são deletados após uso
- PDFs ficam salvos apenas na pasta `resultados/`

### APIs Externas
- OpenAI: Processa transcrição e análise
- Servidor SMTP: Envia email

### Credenciais
- API Keys e senhas **não são salvas**
- Você precisa inserir a cada sessão
- Ou configure variáveis de ambiente (mais seguro)

---

## 💰 Custos

### OpenAI API
Mesmo custo da versão simples:

| Duração | Custo |
|---------|-------|
| 5 min | $0.13 |
| 15 min | $0.24 |
| 30 min | $0.38 |
| 1 hora | $0.66 |

### Email
- Gmail: Gratuito (limite de 500 emails/dia)
- Outlook: Gratuito (limite de 300 emails/dia)
- Outros: Consulte seu provedor

### Hospedagem (Opcional)
Se quiser deixar online 24/7:
- Streamlit Cloud: Gratuito (com limitações)
- Heroku: $7/mês
- DigitalOcean: $12/mês

---

## 🎨 Personalização

### Mudar Cores e Tema

Crie um arquivo `.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"
```

### Modificar Análise

Edite o `prompt_sistema` no arquivo `app.py` (linha ~85) para personalizar os insights extraídos.

### Customizar PDF

Edite a função `gerar_pdf()` (linha ~155) para mudar:
- Cores
- Fontes
- Layout
- Conteúdo

---

## 🌐 Deploy Online (Opcional)

### Opção 1: Streamlit Cloud (Gratuito)

1. Faça upload do código no GitHub
2. Acesse [share.streamlit.io](https://share.streamlit.io)
3. Conecte seu repositório
4. Deploy automático!

**Limitações:**
- Recursos limitados
- Pode ficar lento com arquivos grandes

### Opção 2: Heroku

```bash
# Instale Heroku CLI
heroku login
heroku create seu-app-audio-insights

# Crie Procfile
echo "web: streamlit run app.py --server.port=$PORT" > Procfile

# Deploy
git init
git add .
git commit -m "Initial commit"
git push heroku main
```

### Opção 3: DigitalOcean/AWS

Siga o guia de deploy em produção que criei anteriormente.

---

## 🐛 Solução de Problemas

### Erro: "No module named 'streamlit'"

```bash
pip install streamlit
```

### Erro ao enviar email (Gmail)

**Problema**: Gmail bloqueia apps menos seguros

**Solução**: Use senha de app
1. Ative verificação em 2 etapas
2. Gere senha de app em [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
3. Use essa senha (não a senha normal)

### Erro: "File too large"

**Solução**: Comprima o áudio antes

```bash
ffmpeg -i audio_grande.m4a -b:a 64k audio_comprimido.mp3
```

### Streamlit não abre no navegador

```bash
streamlit run app.py --server.port 8502
```

Acesse manualmente: `http://localhost:8502`

### PDF não está formatado corretamente

Verifique se instalou o reportlab:
```bash
pip install reportlab
```

---

## 📱 Uso em Dispositivos Móveis

### Acessar de Outro Dispositivo

1. Descubra o IP do seu computador:
   ```bash
   # Mac/Linux
   ifconfig | grep inet
   
   # Windows
   ipconfig
   ```

2. Execute com IP público:
   ```bash
   streamlit run app.py --server.address 0.0.0.0
   ```

3. Acesse do celular:
   ```
   http://SEU_IP:8501
   ```

**Nota**: Ambos os dispositivos devem estar na mesma rede WiFi.

---

## 🎓 Exemplos de Uso

### Exemplo 1: Reunião de Equipe

1. Grave a reunião no celular
2. Transfira para o computador
3. Acesse a interface web
4. Upload do áudio
5. Insira seu email
6. Processe
7. Receba o PDF por email em 1 minuto!

### Exemplo 2: Aula ou Palestra

1. Grave a aula
2. Processe na interface
3. Receba transcrição + resumo
4. Compartilhe o PDF com colegas

### Exemplo 3: Entrevista

1. Grave a entrevista
2. Processe
3. Tenha um relatório profissional
4. Envie para o RH

---

## 🔄 Comparação com Outras Versões

| Recurso | Terminal | GUI (Tkinter) | **Web (Streamlit)** |
|---------|----------|---------------|---------------------|
| Interface | ❌ Linha de comando | ✅ Desktop | ✅ **Web moderna** |
| Facilidade | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Email | ❌ | ❌ | ✅ **Automático** |
| PDF | ❌ Markdown | ❌ Markdown | ✅ **PDF profissional** |
| Acesso Remoto | ❌ | ❌ | ✅ **Sim** |
| Player de Áudio | ❌ | ❌ | ✅ **Integrado** |
| Visualização | ❌ | ⚠️ Básica | ✅ **Completa** |
| Deploy Online | ❌ | ❌ | ✅ **Fácil** |

**Vencedor**: Streamlit! 🏆

---

## 📊 Estrutura do Projeto

```
audio-insights-streamlit/
├── app.py                 # Aplicação principal
├── requirements.txt       # Dependências
├── README.md             # Este arquivo
├── temp/                 # Arquivos temporários
└── resultados/           # PDFs gerados
    └── analise_reuniao_20251014_143022.pdf
```

---

## 🚀 Próximos Passos

### Melhorias Futuras (Opcional)

1. **Banco de Dados**: Salvar histórico de análises
2. **Autenticação**: Login de usuários
3. **Múltiplos Arquivos**: Processar vários áudios de uma vez
4. **Integração com Calendários**: Criar eventos automaticamente
5. **Análise Comparativa**: Comparar reuniões ao longo do tempo
6. **Dashboard**: Visualizar métricas e estatísticas
7. **API REST**: Permitir integração com outros sistemas

---

## 📞 Suporte

- **Streamlit Docs**: [docs.streamlit.io](https://docs.streamlit.io)
- **ReportLab Docs**: [reportlab.com/docs](https://www.reportlab.com/docs/reportlab-userguide.pdf)
- **OpenAI API**: [platform.openai.com/docs](https://platform.openai.com/docs)

---

## 📝 Licença

Código aberto. Use livremente!

---

**Desenvolvido por Manus AI** | Outubro 2025

Interface moderna. PDF profissional. Email automático. 🚀

