"""
Script de Atualização da Base de Dados de Ofertas Públicas CVM
Autor: Andrew (BOCOM BBM)
Data: 2024-12-08

Funcionalidades:
- Download automático dos dados do Portal Dados Abertos da CVM
- Sistema de backup automático da versão anterior
- Logs detalhados de execução
- Comparação entre versões (novas ofertas, atualizações)
- Organização em pastas estruturadas
- Relatório de execução

Uso:
    python atualizar_base_cvm.py
"""

import pandas as pd
import requests
from io import BytesIO
import zipfile
from datetime import datetime
import os
import shutil
import logging
from pathlib import Path


# ============================================================================
# CONFIGURAÇÕES
# ============================================================================

# Diretórios
BASE_DIR = Path(__file__).parent
DATA_RAW_DIR = BASE_DIR / 'data' / 'raw'
DATA_PROCESSED_DIR = BASE_DIR / 'data' / 'processed'
DATA_BACKUP_DIR = BASE_DIR / 'data' / 'backup'
LOGS_DIR = BASE_DIR / 'logs'

# URLs do Portal Dados Abertos da CVM
# NOTA: Ambos os arquivos estão dentro do mesmo ZIP
CVM_URL = "https://dados.cvm.gov.br/dados/OFERTA/DISTRIB/DADOS/oferta_distribuicao.zip"

# Nomes dos arquivos
ARQUIVO_RAW_HISTORICO = "oferta_distribuicao.csv"
ARQUIVO_RAW_RESOLUCAO_160 = "oferta_resolucao_160.csv"
ARQUIVO_PROCESSED_HISTORICO = "ofertas_cvm_historico.xlsx"
ARQUIVO_PROCESSED_RESOLUCAO_160 = "ofertas_cvm_resolucao_160.xlsx"


# ============================================================================
# CONFIGURAÇÃO DE LOGS
# ============================================================================

def configurar_logs():
    """Configura sistema de logs com arquivo e console"""

    # Criar diretório de logs se não existir
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    # Nome do arquivo de log com timestamp
    log_filename = LOGS_DIR / 'cvm_atualizacao.log'

    # Configurar formato dos logs
    log_format = '%(asctime)s | %(levelname)-8s | %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'

    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler()  # Também exibe no console
        ]
    )

    return logging.getLogger(__name__)


# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def criar_estrutura_diretorios():
    """Cria estrutura de diretórios necessária"""

    diretorios = [DATA_RAW_DIR, DATA_PROCESSED_DIR, DATA_BACKUP_DIR, LOGS_DIR]

    for diretorio in diretorios:
        diretorio.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Diretório verificado: {diretorio}")


def fazer_backup_arquivo_anterior(nome_arquivo):
    """
    Faz backup do arquivo processado anterior

    Args:
        nome_arquivo: Nome do arquivo Excel a fazer backup
    """

    arquivo_atual = DATA_PROCESSED_DIR / nome_arquivo

    if arquivo_atual.exists():
        # Nome do backup com timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        # Extrair nome base sem extensão
        nome_base = nome_arquivo.replace('.xlsx', '')
        arquivo_backup = DATA_BACKUP_DIR / f"{nome_base}_backup_{timestamp}.xlsx"

        try:
            shutil.copy2(arquivo_atual, arquivo_backup)
            logger.info(f"✓ Backup criado: {arquivo_backup.name}")
            return True
        except Exception as e:
            logger.error(f"✗ Erro ao criar backup: {e}")
            return False
    else:
        logger.info("• Primeira execução - sem arquivo anterior para backup")
        return True


def limpar_backups_antigos(dias_manter=30):
    """Remove backups com mais de X dias"""

    try:
        if not DATA_BACKUP_DIR.exists():
            return

        limite_data = datetime.now().timestamp() - (dias_manter * 24 * 60 * 60)
        backups_removidos = 0

        # Remover backups de ambos os arquivos
        for arquivo in DATA_BACKUP_DIR.glob('*_backup_*.xlsx'):
            if arquivo.stat().st_mtime < limite_data:
                arquivo.unlink()
                backups_removidos += 1

        if backups_removidos > 0:
            logger.info(f"✓ {backups_removidos} backup(s) antigo(s) removido(s)")

    except Exception as e:
        logger.warning(f"⚠ Erro ao limpar backups antigos: {e}")


# ============================================================================
# DOWNLOAD E PROCESSAMENTO
# ============================================================================

def download_dados_cvm_completo():
    """
    Baixa o ZIP da CVM e extrai AMBOS os arquivos CSV:
    - oferta_distribuicao.csv (histórico completo 1988-2025)
    - oferta_resolucao_160.csv (Resolução 160, 2023-2025)

    Returns:
        Tupla (df_historico, df_resolucao_160) ou (None, None) em caso de erro
    """

    logger.info("Baixando arquivo ZIP da CVM...")
    logger.info(f"URL: {CVM_URL}")

    try:
        # Download do arquivo ZIP
        response = requests.get(CVM_URL, timeout=60)
        response.raise_for_status()

        tamanho_mb = len(response.content) / (1024 * 1024)
        logger.info(f"✓ Download concluído ({tamanho_mb:.2f} MB)")

        # Extrair ambos os CSVs do ZIP
        df_historico = None
        df_resolucao_160 = None

        with zipfile.ZipFile(BytesIO(response.content)) as z:
            logger.info(f"• Arquivos no ZIP: {', '.join(z.namelist())}")

            # Extrair oferta_distribuicao.csv (histórico)
            if ARQUIVO_RAW_HISTORICO in z.namelist():
                logger.info(f"• Extraindo {ARQUIVO_RAW_HISTORICO}...")
                with z.open(ARQUIVO_RAW_HISTORICO) as f:
                    df_historico = pd.read_csv(f, encoding='latin-1', sep=';', low_memory=False)
                logger.info(f"✓ Histórico: {len(df_historico):,} ofertas | {len(df_historico.columns)} colunas")

                # Salvar CSV raw
                arquivo_raw = DATA_RAW_DIR / ARQUIVO_RAW_HISTORICO
                df_historico.to_csv(arquivo_raw, index=False, encoding='utf-8-sig', sep=';')
                logger.info(f"✓ CSV raw salvo: {ARQUIVO_RAW_HISTORICO}")

            # Extrair oferta_resolucao_160.csv
            if ARQUIVO_RAW_RESOLUCAO_160 in z.namelist():
                logger.info(f"• Extraindo {ARQUIVO_RAW_RESOLUCAO_160}...")
                with z.open(ARQUIVO_RAW_RESOLUCAO_160) as f:
                    df_resolucao_160 = pd.read_csv(f, encoding='latin-1', sep=';', low_memory=False)
                logger.info(f"✓ Resolução 160: {len(df_resolucao_160):,} ofertas | {len(df_resolucao_160.columns)} colunas")

                # Salvar CSV raw
                arquivo_raw = DATA_RAW_DIR / ARQUIVO_RAW_RESOLUCAO_160
                df_resolucao_160.to_csv(arquivo_raw, index=False, encoding='utf-8-sig', sep=';')
                logger.info(f"✓ CSV raw salvo: {ARQUIVO_RAW_RESOLUCAO_160}")

        return df_historico, df_resolucao_160

    except requests.exceptions.Timeout:
        logger.error("✗ Erro: Timeout ao baixar dados (>60s)")
        return None, None

    except requests.exceptions.RequestException as e:
        logger.error(f"✗ Erro na requisição HTTP: {e}")
        return None, None

    except zipfile.BadZipFile:
        logger.error("✗ Erro: Arquivo ZIP corrompido")
        return None, None

    except Exception as e:
        logger.error(f"✗ Erro inesperado no download: {e}")
        return None, None


def download_dados_cvm_zip(url, nome_arquivo_raw):
    """
    Baixa arquivo ZIP da CVM e extrai o CSV

    Args:
        url: URL do arquivo ZIP
        nome_arquivo_raw: Nome para salvar o CSV extraído

    Returns:
        DataFrame com os dados ou None em caso de erro
    """

    logger.info(f"Baixando {nome_arquivo_raw}...")
    logger.info(f"URL: {url}")

    try:
        # Download do arquivo ZIP
        response = requests.get(url, timeout=60)
        response.raise_for_status()

        tamanho_mb = len(response.content) / (1024 * 1024)
        logger.info(f"✓ Download concluído ({tamanho_mb:.2f} MB)")

        # Extrair CSV do ZIP
        with zipfile.ZipFile(BytesIO(response.content)) as z:
            csv_filename = z.namelist()[0]
            logger.info(f"• Extraindo arquivo: {csv_filename}")

            with z.open(csv_filename) as f:
                df = pd.read_csv(f, encoding='latin-1', sep=';', low_memory=False)

        logger.info(f"✓ Dados carregados: {len(df):,} ofertas | {len(df.columns)} colunas")

        # Salvar CSV raw
        arquivo_raw = DATA_RAW_DIR / nome_arquivo_raw
        df.to_csv(arquivo_raw, index=False, encoding='utf-8-sig', sep=';')
        logger.info(f"✓ CSV raw salvo: {nome_arquivo_raw}")

        return df

    except requests.exceptions.Timeout:
        logger.error("✗ Erro: Timeout ao baixar dados (>60s)")
        return None

    except requests.exceptions.RequestException as e:
        logger.error(f"✗ Erro na requisição HTTP: {e}")
        return None

    except zipfile.BadZipFile:
        logger.error("✗ Erro: Arquivo ZIP corrompido")
        return None

    except Exception as e:
        logger.error(f"✗ Erro inesperado no download: {e}")
        return None


def download_dados_cvm_csv(url, nome_arquivo_raw):
    """
    Baixa arquivo CSV diretamente (sem ZIP) da CVM

    Args:
        url: URL do arquivo CSV
        nome_arquivo_raw: Nome para salvar o CSV raw

    Returns:
        DataFrame com os dados ou None em caso de erro
    """

    logger.info(f"Baixando {nome_arquivo_raw}...")
    logger.info(f"URL: {url}")

    try:
        # Download do arquivo CSV
        response = requests.get(url, timeout=60)
        response.raise_for_status()

        tamanho_mb = len(response.content) / (1024 * 1024)
        logger.info(f"✓ Download concluído ({tamanho_mb:.2f} MB)")

        # Ler CSV com encoding latin-1
        df = pd.read_csv(BytesIO(response.content), encoding='latin-1', sep=';', low_memory=False)

        logger.info(f"✓ Dados carregados: {len(df):,} ofertas | {len(df.columns)} colunas")

        # Salvar CSV raw
        arquivo_raw = DATA_RAW_DIR / nome_arquivo_raw
        df.to_csv(arquivo_raw, index=False, encoding='utf-8-sig', sep=';')
        logger.info(f"✓ CSV raw salvo: {nome_arquivo_raw}")

        return df

    except requests.exceptions.Timeout:
        logger.error("✗ Erro: Timeout ao baixar dados (>60s)")
        return None

    except requests.exceptions.RequestException as e:
        logger.error(f"✗ Erro na requisição HTTP: {e}")
        return None

    except Exception as e:
        logger.error(f"✗ Erro inesperado no download: {e}")
        return None


def comparar_com_versao_anterior(df_novo, nome_arquivo):
    """
    Compara versão nova com a anterior e gera estatísticas

    Args:
        df_novo: DataFrame com os dados novos
        nome_arquivo: Nome do arquivo Excel a comparar

    Returns:
        Dict com estatísticas da comparação
    """

    arquivo_anterior = DATA_PROCESSED_DIR / nome_arquivo

    if not arquivo_anterior.exists():
        logger.info("• Primeira execução - sem comparação disponível")
        return {
            'primeira_execucao': True,
            'ofertas_novas': len(df_novo),
            'ofertas_atualizadas': 0,
            'total_anterior': 0,
            'total_novo': len(df_novo)
        }

    try:
        logger.info("Comparando com versão anterior...")
        df_anterior = pd.read_excel(arquivo_anterior)

        # Identificar coluna de código
        codigo_cols = [col for col in df_novo.columns if 'codigo' in col.lower() or 'cod' in col.lower()]

        if not codigo_cols:
            logger.warning("⚠ Coluna de código não identificada - comparação limitada")
            return {
                'primeira_execucao': False,
                'ofertas_novas': '?',
                'ofertas_atualizadas': '?',
                'total_anterior': len(df_anterior),
                'total_novo': len(df_novo),
                'diferenca': len(df_novo) - len(df_anterior)
            }

        col_codigo = codigo_cols[0]

        # Identificar ofertas novas
        codigos_anteriores = set(df_anterior[col_codigo].unique())
        codigos_novos = set(df_novo[col_codigo].unique())

        ofertas_novas = codigos_novos - codigos_anteriores
        ofertas_removidas = codigos_anteriores - codigos_novos

        stats = {
            'primeira_execucao': False,
            'ofertas_novas': len(ofertas_novas),
            'ofertas_removidas': len(ofertas_removidas),
            'ofertas_mantidas': len(codigos_anteriores & codigos_novos),
            'total_anterior': len(df_anterior),
            'total_novo': len(df_novo),
            'diferenca': len(df_novo) - len(df_anterior)
        }

        logger.info(f"✓ Ofertas novas: {stats['ofertas_novas']}")
        logger.info(f"✓ Ofertas removidas: {stats['ofertas_removidas']}")
        logger.info(f"✓ Total anterior: {stats['total_anterior']:,} → Novo: {stats['total_novo']:,}")

        return stats

    except Exception as e:
        logger.warning(f"⚠ Erro na comparação: {e}")
        return {
            'primeira_execucao': False,
            'erro': str(e),
            'total_novo': len(df_novo)
        }


def limpar_caracteres_invalidos(df):
    """
    Remove caracteres inválidos para Excel de todas as colunas de texto

    Args:
        df: DataFrame a limpar

    Returns:
        DataFrame limpo
    """
    import re

    # Caracteres de controle inválidos no Excel (exceto \t, \n, \r)
    # Refs: https://stackoverflow.com/questions/31848648/
    ILLEGAL_CHARACTERS_RE = re.compile(r'[\000-\010]|[\013-\014]|[\016-\037]')

    # Limpar colunas de texto
    for col in df.columns:
        if df[col].dtype == 'object':  # Colunas de texto
            df[col] = df[col].apply(
                lambda x: ILLEGAL_CHARACTERS_RE.sub('', str(x)) if pd.notna(x) else x
            )

    return df


def processar_e_salvar(df, nome_arquivo):
    """
    Processa dados e salva em Excel formatado

    Args:
        df: DataFrame com os dados
        nome_arquivo: Nome do arquivo Excel a salvar

    Returns:
        True se sucesso, False caso contrário
    """

    logger.info("Processando e salvando arquivo Excel...")

    try:
        # Limpar caracteres inválidos para Excel
        logger.info("• Limpando caracteres inválidos...")
        df_limpo = limpar_caracteres_invalidos(df.copy())

        arquivo_output = DATA_PROCESSED_DIR / nome_arquivo

        # Salvar em Excel
        df_limpo.to_excel(arquivo_output, index=False, engine='openpyxl')

        tamanho_mb = arquivo_output.stat().st_size / (1024 * 1024)
        logger.info(f"✓ Arquivo Excel salvo: {nome_arquivo} ({tamanho_mb:.2f} MB)")

        return True

    except Exception as e:
        logger.error(f"✗ Erro ao salvar Excel: {e}")
        return False


# ============================================================================
# RELATÓRIO DE EXECUÇÃO
# ============================================================================

def gerar_relatorio_consolidado(stats_hist, stats_res160, tempo_execucao):
    """
    Gera relatório consolidado com estatísticas dos dois arquivos

    Args:
        stats_hist: Estatísticas do arquivo histórico
        stats_res160: Estatísticas do arquivo Resolução 160
        tempo_execucao: Tempo total de execução em segundos
    """

    logger.info("")
    logger.info("=" * 70)
    logger.info("RELATÓRIO CONSOLIDADO - ATUALIZAÇÃO BASE CVM")
    logger.info("=" * 70)
    logger.info(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    logger.info(f"Tempo de execução: {tempo_execucao:.2f} segundos")
    logger.info("-" * 70)

    # Arquivo Histórico
    if stats_hist:
        logger.info("ARQUIVO 1: Ofertas Históricas (ofertas_cvm_historico.xlsx)")
        logger.info(f"  Total: {stats_hist.get('total_novo', 0):,} ofertas")
        if not stats_hist.get('primeira_execucao'):
            logger.info(f"  Novas: {stats_hist.get('ofertas_novas', 0)}")
            logger.info(f"  Removidas: {stats_hist.get('ofertas_removidas', 0)}")
        logger.info(f"  Período: 1988-2025 (todos os tipos)")
    else:
        logger.info("ARQUIVO 1: Ofertas Históricas - FALHA NO DOWNLOAD")

    logger.info("")

    # Arquivo Resolução 160
    if stats_res160:
        logger.info("ARQUIVO 2: Resolução 160 (ofertas_cvm_resolucao_160.xlsx)")
        logger.info(f"  Total: {stats_res160.get('total_novo', 0):,} ofertas")
        if not stats_res160.get('primeira_execucao'):
            logger.info(f"  Novas: {stats_res160.get('ofertas_novas', 0)}")
            logger.info(f"  Removidas: {stats_res160.get('ofertas_removidas', 0)}")
        logger.info(f"  Período: 2023-2025 (rito automático)")
    else:
        logger.info("ARQUIVO 2: Resolução 160 - FALHA NO DOWNLOAD")

    logger.info("-" * 70)
    logger.info(f"Localização: {DATA_PROCESSED_DIR}")
    logger.info("=" * 70)
    logger.info("")


# ============================================================================
# FUNÇÃO PRINCIPAL
# ============================================================================

def executar_atualizacao():
    """
    Executa processo completo de atualização da base CVM
    Processa dois arquivos separadamente:
    1. Ofertas Históricas (1988-2025)
    2. Ofertas Resolução 160 (2023-2025, rito automático)

    Returns:
        True se pelo menos um arquivo foi processado com sucesso
    """

    inicio = datetime.now()

    logger.info("")
    logger.info("╔" + "═" * 68 + "╗")
    logger.info("║" + " ATUALIZAÇÃO BASE CVM - OFERTAS PÚBLICAS ".center(68) + "║")
    logger.info("╚" + "═" * 68 + "╝")
    logger.info("")

    try:
        # 1. Criar estrutura de diretórios
        logger.info("1/4 - Verificando estrutura de diretórios...")
        criar_estrutura_diretorios()

        # =====================================================================
        # 2. DOWNLOAD DO ARQUIVO ZIP (contém ambos os CSVs)
        # =====================================================================
        logger.info("")
        logger.info("=" * 70)
        logger.info("2/4 - BAIXANDO DADOS DA CVM (ZIP com 2 arquivos)")
        logger.info("=" * 70)
        logger.info("")

        df_historico, df_resolucao_160 = download_dados_cvm_completo()

        if df_historico is None and df_resolucao_160 is None:
            logger.error("✗ FALHA: Não foi possível baixar nenhum arquivo")
            return False

        # Variáveis para controle de sucesso
        sucesso_historico = False
        sucesso_resolucao_160 = False
        stats_historico = None
        stats_resolucao_160 = None

        # =====================================================================
        # 3. PROCESSAR ARQUIVO HISTÓRICO
        # =====================================================================
        logger.info("")
        logger.info("=" * 70)
        logger.info("3/4 - PROCESSANDO ARQUIVO HISTÓRICO (1988-2025)")
        logger.info("=" * 70)

        if df_historico is not None:
            try:
                logger.info("")
                logger.info("3.1 - Criando backup do arquivo histórico...")
                fazer_backup_arquivo_anterior(ARQUIVO_PROCESSED_HISTORICO)

                logger.info("")
                logger.info("3.2 - Analisando alterações...")
                stats_historico = comparar_com_versao_anterior(df_historico, ARQUIVO_PROCESSED_HISTORICO)

                logger.info("")
                logger.info("3.3 - Salvando arquivo processado...")
                if processar_e_salvar(df_historico, ARQUIVO_PROCESSED_HISTORICO):
                    logger.info("✓ ARQUIVO HISTÓRICO processado com sucesso")
                    sucesso_historico = True
                else:
                    logger.error("✗ Falha ao salvar arquivo histórico")

            except Exception as e:
                logger.error(f"✗ Erro ao processar arquivo histórico: {e}")
                logger.exception("Detalhes:")
        else:
            logger.warning("⚠ Arquivo histórico não encontrado no ZIP")

        # =====================================================================
        # 4. PROCESSAR ARQUIVO RESOLUÇÃO 160
        # =====================================================================
        logger.info("")
        logger.info("=" * 70)
        logger.info("4/4 - PROCESSANDO ARQUIVO RESOLUÇÃO 160 (2023-2025)")
        logger.info("=" * 70)

        if df_resolucao_160 is not None:
            try:
                logger.info("")
                logger.info("4.1 - Criando backup do arquivo Resolução 160...")
                fazer_backup_arquivo_anterior(ARQUIVO_PROCESSED_RESOLUCAO_160)

                logger.info("")
                logger.info("4.2 - Analisando alterações...")
                stats_resolucao_160 = comparar_com_versao_anterior(df_resolucao_160, ARQUIVO_PROCESSED_RESOLUCAO_160)

                logger.info("")
                logger.info("4.3 - Salvando arquivo processado...")
                if processar_e_salvar(df_resolucao_160, ARQUIVO_PROCESSED_RESOLUCAO_160):
                    logger.info("✓ ARQUIVO RESOLUÇÃO 160 processado com sucesso")
                    sucesso_resolucao_160 = True
                else:
                    logger.error("✗ Falha ao salvar arquivo Resolução 160")

            except Exception as e:
                logger.error(f"✗ Erro ao processar arquivo Resolução 160: {e}")
                logger.exception("Detalhes:")
        else:
            logger.warning("⚠ Arquivo Resolução 160 não encontrado no ZIP")

        # =====================================================================
        # 5. FINALIZAÇÃO
        # =====================================================================
        logger.info("")
        logger.info("=" * 70)
        logger.info("FINALIZANDO")
        logger.info("=" * 70)

        # Limpar backups antigos
        logger.info("")
        logger.info("5.1 - Limpando backups antigos...")
        limpar_backups_antigos(dias_manter=30)

        # Gerar relatório consolidado
        logger.info("")
        logger.info("5.2 - Gerando relatório consolidado...")
        tempo_execucao = (datetime.now() - inicio).total_seconds()
        gerar_relatorio_consolidado(stats_historico, stats_resolucao_160, tempo_execucao)

        # Determinar resultado final
        if sucesso_historico and sucesso_resolucao_160:
            logger.info("✓ EXECUÇÃO CONCLUÍDA COM SUCESSO (2/2 arquivos)")
            logger.info("")
            return True
        elif sucesso_historico or sucesso_resolucao_160:
            logger.warning("⚠ EXECUÇÃO PARCIALMENTE CONCLUÍDA (1/2 arquivos)")
            logger.info("")
            return True
        else:
            logger.error("✗ EXECUÇÃO FALHOU (0/2 arquivos)")
            logger.info("")
            return False

    except KeyboardInterrupt:
        logger.warning("")
        logger.warning("⚠ Execução interrompida pelo usuário")
        return False

    except Exception as e:
        logger.error("")
        logger.error(f"✗ ERRO CRÍTICO: {e}")
        logger.exception("Detalhes do erro:")
        return False


# ============================================================================
# EXECUÇÃO
# ============================================================================

if __name__ == "__main__":
    # Configurar sistema de logs
    logger = configurar_logs()

    # Executar atualização
    sucesso = executar_atualizacao()

    # Código de saída
    exit(0 if sucesso else 1)
