#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Construir Bases 2025
====================
Gera 2 bases separadas a partir de CVM + ANBIMA:
- encerradas_2025.xlsx: Ofertas finalizadas (com dados ANBIMA)
- pipeline_2025.xlsx: Ofertas em andamento

Uso:
    python construir_bases.py

Autor: Andrew Lopes / Claude Code
Data: Dezembro 2024
"""

import os
import sys
import glob
import re
from datetime import datetime
from pathlib import Path

import pandas as pd

# Importar configurações
from config import (
    BASE_DIR, CVM_CSV, ANBIMA_DIR, OUTPUT_DIR,
    ENCERRADAS_XLSX, PIPELINE_XLSX,
    PRODUTOS_MAP, STATUS_ENCERRADA, STATUS_PIPELINE,
    COORDENADORES_MAP, ANO_FILTRO, COLUNAS_PIPELINE
)


# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

def extrair_chave_anbima(codigo: str) -> int:
    """Extrai a chave numérica do código ANBIMA (ex: 'RJ-2025-12345' -> 12345)."""
    if pd.isna(codigo):
        return None
    try:
        # Pegar últimos dígitos após o último hífen
        partes = str(codigo).split('-')
        if len(partes) >= 3:
            return int(partes[-1])
        # Tentar extrair qualquer número
        numeros = re.findall(r'\d+', str(codigo))
        if numeros:
            return int(numeros[-1])
    except:
        pass
    return None


def abreviar_coordenador(nome: str) -> str:
    """Abrevia nome do coordenador usando o mapeamento."""
    if pd.isna(nome):
        return ''
    nome_upper = str(nome).upper().strip()

    # Buscar no mapa
    for chave, abrev in COORDENADORES_MAP.items():
        if chave in nome_upper:
            return abrev

    # Se não encontrar, retornar as primeiras palavras
    partes = nome.split()
    if len(partes) >= 2:
        return partes[0][:3].title() + partes[1][:3].title()
    return nome[:6] if len(nome) > 6 else nome


def formatar_data(val) -> str:
    """Formata data para dd/mm/yyyy (ano com 4 dígitos)."""
    if pd.isna(val) or val == '' or str(val) == 'nan':
        return ''
    try:
        if isinstance(val, str):
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%d/%m/%Y', '%d/%m/%Y %H:%M:%S', '%d/%m/%y']:
                try:
                    dt = datetime.strptime(val.split('.')[0], fmt)
                    return dt.strftime('%d/%m/%Y')
                except:
                    continue
            return val[:10] if len(val) >= 10 else val
        elif hasattr(val, 'strftime'):
            return val.strftime('%d/%m/%Y')
    except:
        pass
    return str(val)[:10] if val else ''


def formatar_volume(val) -> str:
    """Formata volume como número inteiro com separador de milhar (ex: 100.000.000)."""
    if pd.isna(val) or val == '' or str(val) == 'nan':
        return ''
    try:
        num = float(str(val).replace(',', '.'))
        # Formatar como inteiro com pontos como separador de milhar (padrão BR)
        return f"{int(num):,}".replace(',', '.')
    except:
        return str(val)


def mapear_produto(valor_mobiliario: str) -> str:
    """Mapeia tipo de valor mobiliário para nome padronizado."""
    if pd.isna(valor_mobiliario):
        return ''
    val = str(valor_mobiliario).strip()
    return PRODUTOS_MAP.get(val, val)


def mapear_publico(publico: str) -> str:
    """Mapeia público alvo para nome padronizado."""
    if pd.isna(publico):
        return ''
    val = str(publico).strip().lower()
    if 'profissional' in val:
        return 'Profissional'
    elif 'qualificado' in val:
        return 'Qualificado'
    elif 'geral' in val:
        return 'Geral'
    return val.title()


def mapear_status(status: str) -> str:
    """Mapeia status para nome padronizado."""
    if pd.isna(status):
        return ''
    val = str(status).strip()

    mapa = {
        'Oferta Encerrada': 'Oferta Encerrada',
        'Registro Concedido': 'Registro Concedido',
        'Aguardando Bookbuilding': 'Aguardando Bookbuilding',
        'Em AnÃ¡lise': 'Em Análise',
        'Em Análise': 'Em Análise',
        'AnÃ¡lise Pendente': 'Análise Pendente',
        'Análise Pendente': 'Análise Pendente',
        'Registro Caducado': 'Registro Caducado',
        'Oferta Revogada': 'Oferta Revogada',
        'Requerimento Expirado': 'Requerimento Expirado',
    }
    return mapa.get(val, val)


def eh_oferta_encerrada(status: str) -> bool:
    """Verifica se o status indica oferta encerrada."""
    status_map = mapear_status(status)
    return status_map in STATUS_ENCERRADA


def eh_oferta_pipeline(status: str) -> bool:
    """Verifica se o status indica oferta em andamento."""
    status_map = mapear_status(status)
    return status_map in STATUS_PIPELINE


def normalizar_emissor(nome: str) -> str:
    """Normaliza nome do emissor para Title Case."""
    if pd.isna(nome):
        return ''
    nome = str(nome).strip()

    # Palavras que devem permanecer em minúsculas (exceto no início)
    palavras_minusculas = {'de', 'da', 'do', 'das', 'dos', 'e', 'em', 'para'}

    # Siglas que devem permanecer em maiúsculas
    siglas = {'S.A.', 'S/A', 'SA', 'LTDA', 'LTDA.', 'SPE', 'EIRELI', 'ME', 'EPP', 'FII', 'FIDC'}

    partes = nome.split()
    resultado = []

    for i, parte in enumerate(partes):
        parte_upper = parte.upper()

        # Manter siglas em maiúsculas
        if parte_upper in siglas or parte_upper.replace('.', '') in siglas:
            resultado.append(parte_upper)
        # Primeira palavra sempre capitalizada
        elif i == 0:
            resultado.append(parte.capitalize())
        # Palavras de conexão em minúsculas
        elif parte.lower() in palavras_minusculas:
            resultado.append(parte.lower())
        else:
            resultado.append(parte.capitalize())

    return ' '.join(resultado)


def limpar_caracteres_ilegais(df: pd.DataFrame) -> pd.DataFrame:
    """Remove caracteres ilegais para Excel (control characters)."""
    import re
    # Regex para caracteres de controle ilegais no Excel
    illegal_chars = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')

    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].apply(lambda x: illegal_chars.sub('', str(x)) if pd.notna(x) else x)
    return df


def extrair_tipo_societario(tipo: str, nome_emissor: str = '') -> str:
    """Extrai tipo societário: S.A. ou Ltda.

    Primeiro tenta do campo Tipo_societario, depois do nome do Emissor.
    """
    # Tentar do campo Tipo_societario
    if pd.notna(tipo) and str(tipo).strip():
        tipo_str = str(tipo).strip().upper()
        if 'SA' in tipo_str or 'S.A' in tipo_str or 'CAPITAL' in tipo_str:
            return 'S.A.'
        elif 'LTDA' in tipo_str or 'LIMITADA' in tipo_str:
            return 'Ltda'

    # Tentar extrair do nome do Emissor (no final da string)
    if pd.notna(nome_emissor) and str(nome_emissor).strip():
        nome = str(nome_emissor).strip().upper()
        # Verificar sufixos comuns
        if nome.endswith('S.A.') or nome.endswith('S/A') or nome.endswith(' SA'):
            return 'S.A.'
        elif nome.endswith('LTDA') or nome.endswith('LTDA.'):
            return 'Ltda'
        # Verificar no meio também
        if ' S.A.' in nome or ' S/A ' in nome or ' SA ' in nome:
            return 'S.A.'
        elif ' LTDA ' in nome or ' LTDA.' in nome:
            return 'Ltda'

    return ''


# =============================================================================
# CARREGAR DADOS
# =============================================================================

def carregar_cvm() -> pd.DataFrame:
    """Carrega CSV da CVM e filtra por ano."""
    print(f"\nCarregando CVM: {CVM_CSV}")

    if not os.path.exists(CVM_CSV):
        print(f"ERRO: Arquivo não encontrado: {CVM_CSV}")
        sys.exit(1)

    # Tentar diferentes encodings
    for enc in ['utf-8', 'latin-1', 'cp1252']:
        try:
            df = pd.read_csv(CVM_CSV, sep=';', encoding=enc)
            break
        except:
            continue
    else:
        print("ERRO: Não foi possível ler o arquivo CSV")
        sys.exit(1)

    print(f"  Total: {len(df)} registros")

    # Filtrar por ano - SEMPRE usar Data_requerimento (Data_Registro é vazia para Aguardando Bookbuilding)
    if 'Data_requerimento' in df.columns:
        df['Ano'] = pd.to_datetime(df['Data_requerimento'], errors='coerce').dt.year
    elif 'Data_Registro' in df.columns:
        df['Ano'] = pd.to_datetime(df['Data_Registro'], errors='coerce').dt.year

    df_filtrado = df[df['Ano'] == ANO_FILTRO].copy()
    print(f"  Filtrado {ANO_FILTRO}: {len(df_filtrado)} registros")

    # Filtrar por produtos válidos
    if 'Valor_Mobiliario' in df_filtrado.columns:
        produtos_validos = list(PRODUTOS_MAP.keys())
        df_filtrado = df_filtrado[df_filtrado['Valor_Mobiliario'].isin(produtos_validos)]
        print(f"  Produtos válidos: {len(df_filtrado)} registros")

    return df_filtrado


def carregar_anbima() -> pd.DataFrame:
    """Carrega arquivo ANBIMA mais recente."""
    print(f"\nCarregando ANBIMA...")

    # Procurar arquivo ofertas-publicas-*.xls
    padroes = [
        str(ANBIMA_DIR / "ofertas-publicas-*.xls"),
        str(ANBIMA_DIR / "ofertas-publicas-*.xlsx"),
    ]

    arquivos = []
    for padrao in padroes:
        arquivos.extend(glob.glob(padrao))

    if not arquivos:
        print("  AVISO: Arquivo ANBIMA não encontrado")
        return pd.DataFrame()

    # Pegar o mais recente
    arquivo = max(arquivos, key=os.path.getmtime)
    print(f"  Arquivo: {os.path.basename(arquivo)}")

    try:
        df = pd.read_excel(arquivo)
        print(f"  Total: {len(df)} registros")

        # Extrair chave
        if 'Código da oferta' in df.columns:
            df['Chave'] = df['Código da oferta'].apply(extrair_chave_anbima)

        return df
    except Exception as e:
        print(f"  ERRO ao ler ANBIMA: {e}")
        return pd.DataFrame()


# =============================================================================
# PROCESSAR DADOS
# =============================================================================

def processar_cvm(df_cvm: pd.DataFrame) -> pd.DataFrame:
    """Processa dados CVM para formato padronizado (encerradas - legado)."""
    registros = []

    for _, row in df_cvm.iterrows():
        registro = {
            'Data Inicio/Registro': formatar_data(row.get('Data_Registro', '')),
            'Data Book': '',
            'Status': mapear_status(row.get('Status_Requerimento', '')),
            'Chave': int(row.get('Numero_Requerimento', 0)),
            'Público': mapear_publico(row.get('Publico_alvo', '')),
            'Produto': mapear_produto(row.get('Valor_Mobiliario', '')),
            'Emissor': str(row.get('Nome_Emissor', '')).strip(),
            'Coordenadores': abreviar_coordenador(row.get('Nome_Lider', '')),
            'Emissão': row.get('Emissao', ''),
            'Série': '',
            'Rating': '',
            'Volume Inicial': formatar_volume(row.get('Valor_Total_Registrado', '')),
            'Volume Final': '',
            'Data de Emissão': '',
            'Data de Vencimento': '',
            'Prazo': '',
            'Taxa Teto': '',
            'Taxa Final': '',
            '12.431': 'S' if row.get('Titulo_incentivado') == 'Sim' else 'N',
            'Venda': '',
            'Obs': '',
        }
        registros.append(registro)

    return pd.DataFrame(registros)


def processar_cvm_pipeline(df_cvm: pd.DataFrame) -> pd.DataFrame:
    """Processa dados CVM para formato PIPELINE (27 colunas)."""
    registros = []

    for _, row in df_cvm.iterrows():
        # Verificar se é CRI ou CRA para preencher Devedor
        produto = mapear_produto(row.get('Valor_Mobiliario', ''))
        devedor = ''
        if produto in ['CRI', 'CRA', 'CR']:
            devedor = str(row.get('Identificacao_devedores_coobrigados', '')).strip()
            if devedor == 'nan':
                devedor = ''

        # Para CRI/CRA/CR: usar Devedor como Emissor (se disponível)
        if produto in ['CRI', 'CRA', 'CR'] and devedor:
            emissor_final = devedor
        else:
            emissor_final = normalizar_emissor(row.get('Nome_Emissor', ''))

        registro = {
            'Data Requerimento': formatar_data(row.get('Data_requerimento', '')),
            'Data Registro': formatar_data(row.get('Data_Registro', '')),
            'Data Book': '',  # Vazia - preencher manual/scraping
            'Bookbuilding': str(row.get('Bookbuilding', '')).strip() if pd.notna(row.get('Bookbuilding')) else '',
            'Status': mapear_status(row.get('Status_Requerimento', '')),
            'Chave': int(row.get('Numero_Requerimento', 0)),
            'CNPJ Emissor': str(row.get('CNPJ_Emissor', '')).strip() if pd.notna(row.get('CNPJ_Emissor')) else '',
            'Emissor': emissor_final,
            'Tipo': extrair_tipo_societario(row.get('Tipo_societario', ''), row.get('Nome_Emissor', '')),
            'Produto': produto,
            'Público': mapear_publico(row.get('Publico_alvo', '')),
            'Coordenadores': abreviar_coordenador(row.get('Nome_Lider', '')),
            'Emissão': row.get('Emissao', ''),
            'Série': '',  # Vazia - preencher manual/scraping
            'Rating': str(row.get('Avaliador_Risco', '')).strip() if pd.notna(row.get('Avaliador_Risco')) else '',
            'Volume Inicial': formatar_volume(row.get('Valor_Total_Registrado', '')),
            'Data de Emissão': '',  # Vazia - preencher manual/scraping
            'Data de Vencimento': '',  # Vazia - preencher manual/scraping
            'Prazo': '',  # Vazia - preencher manual/scraping
            'Taxa Teto': '',  # Vazia - preencher manual/scraping
            'Devedor': devedor,
            'Vasos Comunicantes': str(row.get('Oferta_vasos_comunicantes', '')).strip() if pd.notna(row.get('Oferta_vasos_comunicantes')) else '',
            'Sustentável': str(row.get('Titulo_classificado_como_sustentavel', '')).strip() if pd.notna(row.get('Titulo_classificado_como_sustentavel')) else '',
            '12.431': 'S' if str(row.get('Titulo_incentivado', '')).upper() == 'SIM' else 'N',
            '14.801': '',  # Vazia - preencher manual
            'Securitizada': '',  # Vazia - preencher manual
            'Obs': '',  # Vazia - preencher manual
        }
        registros.append(registro)

    return pd.DataFrame(registros, columns=COLUNAS_PIPELINE)


def enriquecer_com_anbima(df_base: pd.DataFrame, df_anbima: pd.DataFrame) -> pd.DataFrame:
    """Enriquece dados com informações da ANBIMA."""
    if df_anbima.empty:
        return df_base

    print("\nEnriquecendo com dados ANBIMA...")

    # Criar lookup por chave
    anbima_por_chave = {}
    for _, row in df_anbima.iterrows():
        chave = row.get('Chave')
        if pd.notna(chave):
            chave = int(chave)
            if chave not in anbima_por_chave:
                anbima_por_chave[chave] = []
            anbima_por_chave[chave].append(row)

    enriquecidos = 0
    for idx, row in df_base.iterrows():
        chave = row['Chave']
        if chave in anbima_por_chave:
            # Pegar primeira série (ou fazer match por série se tiver)
            dados_anbima = anbima_por_chave[chave][0]

            # Taxa Final
            if pd.isna(row['Taxa Final']) or row['Taxa Final'] == '':
                spread = dados_anbima.get('Spread', '')
                juros = dados_anbima.get('Juros', '')
                indexador = dados_anbima.get('Indexador', '')

                if pd.notna(spread) and spread != '':
                    if 'DI' in str(indexador) or 'CDI' in str(indexador):
                        df_base.at[idx, 'Taxa Final'] = f"CDI + {spread}%"
                    elif 'IPCA' in str(indexador):
                        df_base.at[idx, 'Taxa Final'] = f"IPCA + {spread}%"
                    else:
                        df_base.at[idx, 'Taxa Final'] = f"{spread}%"

            # Volume Final
            if pd.isna(row['Volume Final']) or row['Volume Final'] == '':
                vol = dados_anbima.get('Valor total encerrado da série', '')
                if pd.notna(vol):
                    df_base.at[idx, 'Volume Final'] = formatar_volume(vol)

            # Data de Vencimento
            if pd.isna(row['Data de Vencimento']) or row['Data de Vencimento'] == '':
                dt = dados_anbima.get('Data de vencimento', '')
                if pd.notna(dt):
                    df_base.at[idx, 'Data de Vencimento'] = formatar_data(dt)

            # Prazo
            if pd.isna(row['Prazo']) or row['Prazo'] == '':
                prazo = dados_anbima.get('Prazo série', '')
                if pd.notna(prazo):
                    df_base.at[idx, 'Prazo'] = str(prazo)

            # Série
            if pd.isna(row['Série']) or row['Série'] == '':
                serie = dados_anbima.get('Série', '')
                if pd.notna(serie):
                    df_base.at[idx, 'Série'] = str(serie)

            enriquecidos += 1

    print(f"  {enriquecidos} registros enriquecidos com ANBIMA")
    return df_base


# =============================================================================
# GERAR BASES
# =============================================================================

def gerar_encerradas_anbima(df_anbima: pd.DataFrame, df_cvm: pd.DataFrame) -> pd.DataFrame:
    """Gera base de ofertas encerradas usando ANBIMA como base (~100 colunas).

    Base: ANBIMA (1 linha por série) + 10 colunas extras do CVM.
    """
    print("\n" + "=" * 60)
    print("GERANDO BASE: ENCERRADAS (ANBIMA + CVM)")
    print("=" * 60)

    if df_anbima.empty:
        print("ERRO: Arquivo ANBIMA vazio!")
        return pd.DataFrame()

    # Filtrar ANBIMA: ano 2025 e status Encerrada
    df_anbima['Ano'] = pd.to_datetime(df_anbima['Data de registro da oferta'], errors='coerce', dayfirst=True).dt.year
    df_enc = df_anbima[(df_anbima['Ano'] == ANO_FILTRO) & (df_anbima['Status da oferta'] == 'Encerrada')].copy()
    print(f"Séries encerradas ANBIMA 2025: {len(df_enc)}")

    if df_enc.empty:
        print("Nenhuma oferta encerrada encontrada!")
        return pd.DataFrame()

    # Extrair Chave do código da oferta (ex: SRE/2025/22859 -> 22859)
    df_enc['Chave'] = df_enc['Código da oferta'].apply(extrair_chave_anbima)

    # Criar lookup CVM por chave
    cvm_lookup = {}
    for _, row in df_cvm.iterrows():
        chave = row.get('Numero_Requerimento')
        if pd.notna(chave):
            cvm_lookup[int(chave)] = row

    # Colunas CVM extras para adicionar
    colunas_cvm_extras = [
        ('Tipo Societário', 'Tipo_societario', extrair_tipo_societario),
        ('Bookbuilding CVM', 'Bookbuilding', None),
        ('Vasos Comunicantes', 'Oferta_vasos_comunicantes', None),
        ('Sustentável CVM', 'Titulo_classificado_como_sustentavel', None),
        ('Devedores CVM', 'Identificacao_devedores_coobrigados', None),
        ('Descrição Garantias', 'Descricao_garantias', None),
        ('Descrição Lastro', 'Descricao_lastro', None),
        ('Revolvência', 'Possibilidade_revolvencia', None),
        ('Regime Fiduciário', 'Regime_fiduciario', None),
        ('Ativos Alvo', 'Ativos_alvo', None),
    ]

    # Adicionar colunas CVM extras
    for col_nome, col_cvm, func in colunas_cvm_extras:
        df_enc[col_nome] = ''

    enriquecidos = 0
    for idx, row in df_enc.iterrows():
        chave = row['Chave']
        if chave in cvm_lookup:
            cvm_row = cvm_lookup[chave]
            for col_nome, col_cvm, func in colunas_cvm_extras:
                valor = cvm_row.get(col_cvm, '')
                if func:
                    # Para Tipo Societário, passar também o nome do emissor
                    if col_nome == 'Tipo Societário':
                        valor = func(valor, cvm_row.get('Nome_Emissor', ''))
                    else:
                        valor = func(valor)
                elif pd.notna(valor):
                    valor = str(valor).strip()
                    if valor == 'nan':
                        valor = ''
                else:
                    valor = ''
                df_enc.at[idx, col_nome] = valor
            enriquecidos += 1

    print(f"  {enriquecidos} séries enriquecidas com dados CVM")

    # Calcular coluna "Venda R$" - soma das quantidades × preço unitário
    colunas_distribuicao = [
        'Outros - quantidade de valores mobiliários',
        'Demais pessoas jurídicas ligadas - quantidade de valores mobiliários',
        'Companhias seguradoras - quantidade de valores  mobiliários',
        'Demais instituições financeiras - quantidade de valores mobiliários',
        'Demais pessoas jurídicas - quantidade de valores mobiliários',
        'Clubes de investimento - quantidade de valores mobiliários',
        'Investidores estrangeiros - quantidade de valores',
        'Pessoas naturais - quantidade de valores mobiliários',
        'Fundos de investimentos - quantidade de valores',
        'Entidades de previdência privada - quantidade de valores',
    ]

    # Verificar quais colunas existem no DataFrame
    colunas_existentes = [c for c in colunas_distribuicao if c in df_enc.columns]
    if colunas_existentes and 'Preço unitário' in df_enc.columns:
        # Somar quantidades
        qtd_total = df_enc[colunas_existentes].sum(axis=1, skipna=True)
        # Multiplicar pelo preço unitário
        df_enc['Venda R$'] = qtd_total * df_enc['Preço unitário'].fillna(0)
        print(f"  Coluna 'Venda R$' calculada (qtd × preço unitário)")
    else:
        print("  AVISO: Colunas de distribuição ou Preço unitário não encontradas")

    # Remover coluna auxiliar Ano
    df_enc = df_enc.drop(columns=['Ano'], errors='ignore')

    # Ordenar por chave (mais recente primeiro)
    df_enc = df_enc.sort_values('Chave', ascending=False)

    return df_enc


def gerar_pipeline(df_cvm: pd.DataFrame) -> pd.DataFrame:
    """Gera base de ofertas em andamento (pipeline) com 27 colunas."""
    print("\n" + "=" * 60)
    print("GERANDO BASE: PIPELINE (27 colunas)")
    print("=" * 60)

    # Filtrar pipeline
    df_pipe = df_cvm[df_cvm['Status_Requerimento'].apply(eh_oferta_pipeline)].copy()
    print(f"Ofertas em andamento CVM: {len(df_pipe)}")

    if df_pipe.empty:
        print("Nenhuma oferta em andamento encontrada!")
        return pd.DataFrame(columns=COLUNAS_PIPELINE)

    # Processar para formato pipeline (27 colunas)
    df_base = processar_cvm_pipeline(df_pipe)

    # Ordenar por chave (mais recente primeiro)
    df_base = df_base.sort_values('Chave', ascending=False)

    return df_base


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("\n" + "=" * 60)
    print("CONSTRUIR BASES 2025")
    print("=" * 60)

    # Criar diretório de output
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Carregar dados
    df_cvm = carregar_cvm()
    df_anbima = carregar_anbima()

    if df_cvm.empty:
        print("\nNenhum dado CVM para processar!")
        return

    # Gerar bases
    df_encerradas = gerar_encerradas_anbima(df_anbima, df_cvm)  # ANBIMA como base
    df_pipeline = gerar_pipeline(df_cvm)

    # Salvar
    print("\n" + "=" * 60)
    print("SALVANDO ARQUIVOS")
    print("=" * 60)

    if not df_encerradas.empty:
        # Limpar caracteres ilegais antes de salvar
        df_encerradas = limpar_caracteres_ilegais(df_encerradas)
        df_encerradas.to_excel(ENCERRADAS_XLSX, index=False, sheet_name='Encerradas')
        print(f"✓ {ENCERRADAS_XLSX.name}: {len(df_encerradas)} séries, {len(df_encerradas.columns)} colunas")

    if not df_pipeline.empty:
        df_pipeline.to_excel(PIPELINE_XLSX, index=False, sheet_name='Pipeline')
        print(f"✓ {PIPELINE_XLSX.name}: {len(df_pipeline)} registros")

    # Resumo
    print("\n" + "=" * 60)
    print("RESUMO")
    print("=" * 60)
    print(f"Encerradas: {len(df_encerradas)} séries ({len(df_encerradas.columns)} colunas)")
    print(f"Pipeline: {len(df_pipeline)} ofertas ({len(df_pipeline.columns)} colunas)")
    print(f"\nArquivos salvos em: {OUTPUT_DIR}")
    print("\nConcluído!")


if __name__ == "__main__":
    main()
