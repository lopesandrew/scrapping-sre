#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configurações do projeto de automação CVM.
"""

import os
from pathlib import Path

# Diretório base
BASE_DIR = Path(__file__).parent

# Arquivos de entrada (você baixa manualmente)
CVM_CSV = BASE_DIR / "oferta_resolucao_160.csv"
ANBIMA_DIR = BASE_DIR  # Arquivo ofertas-publicas-*.xls fica aqui

# Arquivos de saída
OUTPUT_DIR = BASE_DIR / "data" / "output"
ENCERRADAS_XLSX = OUTPUT_DIR / "encerradas_2025.xlsx"
PIPELINE_XLSX = OUTPUT_DIR / "pipeline_2025.xlsx"

# Logs
LOGS_DIR = BASE_DIR / "logs"

# Produtos a processar (mapeamento CVM -> Nome padronizado)
PRODUTOS_MAP = {
    'Debêntures': 'Debêntures',
    'DebÃªntures': 'Debêntures',
    'Debêntures Conversíveis': 'Debêntures',
    'DebÃªntures ConversÃ­veis': 'Debêntures',
    'Certificados de Recebíveis do Agronegócio': 'CRA',
    'Certificados de RecebÃ­veis do AgronegÃ³cio': 'CRA',
    'Certificados de Recebíveis Imobiliários': 'CRI',
    'Certificados de RecebÃ­veis ImobiliÃ¡rios': 'CRI',
    'Notas Comerciais': 'NC',
    'Certificados de Recebíveis': 'CR',
    'Certificados de RecebÃ­veis': 'CR',
    'Cédula de Produto Rural Financeira': 'CPR-F',
    'CÃ©dula de Produto Rural Financeira': 'CPR-F',
    'Notas Promissórias': 'NP',
    'Notas PromissÃ³rias': 'NP',
}

# Status que indicam oferta encerrada (dados finais)
STATUS_ENCERRADA = [
    'Oferta Encerrada',
]

# Status que indicam oferta em andamento (Pipeline)
STATUS_PIPELINE = [
    'Registro Concedido',
    'Aguardando Bookbuilding',
    'Em Análise',
    'Análise Pendente',
]

# Abreviações de coordenadores
COORDENADORES_MAP = {
    'BANCO BRADESCO BBI': 'BBI',
    'BRADESCO BBI': 'BBI',
    'ITAU BBA': 'BBA',
    'ITAÚ BBA': 'BBA',
    'BANCO SANTANDER': 'San',
    'SANTANDER': 'San',
    'BTG PACTUAL': 'BTG',
    'BANCO BTG PACTUAL': 'BTG',
    'XP INVESTIMENTOS': 'XP',
    'UBS BB': 'UBS',
    'UBS BRASIL': 'UBS',
    'BANCO SAFRA': 'Safra',
    'SAFRA': 'Safra',
    'BANCO VOTORANTIM': 'BV',
    'BV': 'BV',
    'CAIXA ECONOMICA FEDERAL': 'Caixa',
    'BANCO DO BRASIL': 'BB',
    'BANCO ABC BRASIL': 'ABC',
    'ABC BRASIL': 'ABC',
    'BANCO DAYCOVAL': 'Dayco',
    'DAYCOVAL': 'Dayco',
    'BANCO INTER': 'Inter',
    'INTER': 'Inter',
    'BANCO MODAL': 'Modal',
    'MODAL': 'Modal',
    'BANCO ORIGINAL': 'Original',
    'ORIGINAL': 'Original',
    'BANCO PAN': 'Pan',
    'PAN': 'Pan',
    'BANCO PINE': 'Pine',
    'PINE': 'Pine',
    'BANCO RODOBENS': 'RB',
    'RODOBENS': 'RB',
    'GENIAL INVESTIMENTOS': 'Genial',
    'GENIAL': 'Genial',
    'GUIDE INVESTIMENTOS': 'Guide',
    'GUIDE': 'Guide',
    'ORIZ PARTNERS': 'Oriz',
    'ORIZ': 'Oriz',
    'TERRA INVESTIMENTOS': 'Terra',
    'TERRA': 'Terra',
    'OPEA': 'OPEA',
    'HABITASEC': 'Habitasec',
    'TRUE': 'True',
    'BNDES': 'BNDES',
    'JGP': 'JGP',
    'GLPG': 'GLPG',
    'OSLO': 'Oslo',
    'BS2': 'BS2',
    'STONEX': 'StoneX',
    'ATIVA': 'Ativa',
    'BNP PARIBAS': 'BNP',
}

# Ano a filtrar
ANO_FILTRO = 2025

# Colunas do PIPELINE (27 colunas)
COLUNAS_PIPELINE = [
    'Data Requerimento',
    'Data Registro',
    'Data Book',
    'Bookbuilding',
    'Status',
    'Chave',
    'CNPJ Emissor',
    'Emissor',
    'Tipo',
    'Produto',
    'Público',
    'Coordenadores',
    'Emissão',
    'Série',
    'Rating',
    'Volume Inicial',
    'Data de Emissão',
    'Data de Vencimento',
    'Prazo',
    'Taxa Teto',
    'Devedor',
    'Vasos Comunicantes',
    'Sustentável',
    '12.431',
    '14.801',
    'Securitizada',
    'Obs',
]

# Colunas das ENCERRADAS (a definir)
COLUNAS_ENCERRADAS = [
    # TODO: Definir colunas das encerradas
]
