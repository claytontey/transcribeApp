# 📧 Guia: Como Configurar Email para Envio Automático

Este guia ensina como configurar seu email para que a aplicação possa enviar PDFs automaticamente.

---

## 🔐 Importante: Segurança

**NUNCA use sua senha normal de email diretamente!**

Use **senhas de app** (app passwords) que são mais seguras e podem ser revogadas a qualquer momento.

---

## 📮 Gmail (Recomendado)

### Passo 1: Ativar Verificação em 2 Etapas

1. Acesse [myaccount.google.com/security](https://myaccount.google.com/security)
2. Role até "Como fazer login no Google"
3. Clique em "Verificação em duas etapas"
4. Siga as instruções para ativar

### Passo 2: Gerar Senha de App

1. Acesse [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
2. Pode pedir para fazer login novamente
3. Em "Selecionar app", escolha **"Outro (nome personalizado)"**
4. Digite: **"Audio Insights"**
5. Clique em **"Gerar"**
6. **Copie a senha de 16 caracteres** que aparece
7. Use essa senha na aplicação (não a senha normal!)

### Passo 3: Configurar na Aplicação

Na barra lateral do Streamlit:

```
Servidor SMTP: smtp.gmail.com
Porta SMTP: 587
Seu Email: seu.email@gmail.com
Senha do Email: [cole a senha de app de 16 caracteres]
```

✅ **Pronto!** Seu Gmail está configurado.

---

## 📧 Outlook / Hotmail

### Configuração Simples

O Outlook permite usar a senha normal (mas senha de app é mais seguro).

### Passo 1: Configurar na Aplicação

```
Servidor SMTP: smtp-mail.outlook.com
Porta SMTP: 587
Seu Email: seu.email@outlook.com (ou @hotmail.com)
Senha do Email: sua senha normal
```

### Passo 2 (Opcional): Usar Senha de App

1. Acesse [account.microsoft.com/security](https://account.microsoft.com/security)
2. Ative verificação em duas etapas
3. Gere uma senha de app
4. Use essa senha em vez da normal

✅ **Pronto!** Seu Outlook está configurado.

---

## 📮 Yahoo Mail

### Configuração

```
Servidor SMTP: smtp.mail.yahoo.com
Porta SMTP: 587
Seu Email: seu.email@yahoo.com
Senha do Email: [senha de app]
```

### Gerar Senha de App

1. Acesse [login.yahoo.com/account/security](https://login.yahoo.com/account/security)
2. Clique em "Gerar senha de app"
3. Selecione "Outro app"
4. Digite "Audio Insights"
5. Copie a senha gerada

---

## 📧 ProtonMail

### Configuração

```
Servidor SMTP: smtp.protonmail.com
Porta SMTP: 587
Seu Email: seu.email@protonmail.com
Senha do Email: [senha normal ou bridge password]
```

**Nota**: ProtonMail pode requerer o ProtonMail Bridge para SMTP.

---

## 🏢 Email Corporativo

### Configuração Genérica

Pergunte ao seu departamento de TI:

1. **Servidor SMTP**: Geralmente `smtp.suaempresa.com`
2. **Porta**: Normalmente 587 ou 465
3. **Autenticação**: Seu email e senha corporativos

### Exemplo: Office 365 (Microsoft)

```
Servidor SMTP: smtp.office365.com
Porta SMTP: 587
Seu Email: voce@suaempresa.com
Senha do Email: senha corporativa
```

---

## 🧪 Testar Configuração

### Teste Rápido com Python

Crie um arquivo `testar_email.py`:

```python
import smtplib
from email.mime.text import MIMEText

# CONFIGURE AQUI
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL = "seu.email@gmail.com"
SENHA = "sua senha de app"
DESTINATARIO = "seu.email@gmail.com"

try:
    # Conecta
    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()
    server.login(EMAIL, SENHA)
    
    # Envia email de teste
    msg = MIMEText("Teste de configuração SMTP - Audio Insights")
    msg['Subject'] = "Teste SMTP"
    msg['From'] = EMAIL
    msg['To'] = DESTINATARIO
    
    server.send_message(msg)
    server.quit()
    
    print("✅ Email enviado com sucesso!")
    print("Configuração está correta.")
    
except Exception as e:
    print(f"❌ Erro: {str(e)}")
    print("\nVerifique:")
    print("- Servidor SMTP correto")
    print("- Porta correta")
    print("- Email correto")
    print("- Senha de app (não senha normal)")
```

Execute:
```bash
python testar_email.py
```

Se receber o email, está tudo certo! ✅

---

## 🐛 Problemas Comuns

### Erro: "Username and Password not accepted"

**Causa**: Senha incorreta ou não é senha de app

**Solução**:
1. Verifique se está usando **senha de app** (não senha normal)
2. Gere uma nova senha de app
3. Copie e cole com cuidado (sem espaços)

### Erro: "Connection refused"

**Causa**: Servidor ou porta incorretos

**Solução**:
1. Verifique o servidor SMTP
2. Verifique a porta (geralmente 587)
3. Tente porta 465 se 587 não funcionar

### Erro: "SMTP AUTH extension not supported"

**Causa**: Servidor não suporta autenticação

**Solução**:
1. Verifique se o servidor está correto
2. Alguns servidores requerem SSL (porta 465)

### Gmail: "Less secure app access"

**Causa**: Gmail bloqueou o acesso

**Solução**:
1. **NÃO** ative "acesso a apps menos seguros" (inseguro!)
2. Use **senha de app** em vez disso (seguro!)

### Outlook: "Too many login attempts"

**Causa**: Muitas tentativas falhadas

**Solução**:
1. Aguarde 15 minutos
2. Verifique se email e senha estão corretos
3. Tente novamente

---

## 🔒 Dicas de Segurança

### ✅ Faça

- Use senhas de app quando possível
- Revogue senhas de app que não usa mais
- Use verificação em 2 etapas
- Mantenha suas credenciais privadas

### ❌ Não Faça

- Não compartilhe senhas de app
- Não use senha normal do email
- Não desative verificação em 2 etapas
- Não commit senhas no Git

---

## 📊 Comparação de Provedores

| Provedor | Facilidade | Segurança | Limite Diário | Recomendado |
|----------|-----------|-----------|---------------|-------------|
| **Gmail** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 500 emails | ✅ **Sim** |
| **Outlook** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 300 emails | ✅ **Sim** |
| **Yahoo** | ⭐⭐⭐ | ⭐⭐⭐⭐ | 100 emails | ⚠️ OK |
| **ProtonMail** | ⭐⭐ | ⭐⭐⭐⭐⭐ | Varia | ⚠️ Complexo |
| **Corporativo** | ⭐⭐ | ⭐⭐⭐⭐ | Varia | ⚠️ Depende |

**Recomendação**: Use Gmail ou Outlook para facilidade e confiabilidade.

---

## 🎓 Alternativas ao Email

Se não quiser configurar email, você pode:

### Opção 1: Apenas Download

Comente o código de envio de email e use apenas o download direto do PDF na interface.

### Opção 2: Serviços de Email

Use serviços como:
- **SendGrid**: 100 emails/dia grátis
- **Mailgun**: 5.000 emails/mês grátis
- **AWS SES**: $0.10 por 1.000 emails

### Opção 3: Salvar em Cloud

Salve o PDF no Google Drive, Dropbox, etc. em vez de enviar por email.

---

## 📞 Precisa de Ajuda?

Se ainda tiver problemas:

1. Verifique a documentação do seu provedor de email
2. Teste com o script `testar_email.py` acima
3. Verifique se firewall não está bloqueando
4. Tente de outra rede (WiFi diferente)

---

**Desenvolvido por Manus AI** | Outubro 2025

Configuração segura. Envio confiável. 📧

