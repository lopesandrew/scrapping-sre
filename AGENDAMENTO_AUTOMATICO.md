# Guia: Agendamento Automático no Windows

## 📅 Configuração do Task Scheduler

### 1. Script de Atualização Diária

Criar arquivo `atualizar_base_cvm.py`:

```python
"""
Script de atualização diária da base de ofertas CVM
"""
import pandas as pd
import requests
from io import BytesIO
import zipfile
from datetime import datetime
import logging

# Configuração de log
logging.basicConfig(
    filename='C:\\path\\to\\logs\\cvm_atualizacao.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def atualizar_base():
    try:
        logging.info("Iniciando atualização da base CVM...")
        
        # Download dos dados
        url = "https://dados.cvm.gov.br/dados/OFERTA/DISTRIB/DADOS/oferta_distribuicao.zip"
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        
        # Extrair e processar
        with zipfile.ZipFile(BytesIO(response.content)) as z:
            with z.open('oferta_distribuicao.csv') as f:
                df_cvm = pd.read_csv(f, encoding='latin-1', sep=';', low_memory=False)
        
        # Salvar com timestamp
        data_hoje = datetime.now().strftime('%Y%m%d')
        arquivo_saida = f"C:\\path\\to\\data\\ofertas_cvm_{data_hoje}.xlsx"
        
        df_cvm.to_excel(arquivo_saida, index=False)
        
        logging.info(f"Base atualizada com sucesso: {len(df_cvm)} ofertas")
        logging.info(f"Arquivo salvo: {arquivo_saida}")
        
        # (OPCIONAL) Integrar com base existente
        # df_atual = pd.read_excel('C:\\path\\to\\base_atual.xlsx')
        # df_merged = merge_logic(df_atual, df_cvm)
        # df_merged.to_excel('C:\\path\\to\\base_atual.xlsx', index=False)
        
        return True
        
    except Exception as e:
        logging.error(f"Erro na atualização: {str(e)}")
        return False

if __name__ == "__main__":
    sucesso = atualizar_base()
    exit(0 if sucesso else 1)
```

### 2. Arquivo .bat para execução

Criar `run_cvm_update.bat`:

```batch
@echo off
cd C:\path\to\project
python atualizar_base_cvm.py

REM Opcional: enviar email de notificação
REM python send_notification.py
```

### 3. Configurar Task Scheduler

**Passo a passo:**

1. Abrir **Task Scheduler** (Win + R, digite `taskschd.msc`)

2. Clicar em **"Create Basic Task"** (Criar Tarefa Básica)

3. **Nome:** "Atualização CVM Ofertas Públicas"
   **Descrição:** "Download diário dos dados de ofertas públicas da CVM"

4. **Trigger:** Daily (Diariamente)
   - **Horário:** 08:00 AM (após atualização do portal)
   - **Recur every:** 1 day

5. **Action:** Start a program (Iniciar um programa)
   - **Program/script:** `C:\path\to\project\run_cvm_update.bat`
   - **Start in:** `C:\path\to\project`

6. **Conditions:**
   - ✅ Start only if the computer is on AC power
   - ✅ Start the task even if on batteries
   - ✅ Wake the computer to run this task

7. **Settings:**
   - ✅ Run task as soon as possible after scheduled start is missed
   - ✅ If the task fails, restart every: 10 minutes
   - Attempt to restart up to: 3 times

8. Clicar em **"Finish"**

### 4. Testar agendamento

No Task Scheduler:
- Localizar a tarefa criada
- Clicar com botão direito → **"Run"**
- Verificar log de execução

---

## 🐧 Alternativa: Cron (Linux/Mac)

Editar crontab:
```bash
crontab -e
```

Adicionar linha:
```bash
0 8 * * * cd /path/to/project && python3 atualizar_base_cvm.py
```

Formato: `minuto hora dia mês dia_da_semana comando`
- `0 8 * * *` = Todo dia às 08:00

---

## ☁️ Alternativa: GitHub Actions (Cloud)

Criar `.github/workflows/update_cvm.yml`:

```yaml
name: Atualização CVM

on:
  schedule:
    - cron: '0 8 * * *'  # Diariamente às 08:00 UTC
  workflow_dispatch:  # Permite execução manual

jobs:
  update:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        pip install pandas requests openpyxl
    
    - name: Run update script
      run: |
        python atualizar_base_cvm.py
    
    - name: Upload artifact
      uses: actions/upload-artifact@v3
      with:
        name: ofertas-cvm
        path: ofertas_cvm_*.xlsx
```

**Vantagens GitHub Actions:**
- ✅ Gratuito para repositórios públicos
- ✅ Não depende de máquina local ligada
- ✅ Histórico de execuções
- ✅ Notificações de falha

---

## 📧 Notificação por Email (Opcional)

Adicionar ao script:

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def enviar_email_notificacao(sucesso, mensagem):
    """Envia email com resultado da atualização"""
    
    smtp_server = "smtp.gmail.com"
    porta = 587
    remetente = "seu_email@gmail.com"
    senha = "sua_senha_app"  # Usar senha de app do Gmail
    destinatario = "seu_email@bocom.com.br"
    
    assunto = f"CVM Update: {'✓ Sucesso' if sucesso else '✗ Falha'}"
    
    msg = MIMEMultipart()
    msg['From'] = remetente
    msg['To'] = destinatario
    msg['Subject'] = assunto
    
    corpo = f"""
    Status: {'Concluído com sucesso' if sucesso else 'Falha na execução'}
    
    Detalhes:
    {mensagem}
    
    Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M')}
    """
    
    msg.attach(MIMEText(corpo, 'plain'))
    
    try:
        server = smtplib.SMTP(smtp_server, porta)
        server.starttls()
        server.login(remetente, senha)
        server.send_message(msg)
        server.quit()
        logging.info("Email de notificação enviado")
    except Exception as e:
        logging.error(f"Erro ao enviar email: {str(e)}")
```

---

## 🔍 Monitoramento e Logs

### Estrutura de Log Sugerida:

```
logs/
├── cvm_atualizacao.log          # Log principal
├── cvm_atualizacao_20241208.log # Log diário (rotativo)
└── erros.log                     # Apenas erros críticos
```

### Exemplo de Log:

```
2024-12-08 08:00:00 - INFO - Iniciando atualização da base CVM...
2024-12-08 08:00:15 - INFO - Download concluído (15.2 MB)
2024-12-08 08:00:45 - INFO - Base atualizada com sucesso: 3,847 ofertas
2024-12-08 08:00:46 - INFO - Arquivo salvo: ofertas_cvm_20241208.xlsx
```

---

## ⚡ Checklist de Implantação

- [ ] Criar script de atualização
- [ ] Testar script manualmente
- [ ] Configurar paths absolutos
- [ ] Criar diretórios (data/, logs/)
- [ ] Configurar Task Scheduler / Cron
- [ ] Testar execução agendada
- [ ] Configurar notificações (opcional)
- [ ] Documentar processo para equipe
- [ ] Definir política de backup dos arquivos
- [ ] Estabelecer procedimento para falhas

---

## 🛠️ Troubleshooting

### Problema: Script não executa no horário
**Solução:**
- Verificar se computador está ligado
- Verificar configurações de energia
- Habilitar "Wake computer to run task"

### Problema: Erro de permissão
**Solução:**
- Executar Task Scheduler como administrador
- Verificar permissões de escrita nos diretórios

### Problema: Download falha
**Solução:**
- Verificar conexão com internet
- Adicionar retry logic no script
- Verificar proxy corporativo

### Problema: Arquivo Excel corrompido
**Solução:**
- Validar dados antes de salvar
- Manter backup do arquivo anterior
- Usar try/except ao salvar
