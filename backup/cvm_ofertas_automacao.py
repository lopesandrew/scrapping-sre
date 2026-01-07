"""
Script para automatizar coleta de dados de Ofertas Públicas da CVM
Autor: Andrew
Data: 2024-12-08

DUAS ABORDAGENS:
1. Via Portal Dados Abertos (RECOMENDADO) - atualizado diariamente
2. Via Selenium para scraping do site SRE (se necessário)
"""

import pandas as pd
import requests
from io import BytesIO
import zipfile
from datetime import datetime

# ============================================================================
# ABORDAGEM 1: PORTAL DADOS ABERTOS DA CVM (RECOMENDADA)
# ============================================================================

def download_ofertas_cvm():
    """
    Baixa e extrai o arquivo CSV completo de ofertas públicas
    Fonte: Portal Dados Abertos CVM (atualizado diariamente)
    """
    print("Baixando dados do Portal Dados Abertos da CVM...")
    
    url = "https://dados.cvm.gov.br/dados/OFERTA/DISTRIB/DADOS/oferta_distribuicao.zip"
    
    try:
        # Download do arquivo ZIP
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Extrair CSV do ZIP
        with zipfile.ZipFile(BytesIO(response.content)) as z:
            csv_filename = z.namelist()[0]  # Geralmente oferta_distribuicao.csv
            with z.open(csv_filename) as f:
                df = pd.read_csv(f, encoding='latin-1', sep=';', low_memory=False)
        
        print(f"✓ Dados carregados: {len(df)} ofertas públicas")
        print(f"✓ Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        
        return df
    
    except Exception as e:
        print(f"✗ Erro ao baixar dados: {e}")
        return None


def buscar_oferta_por_codigo(df, codigo_oferta):
    """
    Busca informações de uma oferta específica pelo código
    
    Args:
        df: DataFrame com todas as ofertas
        codigo_oferta: Código da oferta (ex: 21629)
    
    Returns:
        Series com dados da oferta
    """
    if df is None:
        return None
    
    # Tentar encontrar a coluna de código da oferta
    # Possíveis nomes: 'Codigo_Oferta', 'Cod_Oferta', 'ID_Oferta', etc.
    codigo_cols = [col for col in df.columns if 'codigo' in col.lower() or 'cod_' in col.lower()]
    
    if not codigo_cols:
        print(f"Colunas disponíveis: {df.columns.tolist()}")
        return None
    
    # Usar primeira coluna identificada como código
    col_codigo = codigo_cols[0]
    
    oferta = df[df[col_codigo] == int(codigo_oferta)]
    
    if not oferta.empty:
        return oferta.iloc[0]
    else:
        print(f"Oferta {codigo_oferta} não encontrada")
        return None


def exibir_colunas_disponiveis(df):
    """
    Exibe todas as colunas disponíveis no dataset
    """
    if df is not None:
        print("\n=== COLUNAS DISPONÍVEIS NO DATASET ===")
        for i, col in enumerate(df.columns, 1):
            print(f"{i}. {col}")
        print(f"\nTotal: {len(df.columns)} colunas")


def filtrar_ofertas_recentes(df, tipo_valor_mobiliario=None, dias=30):
    """
    Filtra ofertas recentes
    
    Args:
        df: DataFrame com todas as ofertas
        tipo_valor_mobiliario: Filtrar por tipo (ex: 'CRI', 'Debênture', etc.)
        dias: Número de dias para considerar como "recente"
    
    Returns:
        DataFrame filtrado
    """
    if df is None:
        return None
    
    # Tentar identificar coluna de data
    data_cols = [col for col in df.columns if 'data' in col.lower() and 'registro' in col.lower()]
    
    if data_cols:
        col_data = data_cols[0]
        
        # Converter para datetime
        df[col_data] = pd.to_datetime(df[col_data], errors='coerce')
        
        # Filtrar últimos X dias
        data_limite = pd.Timestamp.now() - pd.Timedelta(days=dias)
        df_recente = df[df[col_data] >= data_limite]
        
        if tipo_valor_mobiliario:
            tipo_cols = [col for col in df.columns if 'tipo' in col.lower() and 'valor' in col.lower()]
            if tipo_cols:
                df_recente = df_recente[df_recente[tipo_cols[0]].str.contains(tipo_valor_mobiliario, case=False, na=False)]
        
        return df_recente
    
    return df


# ============================================================================
# ABORDAGEM 2: SELENIUM PARA SCRAPING DO SITE SRE (SE NECESSÁRIO)
# ============================================================================

def scraping_site_sre_selenium(codigo_oferta):
    """
    Scraping do site SRE da CVM usando Selenium
    NOTA: Requer instalação de: pip install selenium webdriver-manager
    
    Args:
        codigo_oferta: Código da oferta (ex: 21629)
    
    Returns:
        Dict com informações extraídas
    """
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        from selenium.webdriver.chrome.options import Options
        
        print(f"\nIniciando scraping do site SRE para oferta {codigo_oferta}...")
        
        # Configurar Chrome headless
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        # Inicializar driver
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        
        # Acessar página
        url = f"https://web.cvm.gov.br/sre-publico-cvm/#/oferta-publica/{codigo_oferta}"
        driver.get(url)
        
        # Aguardar carregamento da página (SPA com Angular/React)
        wait = WebDriverWait(driver, 10)
        
        # Aguardar elemento que contém o status
        # NOTA: Você precisará inspecionar o site para identificar os seletores corretos
        status_element = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "selector-do-status-aqui"))
        )
        
        status = status_element.text
        
        # Extrair outras informações relevantes
        dados = {
            'status': status,
            'codigo': codigo_oferta,
            # Adicionar outros campos conforme necessário
        }
        
        driver.quit()
        
        return dados
    
    except ImportError:
        print("✗ Selenium não instalado. Execute: pip install selenium webdriver-manager")
        return None
    
    except Exception as e:
        print(f"✗ Erro no scraping: {e}")
        return None


# ============================================================================
# EXEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    print("=== AUTOMAÇÃO DE COLETA DE OFERTAS PÚBLICAS DA CVM ===\n")
    
    # ABORDAGEM 1: Usar dados abertos (RECOMENDADO)
    print("1. Baixando dados do Portal Dados Abertos...")
    df_ofertas = download_ofertas_cvm()
    
    if df_ofertas is not None:
        # Exibir informações gerais
        print(f"\n✓ Dataset carregado com sucesso")
        print(f"  - Total de ofertas: {len(df_ofertas):,}")
        print(f"  - Colunas disponíveis: {len(df_ofertas.columns)}")
        
        # Exibir primeiras colunas para entender estrutura
        print("\n=== PRIMEIRAS 10 COLUNAS ===")
        for col in df_ofertas.columns[:10]:
            print(f"  - {col}")
        
        print("\n... (use exibir_colunas_disponiveis() para ver todas)")
        
        # Buscar oferta específica (exemplo: 21629)
        codigo_busca = 21629
        print(f"\n2. Buscando oferta código {codigo_busca}...")
        oferta = buscar_oferta_por_codigo(df_ofertas, codigo_busca)
        
        if oferta is not None:
            print(f"\n✓ Oferta {codigo_busca} encontrada!")
            print("\nPrincipais informações:")
            
            # Exibir campos relevantes (ajustar conforme colunas reais)
            campos_importantes = ['Tipo_Valor_Mobiliario', 'Data_Registro', 'Emissor', 
                                'Modalidade_Registro', 'Situacao', 'Status']
            
            for campo in campos_importantes:
                if campo in oferta.index:
                    print(f"  - {campo}: {oferta[campo]}")
        
        # Filtrar ofertas recentes de CRI
        print("\n3. Exemplo: Filtrando CRIs recentes...")
        cris_recentes = filtrar_ofertas_recentes(df_ofertas, tipo_valor_mobiliario='CRI', dias=30)
        if cris_recentes is not None and not cris_recentes.empty:
            print(f"✓ Encontrados {len(cris_recentes)} CRIs nos últimos 30 dias")
        
        # Salvar base completa em Excel para análise
        print("\n4. Salvando base completa em Excel...")
        output_file = f"ofertas_cvm_{datetime.now().strftime('%Y%m%d')}.xlsx"
        df_ofertas.to_excel(output_file, index=False)
        print(f"✓ Arquivo salvo: {output_file}")
    
    print("\n" + "="*60)
    print("NOTA: A abordagem 2 (Selenium) só é necessária se você")
    print("      precisar de dados que NÃO estão no Portal Dados Abertos.")
    print("="*60)
