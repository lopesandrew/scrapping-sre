#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Conferência de Dados CVM
==================================
Script interativo para conferir dados processados pelo script automático.
Permite comparar valores com a fonte original (CSV CVM) e página web.

Autor: Andrew Lopes / Claude Code
Data: Dezembro 2024
"""

import os
import webbrowser
import pandas as pd
from datetime import datetime

# =============================================================================
# CONFIGURAÇÕES
# =============================================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_CSV_PATH = os.path.join(BASE_DIR, "DCM_CVM.csv")
SOURCE_CSV_PATH = os.path.join(BASE_DIR, "oferta_resolucao_160.csv")
CONFERENCIAS_PATH = os.path.join(BASE_DIR, "conferencias.csv")

# URL base para abrir página da CVM
CVM_BASE_URL = "https://web.cvm.gov.br/sre-publico-cvm/#/oferta-publica/"

# Colunas para conferência (selecionadas pelo usuário)
COLUNAS_CONFERIR = {
    # Colunas do CSV (comparar com fonte original)
    'csv': {
        'Emissor': 'Nome_Emissor',  # ou Identificacao_devedores_coobrigados para CRA/CRI
        'Volume Inicial': 'Valor_Total_Registrado',
        'Tipo Lastro': 'Tipo_lastro',
        'Garantias': 'Descricao_garantias',
        'Lastro': 'Descricao_lastro',
        'Destinação Recursos': 'Destinacao_recursos',
    },
    # Colunas do Scraping (verificar na página web)
    'scraping': [
        'Rating',
        'Volume Final',
        'Taxa Teto',
        'Taxa Final',
    ]
}


# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

def carregar_dados():
    """Carrega os arquivos CSV necessários."""
    if not os.path.exists(OUTPUT_CSV_PATH):
        print(f"ERRO: Arquivo não encontrado: {OUTPUT_CSV_PATH}")
        return None, None

    if not os.path.exists(SOURCE_CSV_PATH):
        print(f"ERRO: Arquivo fonte não encontrado: {SOURCE_CSV_PATH}")
        return None, None

    df_processado = pd.read_csv(OUTPUT_CSV_PATH, sep=';', encoding='utf-8-sig')
    df_fonte = pd.read_csv(SOURCE_CSV_PATH, sep=';', encoding='latin-1', low_memory=False)

    # Limpar nomes das colunas do fonte
    df_fonte.columns = [c.replace('ï»¿', '').replace('\ufeff', '') for c in df_fonte.columns]

    return df_processado, df_fonte


def carregar_conferencias():
    """Carrega o histórico de conferências."""
    if os.path.exists(CONFERENCIAS_PATH):
        return pd.read_csv(CONFERENCIAS_PATH, sep=';', encoding='utf-8-sig')
    return pd.DataFrame(columns=['Chave', 'Data_Conferencia', 'Status', 'Observacao'])


def salvar_conferencia(chave, status, observacao=''):
    """Salva uma conferência no histórico."""
    df_conf = carregar_conferencias()

    nova_conf = {
        'Chave': chave,
        'Data_Conferencia': datetime.now().strftime('%d/%m/%Y %H:%M'),
        'Status': status,
        'Observacao': observacao
    }

    # Remover conferência anterior da mesma chave (se existir)
    df_conf = df_conf[df_conf['Chave'] != chave]

    # Adicionar nova conferência
    df_conf = pd.concat([df_conf, pd.DataFrame([nova_conf])], ignore_index=True)

    df_conf.to_csv(CONFERENCIAS_PATH, sep=';', encoding='utf-8-sig', index=False)


def abrir_pagina_cvm(chave):
    """Abre a página da oferta no navegador."""
    url = f"{CVM_BASE_URL}{chave}"
    print(f"\nAbrindo: {url}")
    webbrowser.open(url)


def formatar_valor(valor, max_len=60):
    """Formata valor para exibição, truncando se necessário."""
    if pd.isna(valor) or valor == '':
        return '[vazio]'
    valor_str = str(valor).strip()
    if len(valor_str) > max_len:
        return valor_str[:max_len] + '...'
    return valor_str


def exibir_comparacao(row_processado, row_fonte, chave):
    """Exibe comparação lado a lado dos valores."""
    print("\n" + "=" * 80)
    print(f"CONFERÊNCIA - Chave: {chave}")
    print(f"Emissor: {row_processado.get('Emissor', 'N/A')}")
    print(f"Produto: {row_processado.get('Produto', 'N/A')}")
    print("=" * 80)

    # Colunas do CSV
    print("\n--- DADOS DO CSV (comparar com fonte original) ---\n")
    print(f"{'Campo':<25} {'Processado':<30} {'Fonte Original':<30}")
    print("-" * 85)

    for col_proc, col_fonte in COLUNAS_CONFERIR['csv'].items():
        valor_proc = formatar_valor(row_processado.get(col_proc, ''))

        # Para Emissor, verificar se é CRA/CRI (usar Identificacao_devedores_coobrigados)
        if col_proc == 'Emissor' and row_processado.get('Produto', '') in ['CRA', 'CRI', 'CR', 'CPR-F']:
            col_fonte = 'Identificacao_devedores_coobrigados'

        valor_fonte = formatar_valor(row_fonte.get(col_fonte, '') if row_fonte is not None else '')
        print(f"{col_proc:<25} {valor_proc:<30} {valor_fonte:<30}")

    # Colunas do Scraping
    print("\n--- DADOS DO SCRAPING (verificar na página web) ---\n")
    print(f"{'Campo':<25} {'Valor Atual':<50}")
    print("-" * 75)

    for col in COLUNAS_CONFERIR['scraping']:
        valor = formatar_valor(row_processado.get(col, ''), max_len=50)
        print(f"{col:<25} {valor:<50}")


def listar_pendentes(df_processado, df_conferencias):
    """Lista ofertas pendentes de conferência."""
    chaves_conferidas = set(df_conferencias['Chave'].dropna().astype(int)) if len(df_conferencias) > 0 else set()
    chaves_processadas = set(df_processado['Chave'].dropna().astype(int))

    pendentes = chaves_processadas - chaves_conferidas
    return list(pendentes)


def listar_todas(df_processado):
    """Lista todas as ofertas processadas."""
    return list(df_processado['Chave'].dropna().astype(int).unique())


# =============================================================================
# MENU INTERATIVO
# =============================================================================

def menu_principal():
    """Menu principal do script."""
    print("\n" + "=" * 50)
    print("CONFERÊNCIA DE DADOS CVM")
    print("=" * 50)
    print("\n1. Conferir ofertas pendentes")
    print("2. Conferir oferta específica (por Chave)")
    print("3. Ver relatório de conferências")
    print("4. Listar todas as ofertas")
    print("0. Sair")

    return input("\nEscolha uma opção: ").strip()


def menu_conferencia(chave, row_processado, row_fonte):
    """Menu de conferência de uma oferta."""
    exibir_comparacao(row_processado, row_fonte, chave)

    print("\n--- AÇÕES ---")
    print("1. Marcar como OK")
    print("2. Marcar como PENDENTE (precisa correção)")
    print("3. Abrir página da CVM")
    print("4. Pular (não conferir agora)")
    print("0. Voltar ao menu")

    return input("\nEscolha: ").strip()


def conferir_oferta(chave, df_processado, df_fonte):
    """Processo de conferência de uma oferta."""
    # Buscar dados processados
    row_proc = df_processado[df_processado['Chave'] == chave]
    if len(row_proc) == 0:
        print(f"Chave {chave} não encontrada na base processada.")
        return False
    row_proc = row_proc.iloc[0]

    # Buscar dados fonte
    row_fonte = df_fonte[df_fonte['Numero_Requerimento'] == chave]
    row_fonte = row_fonte.iloc[0] if len(row_fonte) > 0 else None

    while True:
        opcao = menu_conferencia(chave, row_proc, row_fonte)

        if opcao == '1':
            obs = input("Observação (Enter para pular): ").strip()
            salvar_conferencia(chave, 'OK', obs)
            print(f"\nOferta {chave} marcada como OK!")
            return True

        elif opcao == '2':
            obs = input("Descreva o problema: ").strip()
            salvar_conferencia(chave, 'PENDENTE', obs)
            print(f"\nOferta {chave} marcada como PENDENTE!")
            return True

        elif opcao == '3':
            abrir_pagina_cvm(chave)
            input("\nPressione Enter para continuar...")

        elif opcao == '4':
            print("Pulando...")
            return False

        elif opcao == '0':
            return False


def conferir_pendentes(df_processado, df_fonte, df_conferencias):
    """Confere todas as ofertas pendentes."""
    pendentes = listar_pendentes(df_processado, df_conferencias)

    if not pendentes:
        print("\nNenhuma oferta pendente de conferência!")
        return

    print(f"\n{len(pendentes)} ofertas pendentes de conferência.")

    for i, chave in enumerate(pendentes, 1):
        print(f"\n[{i}/{len(pendentes)}] Conferindo chave {chave}...")
        resultado = conferir_oferta(chave, df_processado, df_fonte)

        if not resultado:
            continuar = input("\nContinuar para próxima? (s/n): ").strip().lower()
            if continuar != 's':
                break


def ver_relatorio(df_conferencias):
    """Exibe relatório de conferências."""
    if len(df_conferencias) == 0:
        print("\nNenhuma conferência realizada ainda.")
        return

    print("\n" + "=" * 70)
    print("RELATÓRIO DE CONFERÊNCIAS")
    print("=" * 70)

    total = len(df_conferencias)
    ok = len(df_conferencias[df_conferencias['Status'] == 'OK'])
    pendente = len(df_conferencias[df_conferencias['Status'] == 'PENDENTE'])

    print(f"\nTotal conferidas: {total}")
    print(f"OK: {ok}")
    print(f"Pendentes: {pendente}")

    if pendente > 0:
        print("\n--- OFERTAS PENDENTES DE CORREÇÃO ---\n")
        df_pend = df_conferencias[df_conferencias['Status'] == 'PENDENTE']
        for _, row in df_pend.iterrows():
            print(f"Chave: {int(row['Chave'])} - {row['Observacao']}")


def listar_ofertas(df_processado):
    """Lista todas as ofertas com informações básicas."""
    print("\n" + "=" * 90)
    print("LISTA DE OFERTAS PROCESSADAS")
    print("=" * 90)

    print(f"\n{'Chave':<10} {'Status':<20} {'Produto':<12} {'Emissor':<40}")
    print("-" * 90)

    for _, row in df_processado.iterrows():
        chave = int(row['Chave']) if not pd.isna(row['Chave']) else 0
        status = str(row.get('Status', ''))[:18]
        produto = str(row.get('Produto', ''))[:10]
        emissor = str(row.get('Emissor', ''))[:38]
        print(f"{chave:<10} {status:<20} {produto:<12} {emissor:<40}")

    print(f"\nTotal: {len(df_processado)} ofertas")


# =============================================================================
# EXECUÇÃO PRINCIPAL
# =============================================================================

def main():
    """Função principal."""
    print("\nCarregando dados...")
    df_processado, df_fonte = carregar_dados()

    if df_processado is None:
        return

    df_conferencias = carregar_conferencias()

    print(f"Base carregada: {len(df_processado)} ofertas processadas")
    print(f"Conferências realizadas: {len(df_conferencias)}")

    while True:
        opcao = menu_principal()

        if opcao == '1':
            conferir_pendentes(df_processado, df_fonte, df_conferencias)
            df_conferencias = carregar_conferencias()  # Recarregar

        elif opcao == '2':
            chave_str = input("\nDigite a Chave da oferta: ").strip()
            try:
                chave = int(chave_str)
                conferir_oferta(chave, df_processado, df_fonte)
                df_conferencias = carregar_conferencias()  # Recarregar
            except ValueError:
                print("Chave inválida!")

        elif opcao == '3':
            ver_relatorio(df_conferencias)

        elif opcao == '4':
            listar_ofertas(df_processado)

        elif opcao == '0':
            print("\nAté logo!")
            break

        else:
            print("Opção inválida!")


if __name__ == "__main__":
    main()
