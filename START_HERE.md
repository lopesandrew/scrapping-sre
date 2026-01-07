# 📦 PACOTE COMPLETO - Automação CVM

## 🎯 O QUE VOCÊ TEM AQUI

Sistema completo para automatizar coleta de ofertas públicas da CVM, substituindo alimentação manual de Excel.

**Status:** ✅ Pronto para uso  
**Tempo de setup:** ~15 minutos  
**Complexidade:** 🟢 Baixa (apenas Python + pandas)

---

## 📁 ARQUIVOS DO PROJETO

### Scripts Python
| Arquivo | Função | Quando Usar |
|---------|--------|-------------|
| `teste_rapido_cvm.py` | Teste inicial rápido | COMEÇAR AQUI - valida conexão e dados |
| `cvm_ofertas_automacao.py` | Script completo com funções | Uso diário e customizações |
| `setup.py` | Configuração inicial do ambiente | Executar uma vez no início |

### Documentação
| Arquivo | Conteúdo |
|---------|----------|
| `README.md` | Documentação completa do projeto |
| `AUTOMACAO_CVM_DOCUMENTACAO.md` | Análise técnica e recomendações |
| `AGENDAMENTO_AUTOMATICO.md` | Guia de agendamento diário |
| `CHEATSHEET.md` | Comandos úteis e snippets |

### Configuração
| Arquivo | Função |
|---------|--------|
| `requirements.txt` | Dependências Python |
| `.gitignore` | Arquivos a ignorar no Git |

---

## 🚀 COMO COMEÇAR (3 PASSOS)

### 1️⃣ Preparar Ambiente (5 min)
```bash
# Instalar dependências
pip install pandas requests openpyxl

# Configurar projeto
python setup.py
```

### 2️⃣ Testar Sistema (2 min)
```bash
python teste_rapido_cvm.py
```

Isso vai:
- ✅ Baixar base completa da CVM (~15 MB)
- ✅ Mostrar estrutura dos dados
- ✅ Buscar oferta 21629 (exemplo)
- ✅ Gerar Excel de amostra

### 3️⃣ Validar Dados (5 min)
- Abrir `amostra_ofertas_cvm.xlsx` no Excel
- Verificar se tem as colunas que você precisa
- Comparar com sua base atual

---

## 📊 FONTE DOS DADOS

**URL:** https://dados.cvm.gov.br/dados/OFERTA/DISTRIB/DADOS/oferta_distribuicao.zip

**Características:**
- 🔄 Atualizado DIARIAMENTE pela CVM
- 📋 Formato CSV (3.000-5.000 ofertas)
- 📦 Tamanho: ~15-20 MB
- ⚡ Download + processamento: ~20 segundos

**Conteúdo:**
- CRI, CRA, Debêntures, Ações, Fundos, etc.
- Status, datas, emissores, volumes
- Histórico completo desde 2000+

---

## 💡 CASOS DE USO

### 1. Buscar Status de Oferta
```python
from scripts.cvm_ofertas_automacao import download_ofertas_cvm, buscar_oferta_por_codigo

df = download_ofertas_cvm()
oferta = buscar_oferta_por_codigo(df, 21629)
print(f"Status: {oferta['Situacao']}")
```

### 2. Filtrar CRIs Recentes
```python
from scripts.cvm_ofertas_automacao import filtrar_ofertas_recentes

cris = filtrar_ofertas_recentes(df, tipo_valor_mobiliario='CRI', dias=30)
cris.to_excel('cris_recentes.xlsx', index=False)
```

### 3. Atualizar Base Excel
```python
import pandas as pd

# Baixar dados CVM
df_cvm = download_ofertas_cvm()

# Ler base atual
df_base = pd.read_excel('minha_base.xlsx')

# Merge/update (ajustar conforme lógica)
df_atualizado = pd.merge(df_base, df_cvm, on='Codigo_Oferta', how='left')

# Salvar
df_atualizado.to_excel('minha_base_atualizada.xlsx', index=False)
```

---

## ⚙️ AGENDAMENTO AUTOMÁTICO

**Opção recomendada:** Windows Task Scheduler

**Passos:**
1. Criar script `atualizar_base_cvm.py` (ver AGENDAMENTO_AUTOMATICO.md)
2. Criar arquivo .bat para executar
3. Configurar Task Scheduler:
   - Gatilho: Diário às 08:00
   - Ação: Executar .bat
   - ✅ Wake computer to run

**Guia completo:** Ver `AGENDAMENTO_AUTOMATICO.md`

---

## 🎓 ENTENDENDO A ESTRUTURA

```
cvm-automation/
│
├── scripts/                  # Scripts Python
│   ├── teste_rapido_cvm.py           # ← COMEÇAR AQUI
│   └── cvm_ofertas_automacao.py      # ← Script completo
│
├── data/                     # Dados (criar após setup)
│   ├── raw/                  # CSVs baixados
│   ├── processed/            # Excel processados
│   └── backup/               # Backups automáticos
│
├── logs/                     # Logs de execução
│
├── docs/                     # Documentação
│   ├── AUTOMACAO_CVM_DOCUMENTACAO.md
│   └── AGENDAMENTO_AUTOMATICO.md
│
├── README.md                 # Documentação principal
├── CHEATSHEET.md            # Comandos úteis
├── requirements.txt         # Dependências
└── setup.py                 # Setup inicial
```

---

## ✅ CHECKLIST DE IMPLEMENTAÇÃO

**Hoje (15 min):**
- [ ] Instalar dependências
- [ ] Executar `setup.py`
- [ ] Rodar `teste_rapido_cvm.py`
- [ ] Analisar `amostra_ofertas_cvm.xlsx`

**Esta semana:**
- [ ] Mapear colunas CVM → Excel atual
- [ ] Adaptar lógica de merge/update
- [ ] Testar pipeline completo
- [ ] Validar com casos reais

**Próxima semana:**
- [ ] Criar script de atualização diária
- [ ] Configurar Task Scheduler
- [ ] Testar execução agendada
- [ ] Documentar processo para equipe

---

## 🔧 CUSTOMIZAÇÕES COMUNS

### Filtrar por Múltiplos Tipos
```python
tipos = ['CRI', 'CRA', 'Debênture']
df_filtrado = df[df['Tipo_Valor_Mobiliario'].isin(tipos)]
```

### Ofertas de Emissor Específico
```python
ofertas_emissor = df[df['Nome_Emissor'].str.contains('BNDES', case=False, na=False)]
```

### Exportar Apenas Colunas Relevantes
```python
colunas = ['Codigo_Oferta', 'Tipo_Valor_Mobiliario', 'Nome_Emissor', 'Data_Registro', 'Situacao']
df[colunas].to_excel('ofertas_resumo.xlsx', index=False)
```

---

## 🐛 TROUBLESHOOTING RÁPIDO

| Problema | Solução |
|----------|---------|
| "Module not found" | `pip install -r requirements.txt` |
| "Connection timeout" | Aumentar timeout ou testar fora da rede corporativa |
| "UnicodeDecodeError" | Já configurado como `latin-1` (padrão CVM) |
| Coluna não existe | Ver `CHEATSHEET.md` → buscar nome correto |
| Script não roda agendado | Usar caminhos absolutos no .bat |

---

## 📚 DOCUMENTAÇÃO DETALHADA

| Dúvida | Ver Arquivo |
|--------|-------------|
| Como o sistema funciona? | `README.md` |
| Por que usar dados abertos? | `AUTOMACAO_CVM_DOCUMENTACAO.md` |
| Como agendar execução? | `AGENDAMENTO_AUTOMATICO.md` |
| Comandos úteis? | `CHEATSHEET.md` |

---

## 🎯 PRÓXIMO PASSO IMEDIATO

**Execute agora:**
```bash
python teste_rapido_cvm.py
```

Isso vai validar que tudo funciona e gerar um Excel de exemplo para você analisar.

---

## 💬 PERGUNTAS FREQUENTES

**P: Por que não usar Selenium no site da CVM?**  
R: O Portal Dados Abertos é oficial, mais rápido, confiável e simples. Selenium só seria necessário para dados que não existem no portal.

**P: Os dados são atualizados em tempo real?**  
R: Não. A CVM atualiza o arquivo diariamente (geralmente após 18h). Para seu caso de uso (alimentação diária de Excel), é perfeito.

**P: Posso usar em produção?**  
R: Sim! A fonte é oficial da CVM e o sistema está pronto para uso.

**P: Preciso saber Python avançado?**  
R: Não. Os scripts estão prontos. Você só precisa executar e, eventualmente, ajustar filtros.

---

## 📞 SUPORTE

**Desenvolvido por:** Andrew  
**Data:** 08/12/2024  
**Propósito:** DCM - BOCOM BBM

Para dúvidas:
1. Ver documentação específica
2. Executar comandos de diagnóstico (CHEATSHEET.md)
3. Verificar logs em `logs/`

---

## ⭐ TL;DR - RESUMÃO

1. **Instalar:** `pip install pandas requests openpyxl`
2. **Testar:** `python teste_rapido_cvm.py`
3. **Usar:** Adaptar `cvm_ofertas_automacao.py` para seu caso
4. **Agendar:** Task Scheduler para rodar diariamente

**Pronto! 🚀**

---

**Desenvolvido com ☕ para automatizar DCM**
