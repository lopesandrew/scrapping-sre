# 🚀 Guia Rápido - CVM Automation

## 📦 Instalação Inicial

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Configurar ambiente
python setup.py

# 3. Testar conexão
python scripts/teste_rapido_cvm.py
```

---

## ⚡ Comandos Principais

### Baixar Base Completa
```bash
python scripts/cvm_ofertas_automacao.py
```

### Teste Rápido
```bash
python scripts/teste_rapido_cvm.py
```

### Setup do Ambiente
```bash
python setup.py
```

---

## 🐍 Snippets Úteis

### Download e Busca Básica
```python
from scripts.cvm_ofertas_automacao import download_ofertas_cvm, buscar_oferta_por_codigo

# Baixar dados
df = download_ofertas_cvm()

# Buscar oferta específica
oferta = buscar_oferta_por_codigo(df, 21629)
print(oferta)
```

### Filtrar por Tipo e Data
```python
from scripts.cvm_ofertas_automacao import filtrar_ofertas_recentes

# CRIs dos últimos 30 dias
cris = filtrar_ofertas_recentes(df, tipo_valor_mobiliario='CRI', dias=30)
cris.to_excel('cris_recentes.xlsx', index=False)
```

### Exportar Colunas Específicas
```python
# Selecionar apenas colunas relevantes
colunas_interesse = [
    'Codigo_Oferta',
    'Tipo_Valor_Mobiliario',
    'Nome_Emissor',
    'Data_Registro',
    'Situacao',
    'Volume_Financeiro'
]

df_resumido = df[colunas_interesse]
df_resumido.to_excel('ofertas_resumo.xlsx', index=False)
```

### Filtros Avançados
```python
# CRIs de 2024 com volume > 100M
filtro = (
    (df['Tipo_Valor_Mobiliario'] == 'CRI') &
    (df['Data_Registro'].str.contains('2024')) &
    (df['Volume_Financeiro'] > 100000000)
)
cris_grandes = df[filtro]
```

---

## 📊 Análises Comuns

### Contagem por Tipo
```python
df['Tipo_Valor_Mobiliario'].value_counts()
```

### Volume Total por Tipo
```python
df.groupby('Tipo_Valor_Mobiliario')['Volume_Financeiro'].sum()
```

### Ofertas por Emissor
```python
df['Nome_Emissor'].value_counts().head(20)
```

### Timeline de Registros
```python
df['Data_Registro'] = pd.to_datetime(df['Data_Registro'])
registros_por_mes = df.groupby(df['Data_Registro'].dt.to_period('M')).size()
```

---

## 🔧 Troubleshooting Rápido

### Erro de encoding
```python
df = pd.read_csv('arquivo.csv', encoding='latin-1', sep=';')
```

### Timeout no download
```python
response = requests.get(url, timeout=120)  # Aumentar timeout
```

### Coluna não encontrada
```python
# Ver todas as colunas
print(df.columns.tolist())

# Buscar coluna por nome parcial
[col for col in df.columns if 'codigo' in col.lower()]
```

### Limpar dados
```python
# Remover linhas duplicadas
df = df.drop_duplicates(subset='Codigo_Oferta')

# Remover valores nulos em coluna específica
df = df[df['Codigo_Oferta'].notna()]
```

---

## 📅 Agendamento (Windows)

### Criar Tarefa Agendada
```batch
# 1. Criar arquivo .bat
@echo off
cd C:\path\to\project
python scripts/atualizar_base_cvm.py

# 2. Task Scheduler
# Ação: Iniciar programa
# Programa: C:\path\to\run_update.bat
# Gatilho: Diário às 08:00
```

---

## 🔍 Exploração de Dados

### Informações Gerais
```python
# Shape do DataFrame
print(f"Linhas: {len(df)}, Colunas: {len(df.columns)}")

# Tipos de dados
df.dtypes

# Estatísticas descritivas
df.describe()

# Valores únicos em coluna
df['Tipo_Valor_Mobiliario'].unique()

# Valores nulos
df.isnull().sum()
```

### Primeiras/Últimas Linhas
```python
df.head(10)     # Primeiras 10
df.tail(10)     # Últimas 10
df.sample(10)   # 10 aleatórias
```

---

## 💾 Exportação

### Excel
```python
df.to_excel('dados.xlsx', index=False)
```

### Excel com múltiplas abas
```python
with pd.ExcelWriter('relatorio.xlsx') as writer:
    df_cri.to_excel(writer, sheet_name='CRIs', index=False)
    df_deb.to_excel(writer, sheet_name='Debêntures', index=False)
    df_cra.to_excel(writer, sheet_name='CRAs', index=False)
```

### CSV
```python
df.to_csv('dados.csv', index=False, encoding='utf-8-sig', sep=';')
```

---

## 🔗 Links Úteis

- **Portal CVM:** https://dados.cvm.gov.br/
- **Documentação Pandas:** https://pandas.pydata.org/docs/
- **Python Requests:** https://requests.readthedocs.io/

---

## 📝 Notas

- Base atualizada diariamente pela CVM (geralmente após 18h)
- Arquivo ZIP contém ~3-5 mil ofertas
- Download: ~15-20 MB
- Processamento: ~5-10 segundos
- Encoding: `latin-1` (padrão CVM)
- Separador CSV: `;` (ponto e vírgula)

---

## 🆘 Suporte

**Comandos de diagnóstico:**

```python
# Verificar versões
import pandas as pd
import requests
print(f"Pandas: {pd.__version__}")
print(f"Requests: {requests.__version__}")

# Testar conexão
import requests
r = requests.get('https://dados.cvm.gov.br/')
print(f"Status: {r.status_code}")

# Verificar estrutura de diretórios
import os
print(os.listdir('.'))
```

---

**Última atualização:** 08/12/2024
