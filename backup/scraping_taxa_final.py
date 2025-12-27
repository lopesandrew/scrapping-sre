#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para fazer scraping de Taxa Final em ofertas encerradas.
Atualiza DCM_CVM.csv com os dados obtidos.
"""

import os
import sys
import pandas as pd

# Adicionar path para importar módulos do processador
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from processar_ofertas_cvm import CVMScraper

CSV_PATH = os.path.join(BASE_DIR, "DCM_CVM.csv")


def obter_ofertas_sem_taxa():
    """Retorna lista de chaves de ofertas encerradas sem Taxa Final."""
    df = pd.read_csv(CSV_PATH, sep=';', encoding='utf-8-sig')
    encerradas = df[(df['Status'] == 'Oferta Encerrada') & (df['Taxa Final'].isna())]
    return sorted(encerradas['Chave'].unique())


def fazer_scraping_ofertas(chaves):
    """Faz scraping das ofertas e retorna dados extraídos."""
    resultados = {}

    print(f"\nIniciando scraping de {len(chaves)} ofertas...")
    print("=" * 60)

    scraper = CVMScraper(headless=True)

    try:
        for i, chave in enumerate(chaves, 1):
            print(f"\n[{i}/{len(chaves)}] Processando chave {chave}...")

            try:
                dados = scraper.scrape_oferta(int(chave))

                if dados and dados.get('series'):
                    serie = dados['series'][0]
                    taxa_final = serie.get('taxa_final', '')
                    volume_final = serie.get('volume_final', '')

                    if taxa_final or volume_final:
                        resultados[chave] = {
                            'taxa_final': taxa_final,
                            'volume_final': volume_final
                        }
                        print(f"  ✓ Taxa Final: {taxa_final}")
                        print(f"  ✓ Volume Final: {volume_final}")
                    else:
                        print(f"  ⚠ Sem dados extraídos")
                else:
                    print(f"  ⚠ Sem dados retornados")

            except Exception as e:
                print(f"  ✗ Erro: {e}")

    finally:
        scraper.close()

    return resultados


def atualizar_csv(resultados):
    """Atualiza DCM_CVM.csv com os dados extraídos."""
    if not resultados:
        print("\nNenhum dado para atualizar.")
        return

    print(f"\n{'=' * 60}")
    print(f"Atualizando CSV com {len(resultados)} ofertas...")

    df = pd.read_csv(CSV_PATH, sep=';', encoding='utf-8-sig')

    atualizados = 0
    for chave, dados in resultados.items():
        mask = df['Chave'] == chave

        if dados.get('taxa_final'):
            df.loc[mask, 'Taxa Final'] = dados['taxa_final']
            atualizados += 1

        if dados.get('volume_final'):
            df.loc[mask, 'Volume Final'] = dados['volume_final']

    # Salvar
    df.to_csv(CSV_PATH, sep=';', encoding='utf-8-sig', index=False)

    print(f"✓ {atualizados} ofertas atualizadas em DCM_CVM.csv")


def main():
    print("\n" + "=" * 60)
    print("SCRAPING DE TAXA FINAL - OFERTAS ENCERRADAS")
    print("=" * 60)

    # Obter ofertas sem taxa
    chaves = obter_ofertas_sem_taxa()
    print(f"\nOfertas encerradas sem Taxa Final: {len(chaves)}")

    if not chaves:
        print("Nenhuma oferta para processar!")
        return

    # Fazer scraping
    resultados = fazer_scraping_ofertas(chaves)

    # Atualizar CSV
    atualizar_csv(resultados)

    print("\n" + "=" * 60)
    print("Concluído!")
    print("=" * 60)


if __name__ == "__main__":
    main()
