#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gera resumo semanal das ofertas encerradas nos últimos 7 dias.
Output: Excel com 22 colunas para envio por email.
"""

import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Configuração
BASE_DIR = Path(__file__).parent
ENCERRADAS_FILE = BASE_DIR / "data" / "output" / "encerradas_2025.xlsx"
OUTPUT_DIR = BASE_DIR / "data" / "output"

# Mapeamento de coordenadores para abreviações
COORD_MAP = {
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
    'BANCO SAFRA': 'Safra',
    'CAIXA ECONOMICA FEDERAL': 'Caixa',
    'BANCO DO BRASIL': 'BB',
    'BANCO ABC BRASIL': 'ABC',
    'BANCO INTER': 'Inter',
    'BANCO PAN': 'Pan',
    'GENIAL INVESTIMENTOS': 'Genial',
    'TERRA INVESTIMENTOS': 'Terra',
    'OPEA': 'OPEA',
    'HABITASEC': 'Habitasec',
    'BNDES': 'BNDES',
    'OSLO': 'Oslo',
    'ATIVA': 'Ativa',
}

# Mapeamento de produtos
PRODUTO_MAP = {
    'Debêntures': 'Debêntures',
    'Certificados de Recebíveis Imobiliários': 'CRI',
    'Certificados de Recebíveis do Agronegócio': 'CRA',
    'Notas Comerciais': 'NC',
    'Certificados de Recebíveis': 'CR',
}


def abreviar_coordenador(nome):
    """Abrevia nome do coordenador."""
    if pd.isna(nome):
        return ''
    nome_upper = str(nome).upper().strip()
    for chave, abrev in COORD_MAP.items():
        if chave in nome_upper:
            return abrev
    # Se não encontrou, retorna as primeiras palavras
    partes = str(nome).split()
    if len(partes) >= 2:
        return partes[0][:3] + partes[1][:3]
    return str(nome)[:6]


def mapear_produto(tvm):
    """Mapeia TVM para sigla do produto."""
    if pd.isna(tvm):
        return ''
    tvm_str = str(tvm).strip()
    return PRODUTO_MAP.get(tvm_str, tvm_str)


def formatar_data(data):
    """Formata data para dd/mm/yyyy."""
    if pd.isna(data):
        return ''
    if isinstance(data, str):
        # Tenta parsear diferentes formatos
        for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d/%m/%y']:
            try:
                dt = datetime.strptime(data.split()[0], fmt)
                return dt.strftime('%d/%m/%Y')
            except:
                pass
        return data
    try:
        return data.strftime('%d/%m/%Y')
    except:
        return str(data)


def formatar_volume(valor):
    """Formata volume em R$ (100.000.000)."""
    if pd.isna(valor) or valor == 0:
        return ''
    try:
        return f"{int(float(valor)):,}".replace(',', '.')
    except:
        return str(valor)


def formatar_taxa_final(indexador, spread):
    """Combina indexador e spread para taxa final."""
    partes = []

    if pd.notna(indexador) and str(indexador).strip():
        idx = str(indexador).strip()
        # Padronizar nomes
        if 'DI' in idx.upper():
            idx = 'CDI'
        elif 'IPCA' in idx.upper():
            idx = 'IPCA'
        partes.append(idx)

    if pd.notna(spread) and spread != 0:
        try:
            spread_val = float(spread)
            if spread_val > 0:
                partes.append(f"+ {spread_val:.2f}%".replace('.', ','))
            else:
                partes.append(f"{spread_val:.2f}%".replace('.', ','))
        except:
            partes.append(str(spread))

    return ' '.join(partes) if partes else ''


def mapear_12431(valor):
    """Mapeia Lei 12431 para S/N."""
    if pd.isna(valor):
        return ''
    valor_str = str(valor).strip().lower()
    if valor_str in ['sim', 's', 'yes', 'true', '1']:
        return 'S'
    elif valor_str in ['não', 'nao', 'n', 'no', 'false', '0', 'não se aplica']:
        return 'N'
    return ''


def gerar_resumo_semanal(dias=7):
    """Gera resumo das encerradas dos últimos N dias."""

    print("=" * 60)
    print("RESUMO SEMANAL - ENCERRADAS")
    print("=" * 60)

    # Carregar encerradas
    if not ENCERRADAS_FILE.exists():
        print(f"ERRO: Arquivo não encontrado: {ENCERRADAS_FILE}")
        print("Execute primeiro: python construir_bases.py")
        sys.exit(1)

    df = pd.read_excel(ENCERRADAS_FILE)
    print(f"Total de séries carregadas: {len(df)}")

    # Converter data de encerramento
    df['Data Enc'] = pd.to_datetime(df['Data de encerramento da oferta'], errors='coerce')

    # Filtrar últimos N dias
    hoje = datetime.now()
    data_corte = hoje - timedelta(days=dias)

    df_filtrado = df[df['Data Enc'] >= data_corte].copy()
    print(f"Ofertas nos últimos {dias} dias: {len(df_filtrado)}")

    if len(df_filtrado) == 0:
        print(f"\nNenhuma oferta encerrada nos últimos {dias} dias.")
        print(f"Data de corte: {data_corte.strftime('%d/%m/%Y')}")

        # Mostrar as datas mais recentes
        datas_recentes = df['Data Enc'].dropna().sort_values(ascending=False).head(5)
        print("\nDatas de encerramento mais recentes:")
        for d in datas_recentes:
            print(f"  - {d.strftime('%d/%m/%Y')}")
        return None

    # Criar DataFrame de saída com as 22 colunas
    resumo = pd.DataFrame()

    # 1. Data Registro
    resumo['Data Registro'] = df_filtrado['Data de registro da oferta'].apply(formatar_data)

    # 2. Data Book (usando Data de emissão)
    resumo['Data Book'] = df_filtrado['Data de emissão'].apply(formatar_data)

    # 3. Status
    resumo['Status'] = df_filtrado['Status da oferta']

    # 4. Chave
    resumo['Chave'] = df_filtrado['Chave']

    # 5. Público (não disponível na ANBIMA - deixar vazio ou pegar da CVM)
    # TODO: Enriquecer encerradas com Público-alvo da CVM
    resumo['Público'] = ''

    # 6. Produto
    resumo['Produto'] = df_filtrado['TVM'].apply(mapear_produto)

    # 7. Emissor (para CRI/CRA usar Nome do devedor)
    def get_emissor(row):
        tvm = str(row.get('TVM', '')).upper()
        if 'CRI' in tvm or 'CRA' in tvm:
            devedor = row.get('Nome do devedor', '')
            if pd.notna(devedor) and str(devedor).strip():
                return str(devedor).strip()
        emissor = row.get('Emissor', '')
        return str(emissor).strip() if pd.notna(emissor) else ''

    resumo['Emissor'] = df_filtrado.apply(get_emissor, axis=1)

    # 8. Coordenadores
    resumo['Coordenadores'] = df_filtrado['Coordenador líder'].apply(abreviar_coordenador)

    # 9. Emissão
    resumo['Emissão'] = df_filtrado['Emissão']

    # 10. Série
    resumo['Série'] = df_filtrado['Série']

    # 11. Rating
    resumo['Rating'] = df_filtrado['Risco de crédito'].fillna('')

    # 12. Volume Inicial
    resumo['Volume Inicial'] = df_filtrado['Valor total emitido da série'].apply(formatar_volume)

    # 13. Volume Final
    resumo['Volume Final'] = df_filtrado['Valor total encerrado da série'].apply(formatar_volume)

    # 14. Data de Emissão
    resumo['Data de Emissão'] = df_filtrado['Data de emissão'].apply(formatar_data)

    # 15. Data de Vencimento
    resumo['Data de Vencimento'] = df_filtrado['Data de vencimento'].apply(formatar_data)

    # 16. Prazo
    resumo['Prazo'] = df_filtrado['Prazo série']

    # 17. Taxa Teto (não disponível na ANBIMA)
    resumo['Taxa Teto'] = ''

    # 18. Taxa Final (Indexador + Spread)
    resumo['Taxa Final'] = df_filtrado.apply(
        lambda row: formatar_taxa_final(row.get('Indexador'), row.get('Spread')),
        axis=1
    )

    # 19. 12.431
    resumo['12.431'] = df_filtrado['Lei 12431'].apply(mapear_12431)

    # 20. Venda % (Venda R$ / Valor total encerrado × 100)
    def calcular_venda_pct(row):
        venda = row.get('Venda R$', 0)
        total = row.get('Valor total encerrado da série', 0)
        if pd.notna(venda) and pd.notna(total) and total > 0:
            pct = (venda / total) * 100
            return f"{pct:.1f}%".replace('.', ',')
        return ''

    resumo['Venda %'] = df_filtrado.apply(calcular_venda_pct, axis=1)

    # 21. Venda R$
    resumo['Venda R$'] = df_filtrado['Venda R$'].apply(formatar_volume)

    # 22. Obs
    resumo['Obs'] = ''

    # Ordenar por data de encerramento (mais recente primeiro)
    resumo = resumo.sort_values('Data Registro', ascending=False)

    # Salvar
    data_hoje = hoje.strftime('%Y-%m-%d')
    output_file = OUTPUT_DIR / f"resumo_semanal_{data_hoje}.xlsx"

    resumo.to_excel(output_file, index=False, sheet_name='Resumo Semanal')

    print(f"\n{'=' * 60}")
    print(f"RESUMO GERADO")
    print(f"{'=' * 60}")
    print(f"Arquivo: {output_file}")
    print(f"Séries: {len(resumo)}")
    print(f"Colunas: {len(resumo.columns)}")
    print(f"Período: {data_corte.strftime('%d/%m/%Y')} a {hoje.strftime('%d/%m/%Y')}")

    # Resumo por produto
    if len(resumo) > 0:
        print(f"\nPor produto:")
        for prod in resumo['Produto'].value_counts().items():
            print(f"  {prod[0]}: {prod[1]}")

    return resumo


if __name__ == '__main__':
    # Permite passar número de dias como argumento
    dias = 7
    if len(sys.argv) > 1:
        try:
            dias = int(sys.argv[1])
        except ValueError:
            print(f"Uso: python resumo_semanal.py [dias]")
            print(f"  dias: número de dias para filtrar (padrão: 7)")
            sys.exit(1)

    gerar_resumo_semanal(dias)
