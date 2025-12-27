#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Comparação CSV vs Excel
=================================
Compara DCM_CVM.csv com DCM_Local.xlsx para as chaves informadas.
Gera Excel com as diferenças no formato do DCM_Local.

Uso:
    python comparar_excel.py
    # Cole as chaves quando solicitado (uma por linha, Enter vazio para terminar)

Autor: Andrew Lopes / Claude Code
Data: Dezembro 2024
"""

import os
import pandas as pd
from datetime import datetime

# =============================================================================
# CONFIGURAÇÕES
# =============================================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "DCM_CVM.csv")
# Excel de referência (SOMENTE LEITURA - nunca modificar!)
EXCEL_PATH = "/Users/andrewlopes/Library/CloudStorage/OneDrive-BCPSecurities/Área de Trabalho/DCM_local.xlsx"
OUTPUT_PATH = os.path.join(BASE_DIR, "atualizacoes_excel.xlsx")


# =============================================================================
# FUNÇÕES
# =============================================================================

def formatar_data_curta(val):
    """Formata data para dd/mm/yy."""
    if pd.isna(val) or val == '' or str(val) == 'nan':
        return ''
    try:
        if isinstance(val, str):
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%d/%m/%Y', '%d/%m/%Y %H:%M:%S']:
                try:
                    dt = datetime.strptime(val.split('.')[0], fmt)
                    return dt.strftime('%d/%m/%y')
                except:
                    continue
            return val
        elif hasattr(val, 'strftime'):
            return val.strftime('%d/%m/%y')
    except:
        pass
    return str(val)[:10] if val else ''


def carregar_dados():
    """Carrega CSV e Excel."""
    print("Carregando arquivos...")

    if not os.path.exists(CSV_PATH):
        print(f"ERRO: Arquivo não encontrado: {CSV_PATH}")
        return None, None

    if not os.path.exists(EXCEL_PATH):
        print(f"ERRO: Arquivo não encontrado: {EXCEL_PATH}")
        return None, None

    df_csv = pd.read_csv(CSV_PATH, sep=';', encoding='utf-8-sig')
    df_csv['Chave'] = df_csv['Chave'].astype(int)

    df_excel = pd.read_excel(EXCEL_PATH)
    df_excel['Chave'] = df_excel['Chave'].astype(int)

    print(f"  CSV: {len(df_csv)} linhas")
    print(f"  Excel: {len(df_excel)} linhas")

    return df_csv, df_excel


def ler_chaves():
    """Lê chaves do usuário."""
    print("\n" + "=" * 60)
    print("Cole as chaves (uma por linha, Enter vazio para terminar):")
    print("=" * 60)

    chaves = []
    while True:
        linha = input().strip()
        if not linha:
            break
        # Aceitar múltiplos formatos: uma por linha, separadas por vírgula, espaço ou tab
        for parte in linha.replace(',', ' ').replace('\t', ' ').split():
            try:
                chave = int(parte.strip())
                if chave not in chaves:
                    chaves.append(chave)
            except ValueError:
                continue

    return sorted(set(chaves))


def comparar_chaves(chaves, df_csv, df_excel):
    """Compara as chaves e retorna diferenças."""
    chaves_excel = set(df_excel['Chave'])
    diferencas = []

    print(f"\nAnalisando {len(chaves)} chaves...")

    for chave in chaves:
        # Verificar se existe no CSV
        rows_csv = df_csv[df_csv['Chave'] == chave]
        if len(rows_csv) == 0:
            print(f"  {chave}: não encontrada no CSV")
            continue

        row_csv = rows_csv.iloc[0]

        # Verificar se existe no Excel
        if chave not in chaves_excel:
            # Oferta nova (não está no Excel)
            diferencas.append({
                'chave': chave,
                'tipo': 'NOVA',
                'row': row_csv
            })
            print(f"  {chave}: NOVA (não está no Excel)")
            continue

        # Comparar com Excel
        row_excel = df_excel[df_excel['Chave'] == chave].iloc[0]
        mudancas = []

        # Status
        status_excel = str(row_excel.get('Status', '')).strip()
        status_csv = str(row_csv.get('Status', '')).strip()
        if status_excel == 'Concedido':
            status_excel = 'Registro Concedido'
        if status_excel != status_csv:
            mudancas.append(f"Status: {status_excel} → {status_csv}")

        # Taxa Final
        taxa_excel = str(row_excel.get('Taxa Final', '')).strip()
        taxa_csv = str(row_csv.get('Taxa Final', '')).strip()
        if taxa_excel in ['', 'nan', 'None'] and taxa_csv not in ['', 'nan', 'None']:
            mudancas.append(f"Taxa Final: {taxa_csv}")

        # Volume Final
        vol_excel = str(row_excel.get('Volume Final', '')).strip()
        vol_csv = str(row_csv.get('Volume Final', '')).strip()
        if vol_excel in ['', 'nan', 'None'] and vol_csv not in ['', 'nan', 'None']:
            mudancas.append(f"Volume Final: {vol_csv}")

        # Rating
        rating_excel = str(row_excel.get('Rating', '')).strip()
        rating_csv = str(row_csv.get('Rating', '')).strip()
        if rating_excel in ['', 'nan', 'None'] and rating_csv not in ['', 'nan', 'None', 'TBD']:
            mudancas.append(f"Rating: {rating_csv}")

        if mudancas:
            diferencas.append({
                'chave': chave,
                'tipo': 'ATUALIZAR',
                'mudancas': mudancas,
                'row': row_csv
            })
            print(f"  {chave}: {', '.join(mudancas)}")
        else:
            print(f"  {chave}: sem alterações")

    return diferencas


def gerar_excel(diferencas, output_path):
    """Gera Excel com as diferenças."""
    if not diferencas:
        print("\nNenhuma diferença encontrada!")
        return

    # Coletar linhas
    linhas = [d['row'] for d in diferencas]
    df = pd.DataFrame(linhas)

    # Criar DataFrame no formato do Excel do usuário
    df_export = pd.DataFrame()
    df_export['Data Inicio/Registro'] = df['Data Registro'].apply(formatar_data_curta)
    df_export['Data Book'] = df['Data Book'].apply(formatar_data_curta)
    df_export['Status'] = df['Status']
    df_export['Chave'] = df['Chave'].astype(int)
    df_export['Público'] = df['Público']
    df_export['Produto'] = df['Produto']
    df_export['Emissor'] = df['Emissor']
    df_export['Coordenadores'] = df['Coordenadores']
    df_export['Emissão'] = df['Nº Emissão']
    df_export['Série'] = df['Série']
    df_export['Rating'] = df['Rating']
    df_export['Volume Inicial'] = df['Volume Inicial']
    df_export['Volume Final'] = df['Volume Final']
    df_export['Data de Emissão'] = df['Data de Emissão'].apply(formatar_data_curta)
    df_export['Data de Vencimento'] = df['Data de Vencimento'].apply(formatar_data_curta)
    df_export['Prazo'] = df['Prazo']
    df_export['Taxa Teto'] = df['Taxa Teto']
    df_export['Taxa Final'] = df['Taxa Final']
    df_export['12.431'] = df['12.431']
    df_export['Venda'] = df['Venda']
    df_export['Obs'] = df['Obs']

    # Ordenar por chave decrescente
    df_export = df_export.sort_values('Chave', ascending=False)

    # Salvar
    df_export.to_excel(output_path, index=False, sheet_name='Atualizações')

    print(f"\n{'=' * 60}")
    print(f"Arquivo gerado: {output_path}")
    print(f"Total: {len(df_export)} ofertas")
    print(f"{'=' * 60}")

    # Resumo
    novas = len([d for d in diferencas if d['tipo'] == 'NOVA'])
    atualizadas = len([d for d in diferencas if d['tipo'] == 'ATUALIZAR'])
    print(f"\n  Novas (não estão no Excel): {novas}")
    print(f"  Atualizações: {atualizadas}")


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("\n" + "=" * 60)
    print("COMPARAÇÃO CSV vs EXCEL")
    print("=" * 60)

    # Carregar dados
    df_csv, df_excel = carregar_dados()
    if df_csv is None:
        return

    # Ler chaves
    chaves = ler_chaves()
    if not chaves:
        print("Nenhuma chave informada!")
        return

    print(f"\nChaves recebidas: {len(chaves)}")

    # Comparar
    diferencas = comparar_chaves(chaves, df_csv, df_excel)

    # Gerar Excel
    gerar_excel(diferencas, OUTPUT_PATH)

    print("\nConcluído!")


if __name__ == "__main__":
    main()
