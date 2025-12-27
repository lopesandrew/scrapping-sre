# Regras de Processamento - CVM Ofertas

Este arquivo contém todas as regras de processamento dos dados de ofertas da CVM.
Edite este arquivo para ajustar as regras conforme necessário.

---

## 1. Produtos Filtrados

Apenas os seguintes produtos são processados:

| Valor no CSV | Valor Simplificado |
|--------------|-------------------|
| Debêntures | Debêntures |
| Debêntures Conversíveis | Debêntures |
| Certificados de Recebíveis do Agronegócio | CRA |
| Certificados de Recebíveis Imobiliários | CRI |
| Notas Comerciais | NC |
| Certificados de Recebíveis | CR |
| Cédula de Produto Rural Financeira | CPR-F |
| Notas Promissórias | NP |

---

## 2. Abreviação de Coordenadores

| Nome Completo | Abreviação |
|---------------|------------|
| BANCO BRADESCO BBI S.A. | BBI |
| BRADESCO BBI S.A. | BBI |
| ITAU BBA ASSESSORIA FINANCEIRA S.A. | BBA |
| ITAÚ BBA S.A. | BBA |
| BANCO SANTANDER (BRASIL) S.A. | San |
| SANTANDER BRASIL | San |
| BTG PACTUAL SERVIÇOS FINANCEIROS S/A DTVM | BTG |
| BANCO BTG PACTUAL S/A | BTG |
| BTG PACTUAL | BTG |
| XP INVESTIMENTOS CCTVM S.A. | XP |
| XP INVESTIMENTOS | XP |
| UBS BB CORRETORA | UBS |
| UBS BRASIL | UBS |
| BANCO SAFRA S/A | Safra |
| BANCO CITIBANK S.A. | Citi |
| CITIBANK | Citi |
| INTER DISTRIBUIDORA | Inter |
| BANCO INTER | Inter |
| ATIVA INVESTIMENTOS | Ativa |
| TERRA INVESTIMENTOS | Terra |
| BANCO BV S.A. | BV |
| BANCO VOTORANTIM | BV |
| BANCO GENIAL S.A. | Genial |
| GENIAL INVESTIMENTOS | Genial |
| CAIXA ECONÔMICA FEDERAL | Caixa |
| BNDES | BNDES |
| BANCO ABC BRASIL | ABC |
| BR PARTNERS | BR Partners |
| OPEA SECURITIZADORA | OPEA |
| BANCO DO BRASIL | BB |
| BANCO DAYCOVAL | Daycoval |
| BANCO MODAL | Modal |
| BANCO RODOBENS | Rodobens |
| BANCO PINE | Pine |
| GUIDE INVESTIMENTOS | Guide |
| ORAMA | Orama |
| BANCO PAN | Pan |
| BANCO ORIGINAL | Original |
| BANCO BMG | BMG |
| PLURAL | Plural |
| GAIA SECURITIZADORA | Gaia |
| TRUE SECURITIZADORA | True |
| VIRGO COMPANHIA | Virgo |
| ISEC SECURITIZADORA | Isec |
| OCTANTE SECURITIZADORA | Octante |
| RB CAPITAL | RB |
| VINCI PARTNERS | Vinci |
| SPX CAPITAL | SPX |

---

## 3. Regra do Emissor

### Para Debêntures, NC e NP:
- Usar campo `Nome_Emissor`

### Para CRA, CRI, CR e CPR-F:
- Usar campo `Identificacao_devedores_coobrigados`
- Se contiver termos genéricos (pessoa física, diversos, pulverizado): usar "Pulverizado"
- Se vazio ou N/A: usar "N/A"

### Formatação (Title Case):
- Primeira letra de cada palavra em maiúscula
- Preposições em minúsculo: de, do, da, dos, das, em, e, para, por, com
- Manter siglas: S.A., S/A, LTDA, CIA, CNPJ, FIDC, FII, FIP

---

## 4. Status (sem simplificação)

Manter valores originais do CSV:
- Oferta Encerrada
- Registro Concedido
- Aguardando Bookbuilding
- Registro Caducado
- Oferta Revogada
- Requerimento Expirado

### Separação de Abas:
- **Pipeline**: Registro Concedido, Aguardando Bookbuilding
- **Registrada**: Oferta Encerrada
- **Ignorar**: Registro Caducado, Oferta Revogada, Requerimento Expirado

---

## 5. Formatação de Taxas

Padrões aceitos:
- `CDI + X,XX%` (spread sobre CDI)
- `X,XX% CDI` ou `XX% CDI` (percentual do CDI)
- `IPCA + X,XX%` (spread sobre IPCA)
- `Pré X,XX%` (taxa prefixada)
- `B30 + X,XX%` ou `B30 - X,XX%` (NTN-B como referência)
- `DI1FXX + X,XX%` ou `DI1FXX - X,XX%` (futuros de DI)
- `VC + X,XX%` (variação cambial)
- `Variável` (casos especiais)

---

## 6. Colunas do Excel

### Ordem das Colunas:

| # | Coluna | Fonte |
|---|--------|-------|
| 1 | Data Requerimento | CSV |
| 2 | Data Registro | CSV |
| 3 | Data Book | Manual |
| 4 | Status | CSV |
| 5 | Chave | CSV |
| 6 | Público | CSV |
| 7 | Produto | CSV (simplificado) |
| 8 | Emissor | CSV (Title Case) |
| 9 | Coordenadores | CSV (abreviado) |
| 10 | Nº Emissão | CSV |
| 11 | Série | Scraping |
| 12 | Espécie | Scraping |
| 13 | Rating | Scraping |
| 14 | Volume Inicial | CSV |
| 15 | Volume Final | Scraping |
| 16 | Data de Emissão | Scraping |
| 17 | Data de Vencimento | Scraping |
| 18 | Prazo | Calculado |
| 19 | Taxa Teto | Scraping |
| 20 | Taxa Final | Scraping |
| 21 | 12.431 | CSV |
| 22 | 14.801 | Scraping |
| 23 | Venda | Manual |
| 24 | Venda R$ | Manual |
| 25 | Obs | CSV |
| 26 | Tipo Oferta | CSV |
| 27 | Regime Distribuição | CSV |
| 28 | Bookbuilding | CSV |
| 29 | IPO | CSV |
| 30 | Vasos Comunicantes | CSV |
| 31 | Sustentável | CSV |
| 32 | Tipo Lastro | CSV |
| 33 | Regime Fiduciário | CSV |
| 34 | Garantias | CSV |
| 35 | Lastro | CSV |
| 36 | Destinação Recursos | CSV |
| 37 | Agente Fiduciário | CSV |

---

## 7. Mapeamento CSV → Excel

| Campo Excel | Campo CSV |
|-------------|-----------|
| Data Requerimento | Data_requerimento |
| Data Registro | Data_Registro |
| Status | Status_Requerimento |
| Chave | Numero_Requerimento |
| Público | Publico_alvo |
| Produto | Valor_Mobiliario |
| Emissor | Nome_Emissor ou Identificacao_devedores_coobrigados |
| Coordenadores | Nome_Lider |
| Nº Emissão | Emissao |
| Volume Inicial | Valor_Total_Registrado |
| 12.431 | Titulo_incentivado |
| Tipo Oferta | Tipo_Oferta |
| Regime Distribuição | Regime_distribuicao |
| Bookbuilding | Bookbuilding |
| IPO | Oferta_inicial |
| Vasos Comunicantes | Oferta_vasos_comunicantes |
| Sustentável | Titulo_classificado_como_sustentavel |
| Tipo Lastro | Tipo_lastro |
| Regime Fiduciário | Regime_fiduciario |
| Garantias | Descricao_garantias |
| Lastro | Descricao_lastro |
| Destinação Recursos | Destinacao_recursos |
| Agente Fiduciário | Agente_fiduciario |

---

## 8. Labels para Scraping (Página CVM)

URL: `https://web.cvm.gov.br/sre-publico-cvm/#/oferta-publica/{Numero_Requerimento}`

| Campo | Label na Página |
|-------|-----------------|
| Série | Número da série na seção "Características do Valor Mobiliário" |
| Espécie | "Espécie:" |
| Rating | "Avaliação de risco:" |
| Volume Final | "Valor Pós Coleta de Intenções:" |
| Data de Emissão | "Data de emissão:" |
| Data de Vencimento | "Data de vencimento:" |
| Taxa Teto | "Informações sobre remuneração máxima:" ou "Informações sobre remuneração:" |
| Taxa Final | "Informações sobre remuneração final (pós bookbuilding):" |
| 14.801 | "Debêntures de infraestrutura - Lei 14.801/24:" |

---

## 9. Regras de Atualização

### Oferta NOVA:
- Adicionar na aba Pipeline
- Fazer scraping completo

### Oferta com MUDANÇA DE STATUS:
- Atualizar campo Status
- Se novo status = "Oferta Encerrada": mover para aba Registrada
- Refazer scraping (pode ter novos dados)

### Oferta sem mudança:
- Não alterar

---

## 10. Cálculo do Prazo

```
Prazo = (Data_Vencimento - Data_Emissão).days / 365
Formato: 2 casas decimais
```

---

## 11. Arquivos

| Arquivo | Descrição |
|---------|-----------|
| oferta_resolucao_160.csv | CSV fonte (salvo manualmente) |
| DCM_CVM.xlsx | Excel de saída (atualizado incrementalmente) |
| processar_ofertas_cvm.py | Script principal |
| REGRAS_PROCESSAMENTO.md | Este arquivo de regras |
