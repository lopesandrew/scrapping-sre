"""
TESTE RÁPIDO: Buscar Status da Oferta 21629
Execução: python teste_rapido_cvm.py
"""

import pandas as pd
import requests
from io import BytesIO
import zipfile

print("="*70)
print("TESTE: Busca de Oferta CVM via Portal Dados Abertos")
print("="*70)

# 1. Download e extração
print("\n[1/3] Baixando dados da CVM...")
url = "https://dados.cvm.gov.br/dados/OFERTA/DISTRIB/DADOS/oferta_distribuicao.zip"

try:
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    print("✓ Download concluído")
    
    # 2. Carregar CSV
    print("\n[2/3] Extraindo e carregando CSV...")
    with zipfile.ZipFile(BytesIO(response.content)) as z:
        csv_name = z.namelist()[0]
        with z.open(csv_name) as f:
            df = pd.read_csv(f, encoding='latin-1', sep=';', low_memory=False)
    
    print(f"✓ {len(df):,} ofertas carregadas")
    print(f"✓ {len(df.columns)} colunas disponíveis")
    
    # 3. Mostrar estrutura
    print("\n[3/3] Estrutura do dataset:")
    print("\nPrimeiras 15 colunas:")
    for i, col in enumerate(df.columns[:15], 1):
        print(f"  {i:2d}. {col}")
    
    print(f"\n... e mais {len(df.columns) - 15} colunas")
    
    # 4. Buscar oferta específica
    print("\n" + "="*70)
    print("BUSCA: Oferta 21629")
    print("="*70)
    
    # Tentar diferentes colunas possíveis para código
    colunas_codigo = [col for col in df.columns if any(x in col.lower() for x in ['codigo', 'cod_', 'numero', 'num_'])]
    
    print(f"\nColunas identificadas como possível código: {colunas_codigo}")
    
    encontrada = False
    for col in colunas_codigo:
        try:
            # Converter para numérico se necessário
            df[col] = pd.to_numeric(df[col], errors='coerce')
            oferta = df[df[col] == 21629]
            
            if not oferta.empty:
                print(f"\n✓ OFERTA ENCONTRADA na coluna '{col}'!\n")
                print("INFORMAÇÕES:")
                print("-" * 70)
                
                # Exibir todos os dados da oferta
                for campo, valor in oferta.iloc[0].items():
                    if pd.notna(valor) and str(valor).strip():  # Apenas valores não vazios
                        print(f"{campo:40s}: {valor}")
                
                encontrada = True
                break
        except:
            continue
    
    if not encontrada:
        print("\n⚠️ Oferta 21629 não encontrada no dataset")
        print("\nSugestão: Verificar se o código está correto ou se a oferta")
        print("          ainda não foi incluída no Portal Dados Abertos")
    
    # 5. Salvar amostra em Excel para inspeção
    print("\n" + "="*70)
    print("EXPORTANDO amostra para Excel...")
    print("="*70)
    
    # Salvar primeiras 100 linhas + coluna de códigos
    df_sample = df.head(100)
    output_file = "amostra_ofertas_cvm.xlsx"
    df_sample.to_excel(output_file, index=False)
    print(f"✓ Arquivo salvo: {output_file}")
    print("  (Use este arquivo para entender a estrutura dos dados)")
    
except requests.exceptions.RequestException as e:
    print(f"\n✗ ERRO no download: {e}")
    print("\nPossíveis causas:")
    print("  1. Sem conexão com internet")
    print("  2. Firewall bloqueando acesso")
    print("  3. Site da CVM temporariamente indisponível")
    
except Exception as e:
    print(f"\n✗ ERRO: {e}")
    print(f"Tipo: {type(e).__name__}")

print("\n" + "="*70)
print("Teste concluído!")
print("="*70)
