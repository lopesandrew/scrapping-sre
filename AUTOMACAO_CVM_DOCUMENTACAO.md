# Automação de Coleta de Ofertas Públicas da CVM

**Data:** 08/12/2024  
**Objetivo:** Automatizar alimentação diária da base Excel com dados de ofertas públicas

---

## 📋 Resumo Executivo

**Status:** ✅ **VIÁVEL** - Automação 100% possível  
**Melhor abordagem:** Portal Dados Abertos da CVM (API/CSV)  
**Complexidade:** 🟢 Baixa (simples requests + pandas)

---

## 🎯 Descobertas

### 1. Site SRE da CVM
- **URL consultada:** `https://web.cvm.gov.br/sre-publico-cvm/#/oferta-publica/21629`
- **Tecnologia:** Single Page Application (SPA) com JavaScript
- **Problema:** Web scraping tradicional não funciona (precisa executar JS)
- **Solução alternativa:** Selenium (mais complexo e instável)

### 2. Portal Dados Abertos da CVM ⭐ **RECOMENDADO**
- **URL:** https://dados.cvm.gov.br/
- **Arquivo principal:** `oferta_distribuicao.csv` (compactado em ZIP)
- **Frequência de atualização:** **DIÁRIA** ✅
- **Última atualização verificada:** 08/12/2025
- **Formato:** CSV (separado por ponto-e-vírgula)
- **Encoding:** Latin-1

#### Conteúdo Disponível
- Ofertas registradas na CVM (ICVM 400 ou RCVM 160)
- Ofertas com registro automático (ICVM 555)
- Ofertas com esforços restritos (ICVM 476) encerradas
- Todas as classes: CRI, CRA, Debêntures, Ações, Fundos, etc.

#### Colunas Principais (conforme documentação)
- **Identificação:** Código da oferta, Tipo de valor mobiliário
- **Datas:** Data de registro, Data de início da oferta
- **Emissor:** Nome, CNPJ, Tipo societário
- **Registro:** Modalidade de registro/dispensa
- **Status/Situação:** Situação da oferta
- **Valores:** Volume, quantidade distribuída
- **Coordenadores:** Instituições participantes
- **Comunicados:** Último comunicado, data

---

## 🔧 Implementação

### Opção 1: Portal Dados Abertos (RECOMENDADA)

**Vantagens:**
- ✅ Oficial e confiável
- ✅ Atualização diária automática
- ✅ Dados estruturados e completos
- ✅ Não depende de estrutura HTML do site
- ✅ Sem risco de bloqueio por bot
- ✅ Performance excelente
- ✅ Simples de implementar

**Desvantagens:**
- ⚠️ Precisa entender a estrutura das colunas (dicionário de dados)
- ⚠️ Dados do dia anterior (não tempo real)

**Código básico:**
```python
import pandas as pd
import requests
from io import BytesIO
import zipfile

url = "https://dados.cvm.gov.br/dados/OFERTA/DISTRIB/DADOS/oferta_distribuicao.zip"
response = requests.get(url)

with zipfile.ZipFile(BytesIO(response.content)) as z:
    with z.open('oferta_distribuicao.csv') as f:
        df = pd.read_csv(f, encoding='latin-1', sep=';', low_memory=False)

# Filtrar por código, data, tipo, etc.
oferta_21629 = df[df['Codigo_Oferta'] == 21629]  # Ajustar nome da coluna
```

### Opção 2: Scraping com Selenium

**Vantagens:**
- ✅ Acesso aos dados exatos do site SRE
- ✅ Pode capturar informações em tempo real

**Desvantagens:**
- ❌ Complexo de implementar e manter
- ❌ Depende da estrutura HTML do site
- ❌ Mais lento (carrega navegador)
- ❌ Pode ser bloqueado/detectado
- ❌ Requer ChromeDriver ou geckodriver
- ❌ Consome mais recursos

**Quando usar:**
- Apenas se precisar de informações que NÃO existem no Portal Dados Abertos
- Se precisar de dados em tempo real (não pode esperar atualização diária)

---

## 🚀 Próximos Passos

### 1. Teste Inicial (Hoje)
```bash
# Instalar dependências
pip install pandas requests openpyxl

# Executar script de teste
python cvm_ofertas_automacao.py
```

### 2. Validação da Base
- ✅ Verificar se todas as colunas necessárias estão presentes
- ✅ Comparar com sua base Excel atual
- ✅ Identificar campos de interesse (Status, Situação, etc.)

### 3. Agendamento Diário
**Opções:**
- **Windows:** Task Scheduler
- **Linux/Mac:** Cron job
- **Cloud:** GitHub Actions, AWS Lambda, Google Cloud Functions

**Exemplo de agendamento (Windows Task Scheduler):**
```
Ação: python C:\path\to\cvm_ofertas_automacao.py
Gatilho: Diariamente às 08:00
```

### 4. Integração com Excel Existente
```python
# Ler base Excel atual
df_atual = pd.read_excel('base_ofertas_atual.xlsx')

# Baixar dados atualizados da CVM
df_cvm = download_ofertas_cvm()

# Atualizar/merge conforme lógica de negócio
df_atualizado = pd.merge(df_atual, df_cvm, on='codigo_oferta', how='left')

# Salvar
df_atualizado.to_excel('base_ofertas_atualizada.xlsx', index=False)
```

---

## 📊 Estrutura Sugerida do Sistema

```
project/
│
├── scripts/
│   ├── cvm_ofertas_automacao.py  # Script principal
│   └── config.py                  # Configurações (paths, colunas, etc.)
│
├── data/
│   ├── raw/                       # CSVs baixados da CVM
│   └── processed/                 # Excel processados
│
├── logs/
│   └── execucoes.log              # Log de execuções
│
└── requirements.txt               # Dependências Python
```

---

## 🔍 Resposta à Pergunta Original

### "Qual é o Status da Oferta 21629?"

**Não consegui acessar diretamente** porque:
1. O site SRE é uma SPA que requer JavaScript
2. Minha ferramenta de web_fetch não executa JS
3. A rede está bloqueando downloads diretos

**MAS a solução é simples:**
1. Baixe o CSV do Portal Dados Abertos (link fornecido)
2. Filtre pela oferta 21629
3. Verifique a coluna de status/situação

**Você conseguirá fazer isso em ~5 linhas de Python** usando o script que criei.

---

## 📚 Recursos Adicionais

### Documentação Oficial CVM
- Portal Dados Abertos: https://dados.cvm.gov.br/
- Dicionário de Dados: Disponível na própria página do dataset
- Novidades: https://dados.cvm.gov.br/pages/novidades

### Alternativas Futuras
- **API CKAN:** O portal usa CKAN, que tem API REST nativa
  - Endpoint base: https://dados.cvm.gov.br/api/3/action/
  - Exemplo: `datastore_search` para queries SQL-like

### Suporte
- Se tiver dúvidas sobre a estrutura dos dados: contato CVM via portal
- Issues técnicas Python: me chame novamente!

---

## ⚙️ Checklist de Implementação

- [ ] Instalar dependências (`pandas`, `requests`, `openpyxl`)
- [ ] Executar script de teste
- [ ] Validar colunas disponíveis vs. necessárias
- [ ] Mapear campos da CVM → campos da base Excel
- [ ] Criar lógica de merge/update
- [ ] Testar pipeline completo
- [ ] Configurar agendamento diário
- [ ] Criar log de execuções
- [ ] Documentar processo para equipe
- [ ] (Opcional) Criar dashboard de monitoramento

---

## 💡 Recomendação Final

**Use o Portal Dados Abertos.** É a solução oficial, confiável e de fácil manutenção.  
Selenium só se for absolutamente necessário (dados não disponíveis no portal).

**Tempo estimado de implementação:** 2-4 horas (incluindo testes e validação)
