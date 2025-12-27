#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Processador de Ofertas CVM
==========================
Script para processar dados de ofertas públicas da CVM.
- Lê CSV da Resolução 160
- Faz scraping das páginas individuais para dados detalhados
- Atualiza Excel incrementalmente

Autor: Andrew Lopes / Claude Code
Data: Dezembro 2024
"""

import os
import re
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import pandas as pd

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# =============================================================================
# CONFIGURAÇÕES
# =============================================================================

# Caminhos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "oferta_resolucao_160.csv")
OUTPUT_CSV_PATH = os.path.join(BASE_DIR, "DCM_CVM.csv")
ANBIMA_PATH = None  # Será definido pelo usuário

# URL base para scraping
CVM_BASE_URL = "https://web.cvm.gov.br/sre-publico-cvm/#/oferta-publica/"

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(BASE_DIR, 'logs', 'processamento.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# =============================================================================
# MAPEAMENTOS E CONSTANTES
# =============================================================================

# Produtos a processar (mapeamento CSV -> Excel)
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
    'Outros títulos de securitização': 'Outros',
    'Outros tÃ­tulos de securitizaÃ§Ã£o': 'Outros',
}

# Lista de produtos válidos
PRODUTOS_VALIDOS = list(PRODUTOS_MAP.keys())

# Abreviação de coordenadores
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
    'BANCO CITIBANK': 'Citi',
    'CITIBANK': 'Citi',
    'CITI': 'Citi',
    'INTER DISTRIBUIDORA': 'Inter',
    'BANCO INTER': 'Inter',
    'ATIVA INVESTIMENTOS': 'Ativa',
    'ATIVA': 'Ativa',
    'TERRA INVESTIMENTOS': 'Terra',
    'TERRA': 'Terra',
    'BANCO BV': 'BV',
    'BANCO VOTORANTIM': 'BV',
    'BV': 'BV',
    'BANCO GENIAL': 'Genial',
    'GENIAL': 'Genial',
    'CAIXA ECONÔMICA': 'Caixa',
    'CAIXA ECONOMICA': 'Caixa',
    'CAIXA': 'Caixa',
    'BNDES': 'BNDES',
    'BANCO ABC': 'ABC',
    'ABC BRASIL': 'ABC',
    'BR PARTNERS': 'BR Partners',
    'OPEA': 'OPEA',
    'BANCO DO BRASIL': 'BB',
    'BANCO DAYCOVAL': 'Daycoval',
    'DAYCOVAL': 'Daycoval',
    'BANCO MODAL': 'Modal',
    'MODAL': 'Modal',
    'BANCO RODOBENS': 'Rodobens',
    'BANCO PINE': 'Pine',
    'PINE': 'Pine',
    'GUIDE INVESTIMENTOS': 'Guide',
    'GUIDE': 'Guide',
    'ORAMA': 'Orama',
    'BANCO PAN': 'Pan',
    'PAN': 'Pan',
    'BANCO ORIGINAL': 'Original',
    'BANCO BMG': 'BMG',
    'BMG': 'BMG',
    'PLURAL': 'Plural',
    'GAIA': 'Gaia',
    'TRUE SECURITIZADORA': 'True',
    'TRUE': 'True',
    'VIRGO COMPANHIA': 'Virgo',
    'VIRGO': 'Virgo',
    'ISEC': 'Isec',
    'OCTANTE': 'Octante',
    'RB CAPITAL': 'RB',
    'RB': 'RB',
    'VINCI': 'Vinci',
    'SPX': 'SPX',
    'OPEA SECURITIZADORA': 'Opea',
    'HABITASEC': 'Habitasec',
    'BARIGUI': 'Barigui',
    'FIDUCIAL': 'Fiducial',
    'MASTER': 'Master',
    'FATOR': 'Fator',
    'OURINVEST': 'Ourinvest',
}

# Preposições para Title Case
PREPOSICOES = {'de', 'do', 'da', 'dos', 'das', 'em', 'e', 'para', 'por', 'com', 'sem', 'sob'}

# Siglas a manter
SIGLAS = {'S.A.', 'S/A', 'LTDA', 'LTDA.', 'CIA', 'CIA.', 'CNPJ', 'FIDC', 'FII', 'FIP', 'FIAGRO'}

# Status para Pipeline (em andamento)
STATUS_PIPELINE = ['Registro Concedido', 'Aguardando Bookbuilding', 'Aguardando Encerramento']

# Status para Registrada (encerradas)
STATUS_REGISTRADA = ['Oferta Encerrada']

# Status ignorados
STATUS_IGNORAR = ['Registro Caducado']

# Mapeamento para normalizar status
STATUS_NORMALIZAR = {
    'Encerrado': 'Oferta Encerrada',
    'Concedido': 'Registro Concedido',
}

# Colunas do Excel (ordem)
COLUNAS_EXCEL = [
    'Data Requerimento',
    'Data Registro',
    'Data Book',
    'Status',
    'Chave',
    'Público',
    'Produto',
    'Emissor',
    'Coordenadores',
    'Nº Emissão',
    'Série',
    'Espécie',
    'Rating',
    'Volume Inicial',
    'Volume Final',
    'Data de Emissão',
    'Data de Vencimento',
    'Prazo',
    'Taxa Teto',
    'Taxa Final',
    '12.431',
    '14.801',
    'Venda',
    'Venda R$',
    'Obs',
    'Tipo Oferta',
    'Regime Distribuição',
    'Bookbuilding',
    'IPO',
    'Vasos Comunicantes',
    'Sustentável',
    'Tipo Lastro',
    'Regime Fiduciário',
    'Garantias',
    'Lastro',
    'Destinação Recursos',
    'Agente Fiduciário',
]


# =============================================================================
# FUNÇÕES DE FORMATAÇÃO
# =============================================================================

def normalizar_status(status: str) -> str:
    """Normaliza o status para valores padronizados."""
    if not status or pd.isna(status):
        return ''
    status = str(status).strip()
    return STATUS_NORMALIZAR.get(status, status)


def formatar_nome_titulo(nome: str) -> str:
    """
    Converte nome para Title Case inteligente.
    - Primeira letra de cada palavra maiúscula
    - Preposições em minúsculo
    - Mantém siglas
    """
    if not nome or pd.isna(nome):
        return ""

    nome = str(nome).strip()
    palavras = nome.split()
    resultado = []

    for i, palavra in enumerate(palavras):
        # Verificar se é sigla
        palavra_upper = palavra.upper()
        if palavra_upper in SIGLAS or palavra_upper.replace('.', '') in [s.replace('.', '') for s in SIGLAS]:
            resultado.append(palavra_upper)
        # Primeira palavra sempre com maiúscula
        elif i == 0:
            resultado.append(palavra.capitalize())
        # Preposições em minúsculo
        elif palavra.lower() in PREPOSICOES:
            resultado.append(palavra.lower())
        else:
            resultado.append(palavra.capitalize())

    return ' '.join(resultado)


def simplificar_produto(valor_mobiliario: str) -> Optional[str]:
    """
    Simplifica o nome do produto (valor mobiliário).
    Retorna None se não for um produto válido.
    """
    if not valor_mobiliario or pd.isna(valor_mobiliario):
        return None

    valor_mobiliario = str(valor_mobiliario).strip()

    # Buscar mapeamento direto
    if valor_mobiliario in PRODUTOS_MAP:
        return PRODUTOS_MAP[valor_mobiliario]

    # Buscar por substring
    for chave, valor in PRODUTOS_MAP.items():
        if chave.lower() in valor_mobiliario.lower():
            return valor

    return None


def abreviar_coordenador(nome_lider: str) -> str:
    """
    Abrevia o nome do coordenador líder.
    """
    if not nome_lider or pd.isna(nome_lider):
        return ""

    nome_lider_original = str(nome_lider).strip()
    nome_lider = nome_lider_original.upper()

    # Ordenar chaves por tamanho (maior primeiro) para evitar matches parciais
    chaves_ordenadas = sorted(COORDENADORES_MAP.keys(), key=len, reverse=True)

    # Buscar abreviação
    for chave in chaves_ordenadas:
        if chave in nome_lider:
            return COORDENADORES_MAP[chave]

    # Se não encontrar na tabela, aplicar lógica de fallback
    # Remover termos genéricos
    termos_remover = ['BANCO', 'S.A.', 'S/A', 'LTDA', 'CORRETORA', 'DISTRIBUIDORA',
                       'DTVM', 'CTVM', 'CCTVM', 'INVESTIMENTOS', 'ASSESSORIA', 'FINANCEIRA']

    nome_limpo = nome_lider
    for termo in termos_remover:
        nome_limpo = nome_limpo.replace(termo, '').strip()

    # Pegar primeira palavra significativa
    partes = [p for p in nome_limpo.split() if len(p) > 2]
    if partes:
        return partes[0].title()

    # Último recurso: retornar nome original em title case limitado
    return nome_lider_original[:20].title() if nome_lider_original else ""


def extrair_emissor(row: pd.Series, produto: str) -> str:
    """
    Extrai o emissor correto baseado no tipo de produto.
    - Debêntures/NC/NP: Nome_Emissor
    - CRA/CRI/CR/CPR-F: Identificacao_devedores_coobrigados
    """
    if produto in ['Debêntures', 'NC', 'NP']:
        emissor = row.get('Nome_Emissor', '')
    else:  # CRA, CRI, CR, CPR-F
        emissor = row.get('Identificacao_devedores_coobrigados', '')

        # Verificar se é pulverizado
        if emissor and not pd.isna(emissor):
            emissor_lower = str(emissor).lower()
            termos_pulverizado = ['pessoa física', 'pessoas físicas', 'diversos', 'pulverizado',
                                  'pessoa jurídica', 'pessoas jurídicas', 'n/a', 'não aplicável']
            if any(termo in emissor_lower for termo in termos_pulverizado):
                return 'Pulverizado'

            # Limpar o texto - extrair apenas o nome principal da empresa
            emissor = _limpar_nome_emissor(str(emissor))

        # Se vazio, tentar Nome_Emissor
        if not emissor or pd.isna(emissor) or str(emissor).strip() == '':
            emissor = row.get('Nome_Emissor', '')

    if not emissor or pd.isna(emissor):
        return 'N/A'

    return formatar_nome_titulo(str(emissor))


def _limpar_nome_emissor(texto: str) -> str:
    """
    Limpa o texto do emissor, extraindo apenas o nome principal.
    Remove CNPJ, descrições longas, avalistas, etc.
    """
    if not texto:
        return texto

    import re

    # Remover prefixos comuns
    prefixos_remover = ['Devedora:', 'Devedoras:', 'Devedor:', 'Cedente:', 'Cedentes:']
    for prefixo in prefixos_remover:
        if texto.startswith(prefixo):
            texto = texto[len(prefixo):].strip()
        texto = texto.replace(prefixo, '').strip()

    # Padrões para cortar o texto
    padroes_corte = [
        r'\s*,?\s*inscrit[ao]',  # "inscrita no CNPJ"
        r'\s*,?\s*CNPJ',  # CNPJ diretamente
        r'\s*\|\s*Avalistas?:',  # Avalistas
        r'\s*,?\s*com\s+aval',  # com aval
        r'\s*,?\s*Os\s+Direitos',  # descrição de direitos
        r'\s*,?\s*100%',  # percentuais
        r'\s*:\s*\d+\.\d+\.\d+',  # padrão de CNPJ
    ]

    resultado = texto.strip()

    for padrao in padroes_corte:
        match = re.search(padrao, resultado, re.IGNORECASE)
        if match:
            resultado = resultado[:match.start()].strip()

    # Remover vírgulas ou pontos no final
    resultado = re.sub(r'[,.\s]+$', '', resultado)

    # Se ficou muito curto, usar original (limitado)
    if len(resultado) < 3:
        resultado = texto[:100]

    # Limitar tamanho máximo
    if len(resultado) > 100:
        # Tentar cortar em um separador natural
        for sep in [' | ', ', ', ' - ']:
            if sep in resultado[:100]:
                resultado = resultado[:resultado.find(sep, 50) if resultado.find(sep, 50) > 0 else 100]
                break
        else:
            resultado = resultado[:100]

    return resultado.strip()


def formatar_data(data) -> str:
    """Formata data para DD/MM/AAAA."""
    if pd.isna(data):
        return ''
    if isinstance(data, str):
        try:
            # Usar dayfirst=True para datas no formato DD/MM/YYYY
            data = pd.to_datetime(data, dayfirst=True)
        except:
            return data
    return data.strftime('%d/%m/%Y')


def formatar_volume(valor) -> str:
    """Formata volume sem decimais, com ponto como separador de milhar."""
    if pd.isna(valor) or valor == '' or valor == 0:
        return ''
    try:
        # Limpar o valor - remover R$, espaços, e normalizar separadores
        valor_str = str(valor).strip()
        valor_str = valor_str.replace('R$', '').strip()

        # Se tem vírgula como decimal e ponto como milhar (formato BR)
        # Ex: 1.234.567,89 -> 1234567.89
        if ',' in valor_str and '.' in valor_str:
            valor_str = valor_str.replace('.', '').replace(',', '.')
        # Se só tem vírgula, é decimal
        elif ',' in valor_str:
            valor_str = valor_str.replace(',', '.')

        valor_float = float(valor_str)
        return f"{int(valor_float):,}".replace(',', '.')
    except:
        return str(valor)


def calcular_prazo(data_emissao, data_vencimento) -> str:
    """Calcula prazo em anos com 2 decimais."""
    if pd.isna(data_emissao) or pd.isna(data_vencimento):
        return ''
    try:
        if isinstance(data_emissao, str):
            data_emissao = pd.to_datetime(data_emissao)
        if isinstance(data_vencimento, str):
            data_vencimento = pd.to_datetime(data_vencimento)

        dias = (data_vencimento - data_emissao).days
        anos = dias / 365
        return f"{anos:.2f}"
    except:
        return ''


# =============================================================================
# FUNÇÕES ANBIMA
# =============================================================================

def extrair_chave_anbima(codigo: str) -> Optional[int]:
    """
    Extrai a chave CVM do código ANBIMA.
    Formatos:
    - SRE/2025/23267 -> 23267
    - RJ-2016-07894 -> 7894
    - SP-2017-50128 -> 50128
    """
    if not codigo or pd.isna(codigo):
        return None

    codigo = str(codigo)

    # Formato SRE/YYYY/XXXXX
    match = re.search(r'SRE/\d{4}/(\d+)', codigo)
    if match:
        return int(match.group(1))

    # Formato XX-YYYY-XXXXX
    match = re.search(r'-(\d+)$', codigo)
    if match:
        return int(match.group(1))

    return None


def formatar_taxa_anbima(row) -> str:
    """
    Formata taxa a partir dos campos Indexador e Spread da ANBIMA.
    Retorna formato: "CDI + 1,35%" ou "IPCA + 5,50%" ou "Pré 12,50%"
    """
    indexador = row.get('Indexador', '')
    spread = row.get('Spread')

    if pd.isna(indexador) or indexador == 'Não identificado':
        return ''

    # Mapear indexador ANBIMA para nosso padrão
    if 'DI' in str(indexador):
        idx = 'CDI'
    elif 'IPCA' in str(indexador):
        idx = 'IPCA'
    elif 'Pré' in str(indexador) or 'Prefixado' in str(indexador):
        idx = 'Pré'
    else:
        return ''  # Indexador não mapeado

    # Formatar spread
    if pd.notna(spread) and spread != 0:
        spread_fmt = f"{float(spread):.2f}".replace('.', ',')
        if idx == 'Pré':
            return f"Pré {spread_fmt}%"
        else:
            return f"{idx} + {spread_fmt}%"

    return idx


def carregar_anbima(caminho: str) -> Dict[int, Dict]:
    """
    Carrega base ANBIMA e retorna dicionário indexado por chave CVM.

    Args:
        caminho: Caminho do arquivo .xls da ANBIMA

    Returns:
        Dict com chave CVM -> dados da oferta
    """
    if not caminho or not os.path.exists(caminho):
        logger.warning(f"Arquivo ANBIMA não encontrado: {caminho}")
        return {}

    try:
        logger.info(f"Carregando base ANBIMA: {caminho}")
        df = pd.read_excel(caminho)

        anbima_dict = {}
        for _, row in df.iterrows():
            chave = extrair_chave_anbima(row.get('Código da oferta'))
            if chave and chave not in anbima_dict:
                anbima_dict[chave] = {
                    'taxa_final': formatar_taxa_anbima(row),
                    'volume_final': row.get('Valor total encerrado da série'),
                    'indexador': row.get('Indexador'),
                    'spread': row.get('Spread'),
                    'emissor_anbima': row.get('Emissor'),
                    'devedor_anbima': row.get('Nome do devedor'),
                }

        logger.info(f"ANBIMA carregada: {len(anbima_dict)} ofertas únicas")
        return anbima_dict

    except Exception as e:
        logger.error(f"Erro ao carregar ANBIMA: {e}")
        return {}


def complementar_com_anbima(dados_base: Dict, anbima_dict: Dict[int, Dict]) -> Dict:
    """
    Complementa dados da oferta com informações da ANBIMA.
    Apenas para ofertas encerradas que não têm Taxa Final.

    Args:
        dados_base: Dict com dados da oferta
        anbima_dict: Dict com dados da ANBIMA indexado por chave

    Returns:
        Dict atualizado
    """
    chave = dados_base.get('Chave')
    if not chave:
        return dados_base

    chave = int(chave)

    # Verificar se tem dados na ANBIMA
    if chave not in anbima_dict:
        return dados_base

    dados_anbima = anbima_dict[chave]

    # Complementar Taxa Final (se vazio)
    if not dados_base.get('Taxa Final') or dados_base.get('Taxa Final') == '':
        taxa_anbima = dados_anbima.get('taxa_final', '')
        if taxa_anbima:
            dados_base['Taxa Final'] = taxa_anbima
            logger.debug(f"Chave {chave}: Taxa Final da ANBIMA = {taxa_anbima}")

    # Complementar Volume Final (se vazio e oferta encerrada)
    if not dados_base.get('Volume Final') or dados_base.get('Volume Final') == '':
        vol_anbima = dados_anbima.get('volume_final')
        if pd.notna(vol_anbima) and vol_anbima:
            dados_base['Volume Final'] = formatar_volume(vol_anbima)
            logger.debug(f"Chave {chave}: Volume Final da ANBIMA = {vol_anbima}")

    return dados_base


# =============================================================================
# CLASSE CVMScraper
# =============================================================================

class CVMScraper:
    """
    Classe para fazer scraping das páginas de ofertas da CVM.
    """

    # Tempo de espera para carregamento (segundos)
    TEMPO_ESPERA_INICIAL = 20
    TEMPO_ESPERA_RETRY = 15
    MAX_TENTATIVAS = 3

    # Texto OBRIGATÓRIO que indica que a seção de características carregou
    TEXTO_OBRIGATORIO = 'Características do Valor Mobiliário'

    # Textos adicionais para verificação (pelo menos 1 deve estar presente)
    TEXTOS_VERIFICACAO = [
        'Data de emissão',
        'Data de vencimento',
        'Lote Base',
        'remuneração'
    ]

    def __init__(self, headless: bool = True):
        """
        Inicializa o scraper com Chrome.

        Args:
            headless: Se True, roda sem abrir janela do navegador
        """
        self.headless = headless
        self.driver = None
        self._setup_driver()

    def _setup_driver(self):
        """Configura o driver do Chrome."""
        options = Options()
        if self.headless:
            options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.implicitly_wait(10)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """Fecha o navegador."""
        if self.driver:
            self.driver.quit()
            self.driver = None

    def _pagina_carregou(self, texto_pagina: str) -> bool:
        """Verifica se a página carregou os dados corretamente."""
        # Verificar se o texto obrigatório está presente
        if self.TEXTO_OBRIGATORIO.lower() not in texto_pagina.lower():
            return False

        # Verificar se pelo menos um dos textos adicionais está presente
        for texto in self.TEXTOS_VERIFICACAO:
            if texto.lower() in texto_pagina.lower():
                return True
        return False

    def _aguardar_e_verificar(self, tentativa: int = 1) -> str:
        """
        Aguarda carregamento e verifica se dados estão presentes.
        Retorna o texto da página se carregou, string vazia se não.
        """
        tempo_espera = self.TEMPO_ESPERA_INICIAL if tentativa == 1 else self.TEMPO_ESPERA_RETRY

        logger.info(f"Tentativa {tentativa}/{self.MAX_TENTATIVAS} - Aguardando {tempo_espera}s...")
        time.sleep(tempo_espera)

        try:
            body = self.driver.find_element(By.TAG_NAME, "body")
            texto = body.text

            if self._pagina_carregou(texto):
                logger.info("Página carregou corretamente!")
                return texto
            else:
                logger.warning("Dados não carregaram completamente")
                return ""
        except Exception as e:
            logger.error(f"Erro ao verificar página: {e}")
            return ""

    def scrape_oferta(self, numero_requerimento: int) -> Dict:
        """
        Faz scraping de uma oferta específica.
        Tenta múltiplas vezes com refresh se necessário.

        Args:
            numero_requerimento: Número do requerimento (Chave)

        Returns:
            Dict com dados extraídos por série
        """
        url = f"{CVM_BASE_URL}{numero_requerimento}"
        logger.info(f"Acessando: {url}")

        texto_pagina = ""

        for tentativa in range(1, self.MAX_TENTATIVAS + 1):
            try:
                if tentativa == 1:
                    self.driver.get(url)
                else:
                    # Dar refresh na página
                    logger.info("Dando refresh na página...")
                    self.driver.refresh()

                # Aguardar e verificar
                texto_pagina = self._aguardar_e_verificar(tentativa)

                if texto_pagina:
                    break

            except TimeoutException:
                logger.warning(f"Timeout na tentativa {tentativa}")
            except Exception as e:
                logger.error(f"Erro na tentativa {tentativa}: {e}")

        if not texto_pagina:
            logger.error(f"Falha ao carregar página após {self.MAX_TENTATIVAS} tentativas")
            return {}

        # Extrair dados
        dados = self._extrair_dados_pagina(texto_pagina)
        return dados

    def _extrair_dados_pagina(self, texto_pagina: str) -> Dict:
        """
        Extrai todos os dados relevantes do texto da página.

        Args:
            texto_pagina: Texto visível da página
        """
        dados = {
            'series': [],
            'rating': '',
            'lei_14801': '',
        }

        try:
            # Extrair Rating
            dados['rating'] = self._extrair_rating(texto_pagina)

            # Extrair Lei 14.801
            lei_14801 = self._extrair_campo_texto(texto_pagina, 'Lei 14.801')
            if not lei_14801:
                lei_14801 = self._extrair_campo_texto(texto_pagina, '14801')
            if lei_14801:
                dados['lei_14801'] = 'S' if 'sim' in lei_14801.lower() else 'N'

            # Extrair dados da série
            serie_data = {
                'numero': self._extrair_numero_serie(texto_pagina),
                'especie': self._extrair_campo_texto(texto_pagina, 'Espécie'),
                'volume_final': '',
                'data_emissao': self._extrair_data(texto_pagina, 'Data de emissão'),
                'data_vencimento': self._extrair_data(texto_pagina, 'Data de vencimento'),
                'taxa_teto': '',
                'taxa_final': '',
            }

            # Taxa Teto - label: "Informações sobre remuneração" (antes do bookbuilding)
            serie_data['taxa_teto'] = self._extrair_taxa(texto_pagina, 'Informações sobre remuneração')
            if not serie_data['taxa_teto']:
                serie_data['taxa_teto'] = self._extrair_taxa(texto_pagina, 'remuneração máxima')

            # Taxa Final - label: "Informações sobre remuneração final (pós bookbuilding)"
            serie_data['taxa_final'] = self._extrair_taxa(texto_pagina, 'remuneração final (pós bookbuilding)')
            if not serie_data['taxa_final']:
                serie_data['taxa_final'] = self._extrair_taxa(texto_pagina, 'pós bookbuilding')
            if not serie_data['taxa_final']:
                serie_data['taxa_final'] = self._extrair_taxa(texto_pagina, 'remuneração final')

            # Volume Final - tentar várias alternativas
            serie_data['volume_final'] = self._extrair_valor(texto_pagina, 'Valor Pós Coleta de Intenções')
            if not serie_data['volume_final']:
                serie_data['volume_final'] = self._extrair_valor(texto_pagina, 'Lote Base')
            if not serie_data['volume_final']:
                serie_data['volume_final'] = self._extrair_valor(texto_pagina, 'Valor Total')

            dados['series'] = [serie_data]

            # Log dos dados extraídos
            logger.info(f"Dados extraídos - Série: {serie_data['numero']}, "
                       f"Emissão: {serie_data['data_emissao']}, "
                       f"Vencimento: {serie_data['data_vencimento']}")

        except Exception as e:
            logger.error(f"Erro ao extrair dados da página: {e}")

        return dados

    def _extrair_campo_texto(self, texto: str, label: str) -> str:
        """Extrai valor após um label no texto."""
        try:
            # Buscar o label no texto (case insensitive)
            texto_lower = texto.lower()
            label_lower = label.lower()

            idx = texto_lower.find(label_lower)
            if idx == -1:
                return ''

            # Pegar texto após o label
            resto = texto[idx + len(label):].strip()

            # Pegar até a próxima quebra de linha ou limite
            linhas = resto.split('\n')
            if linhas:
                valor = linhas[0].strip()
                # Remover caracteres de separação
                valor = valor.lstrip(':').strip()
                return valor[:200]  # Limitar tamanho
            return ''
        except:
            return ''

    def _extrair_numero_serie(self, texto: str) -> str:
        """Extrai número da série."""
        # Buscar padrões como "Série 1", "Série única", etc.
        import re
        match = re.search(r'[Ss]érie\s*:?\s*(\d+|[Úú]nica|[Ss]ênior|[Mm]ezanino|[Ss]ubordinada)', texto)
        if match:
            return match.group(1)
        return '1'  # Padrão

    def _extrair_valor(self, texto: str, label: str) -> str:
        """Extrai valor monetário após um label."""
        valor = self._extrair_campo_texto(texto, label)
        if valor:
            # Tentar extrair apenas números
            import re
            # Padrão: R$ 1.234.567,89 ou 1.234.567,89 ou 1234567.89
            match = re.search(r'R?\$?\s*([\d.,]+)', valor)
            if match:
                return match.group(1).strip()
        return valor

    def _extrair_data(self, texto: str, label: str) -> str:
        """Extrai data após um label."""
        valor = self._extrair_campo_texto(texto, label)
        if valor:
            # Buscar padrão de data DD/MM/YYYY ou YYYY-MM-DD
            import re
            match = re.search(r'(\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2})', valor)
            if match:
                return match.group(1)
        return valor

    def _extrair_taxa(self, texto: str, label: str) -> str:
        """
        Extrai informação de taxa/remuneração.
        Identifica base 252 (CDI) ou base 360 (VC) e extrai o percentual.
        """
        import re

        # Buscar o label no texto
        texto_lower = texto.lower()
        label_lower = label.lower()

        idx = texto_lower.find(label_lower)
        if idx == -1:
            return ''

        # Pegar trecho grande para encontrar padrões de taxa
        trecho = texto[idx:idx + 800]
        trecho_lower = trecho.lower()

        # Buscar percentual no trecho (X,XX% ou X.XX% ou X,XXXX%)
        percentuais = re.findall(r'(\d+[,\.]\d+)\s*%', trecho)
        if not percentuais:
            percentuais = re.findall(r'(\d+)\s*%', trecho)

        if percentuais:
            # Pegar o primeiro percentual encontrado
            pct = percentuais[0].replace('.', ',')

            # Base 360 = VC (único caso)
            if re.search(r'(b360|e360|base\s*360|360\s*dias)', trecho_lower):
                return f"VC + {pct}%"

            # Base 252 = identificar o indexador mencionado
            # IPCA
            if 'ipca' in trecho_lower:
                return f"IPCA + {pct}%"

            # NTN-B
            if 'ntn' in trecho_lower or 'ntnb' in trecho_lower:
                return f"NTN-B + {pct}%"

            # Prefixado
            if 'prefixad' in trecho_lower or 'pré' in trecho_lower or re.search(r'\bpre\b', trecho_lower):
                return f"Pré {pct}%"

            # CDI (padrão para base 252 ou quando menciona CDI/DI)
            if 'cdi' in trecho_lower or 'di' in trecho_lower or re.search(r'(b252|e252|base\s*252|252)', trecho_lower):
                return f"CDI + {pct}%"

        # Se não encontrou padrão, usar extração normal
        valor = self._extrair_campo_texto(texto, label)
        if valor:
            valor = valor[:300]
            valor = self._formatar_taxa(valor)
        return valor

    def _formatar_taxa(self, valor: str) -> str:
        """
        Formata taxa extraída para padrão: INDEXADOR + X,XX%
        Regras:
        - Remove prefixos como "(pós bookbuilding):"
        - Identifica VC+ por b360/e360/base360
        - Extrai indexador + spread
        """
        import re

        if not valor:
            return ''

        # Remover prefixos comuns
        prefixos_remover = [
            r'\(pós bookbuilding\):?\s*',
            r'pós bookbuilding:?\s*',
            r'Informações sobre remuneração.*?:\s*',
        ]
        for prefixo in prefixos_remover:
            valor = re.sub(prefixo, '', valor, flags=re.IGNORECASE)

        valor = valor.strip()

        # Regra VC+ (Base 360): identificar por b360, e360, base 360, base360
        if re.search(r'(b360|e360|base\s*360)', valor, re.IGNORECASE):
            # Extrair o percentual
            match = re.search(r'(\d+[,\.]\d+)\s*%', valor)
            if match:
                pct = match.group(1).replace('.', ',')
                return f"VC + {pct}%"
            # Se não encontrar com decimal, tentar inteiro
            match = re.search(r'(\d+)\s*%', valor)
            if match:
                return f"VC + {match.group(1)}%"

        # Padrões de indexadores conhecidos
        indexadores = {
            r'CDI\s*[\+\-]\s*([\d,\.]+)\s*%': 'CDI',
            r'([\d,\.]+)\s*%\s*(?:do\s+)?CDI': 'CDI',
            r'IPCA\s*[\+\-]\s*([\d,\.]+)\s*%': 'IPCA',
            r'NTN-?B\s*[\+\-]\s*([\d,\.]+)\s*%': 'NTN-B',
            r'(?:Pré|PRE|Prefixad[ao])\s*([\d,\.]+)\s*%': 'Pré',
            r'DI\s*[\+\-]\s*([\d,\.]+)\s*%': 'DI',
            r'SELIC\s*[\+\-]\s*([\d,\.]+)\s*%': 'SELIC',
            r'B30\s*[\+\-]\s*([\d,\.]+)\s*%': 'B30',
        }

        for padrao, indexador in indexadores.items():
            match = re.search(padrao, valor, re.IGNORECASE)
            if match:
                spread = match.group(1).replace('.', ',')
                if indexador == 'Pré':
                    return f"Pré {spread}%"
                else:
                    # Verificar se é + ou -
                    sinal = '+' if '+' in valor or '-' not in valor else '-'
                    return f"{indexador} {sinal} {spread}%"

        # Se não encontrou padrão conhecido, retornar valor limpo (limitado)
        return valor[:80] if len(valor) > 80 else valor

    def _extrair_rating(self, texto: str) -> str:
        """Extrai o rating (nota de risco) da página."""
        import re

        # Buscar seção de avaliação de risco
        texto_lower = texto.lower()
        idx_avaliacao = texto_lower.find('avaliação de risco')
        if idx_avaliacao == -1:
            idx_avaliacao = texto_lower.find('rating')

        if idx_avaliacao == -1:
            return 'TBD'  # Seção de rating não encontrada

        # Pegar trecho após "avaliação de risco"
        trecho = texto[idx_avaliacao:idx_avaliacao + 800]

        # Verificar se é N/A primeiro - retornar TBD pois usuário preencherá depois
        if 'n/a' in trecho[:100].lower() or 'não aplicável' in trecho[:100].lower():
            return 'TBD'

        # Padrões de rating específicos (ordem de prioridade)
        padroes_rating = [
            # Com sufixo de país/escala em parênteses: AAA(bra), AA+(sf), BB-(bra)
            r'([A-D]{1,3}[+-]?\s*\([a-zA-Z]{2,4}\))',
            # Prefixo br: brAAA, brAA+, brBB-
            r'(br[A-D]{1,3}[+-]?)',
            # Escala Moody's: Aaa, Aa1, Aa2, Baa1, Ba2, etc.
            r'([A-C]a{1,2}[1-3]?)',
            r'([B]a[a]?[1-3]?)',
            # Escala S&P/Fitch padrão: AAA, AA+, AA, AA-, A+, BBB+, etc.
            # Precisa ter pelo menos 2 caracteres e terminar com +/-/número
            r'\b([A-D]{2,3}[+-])\b',
            r'\b([A-D]{3})\b',
        ]

        for padrao in padroes_rating:
            matches = re.findall(padrao, trecho)
            for match in matches:
                # Validar que parece um rating real
                match_upper = match.upper().replace(' ', '')
                # Ignorar palavras comuns
                if match_upper in ['S.A.', 'S/A', 'LTDA', 'CIA', 'LTD', 'AAB', 'ABA', 'BAA', 'ABC', 'CAD']:
                    continue
                # Deve começar com A, B, C ou D e ter formato de rating
                if re.match(r'^(br)?[A-Da-d]{2,3}', match, re.IGNORECASE):
                    return match
                if re.match(r'^[A-D]{1,3}[+-]?\s*\([a-zA-Z]+\)$', match, re.IGNORECASE):
                    return match

        # Se tem seção de rating mas não encontrou valor específico, marcar como TBD
        return 'TBD'

    def _extrair_campo(self, texto: str, labels: List[str]) -> str:
        """Extrai valor de um campo baseado nos labels."""
        for label in labels:
            # Buscar padrão: label seguido de valor
            pattern = rf'{re.escape(label)}\s*:?\s*([^\n<]+)'
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                valor = match.group(1).strip()
                # Limpar HTML tags
                valor = re.sub(r'<[^>]+>', '', valor)
                return valor.strip()
        return ''

    def _extrair_series(self) -> List[Dict]:
        """Extrai dados de cada série."""
        series = []

        try:
            # Tentar encontrar elementos de série
            # Nota: Os seletores CSS precisam ser ajustados conforme a estrutura real da página
            serie_elements = self.driver.find_elements(By.CSS_SELECTOR, "[class*='serie'], [class*='Serie']")

            if not serie_elements:
                # Tentar outro seletor
                serie_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Série')]")

            for elem in serie_elements:
                try:
                    serie_data = {
                        'numero': '',
                        'especie': '',
                        'volume_final': '',
                        'data_emissao': '',
                        'data_vencimento': '',
                        'taxa_teto': '',
                        'taxa_final': '',
                    }

                    # Extrair número da série
                    texto = elem.text
                    match = re.search(r'[Ss]érie\s*:?\s*(\d+|[Úú]nica|[Ss]ênior|[Mm]ezanino)', texto)
                    if match:
                        serie_data['numero'] = match.group(1)

                    series.append(serie_data)
                except Exception as e:
                    logger.debug(f"Erro ao extrair série: {e}")
                    continue

        except Exception as e:
            logger.debug(f"Não foi possível extrair séries: {e}")

        return series


# =============================================================================
# FUNÇÕES DE PROCESSAMENTO
# =============================================================================

def carregar_csv() -> pd.DataFrame:
    """Carrega e processa o CSV da CVM."""
    logger.info(f"Carregando CSV: {CSV_PATH}")

    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"Arquivo CSV não encontrado: {CSV_PATH}")

    df = pd.read_csv(CSV_PATH, sep=';', encoding='latin-1', low_memory=False)

    # Limpar nomes das colunas (remover BOM)
    df.columns = [c.replace('ï»¿', '').replace('\ufeff', '') for c in df.columns]

    logger.info(f"CSV carregado: {len(df)} registros")

    return df


def filtrar_produtos(df: pd.DataFrame) -> pd.DataFrame:
    """Filtra apenas os produtos de interesse."""
    # Criar coluna de produto simplificado
    df['Produto_Simplificado'] = df['Valor_Mobiliario'].apply(simplificar_produto)

    # Filtrar apenas produtos válidos
    df_filtrado = df[df['Produto_Simplificado'].notna()].copy()

    logger.info(f"Após filtro de produtos: {len(df_filtrado)} registros")

    return df_filtrado


def carregar_base_existente() -> pd.DataFrame:
    """
    Carrega o CSV existente com todos os dados.
    Retorna DataFrame único com coluna Status diferenciando Pipeline/Registrada.
    """
    if not os.path.exists(OUTPUT_CSV_PATH):
        logger.info("CSV não existe, será criado novo")
        return pd.DataFrame(columns=COLUNAS_EXCEL)

    try:
        df = pd.read_csv(OUTPUT_CSV_PATH, sep=';', encoding='utf-8-sig')
        logger.info(f"CSV carregado: {len(df)} registros")
        return df
    except Exception as e:
        logger.warning(f"Erro ao carregar CSV: {e}")
        return pd.DataFrame(columns=COLUNAS_EXCEL)


def identificar_mudancas(df_csv: pd.DataFrame, df_existente: pd.DataFrame) -> Dict:
    """
    Identifica ofertas novas, atualizadas e encerradas.
    """
    # Chaves existentes
    chaves_existentes = set(df_existente['Chave'].dropna().astype(int)) if 'Chave' in df_existente.columns and len(df_existente) > 0 else set()

    # Chaves em Pipeline (não encerradas)
    chaves_pipeline = set()
    if len(df_existente) > 0 and 'Status' in df_existente.columns:
        df_pipeline = df_existente[df_existente['Status'].isin(STATUS_PIPELINE)]
        chaves_pipeline = set(df_pipeline['Chave'].dropna().astype(int)) if len(df_pipeline) > 0 else set()

    # Chaves do CSV
    chaves_csv = set(df_csv['Numero_Requerimento'].dropna().astype(int))

    # Novas
    novas = chaves_csv - chaves_existentes

    # Verificar mudanças de status nas existentes
    atualizadas = []
    encerradas = []

    for _, row in df_csv.iterrows():
        chave = int(row['Numero_Requerimento'])
        status_csv = row['Status_Requerimento']

        if chave in chaves_pipeline:
            # Verificar se mudou para Encerrada
            if status_csv == 'Oferta Encerrada':
                encerradas.append(chave)
            # Verificar outras mudanças de status
            else:
                status_base = df_existente[df_existente['Chave'] == chave]['Status'].values
                if len(status_base) > 0 and status_base[0] != status_csv:
                    atualizadas.append(chave)

    resultado = {
        'novas': list(novas),
        'atualizadas': atualizadas,
        'encerradas': encerradas,
    }

    logger.info(f"Mudanças identificadas: {len(resultado['novas'])} novas, "
                f"{len(resultado['atualizadas'])} atualizadas, {len(resultado['encerradas'])} encerradas")

    return resultado


def processar_linha_csv(row: pd.Series, produto: str) -> Dict:
    """
    Processa uma linha do CSV e retorna dict com dados formatados.
    """
    return {
        'Data Requerimento': formatar_data(row.get('Data_requerimento')),
        'Data Registro': formatar_data(row.get('Data_Registro')),
        'Data Book': '',  # Preenchimento manual
        'Status': normalizar_status(row.get('Status_Requerimento', '')),
        'Chave': int(row.get('Numero_Requerimento', 0)),
        'Público': row.get('Publico_alvo', ''),
        'Produto': produto,
        'Emissor': extrair_emissor(row, produto),
        'Coordenadores': abreviar_coordenador(row.get('Nome_Lider', '')),
        'Nº Emissão': row.get('Emissao', ''),
        'Série': '',  # Scraping
        'Espécie': '',  # Scraping
        'Rating': '',  # Scraping
        'Volume Inicial': formatar_volume(row.get('Valor_Total_Registrado')),
        'Volume Final': '',  # Scraping
        'Data de Emissão': '',  # Scraping
        'Data de Vencimento': '',  # Scraping
        'Prazo': '',  # Calculado
        'Taxa Teto': '',  # Scraping
        'Taxa Final': '',  # Scraping
        '12.431': 'S' if row.get('Titulo_incentivado') == 'S' else 'N',
        '14.801': '',  # Scraping
        'Venda': '',  # Manual
        'Venda R$': '',  # Manual
        'Obs': '',
        'Tipo Oferta': row.get('Tipo_Oferta', ''),
        'Regime Distribuição': row.get('Regime_distribuicao', ''),
        'Bookbuilding': row.get('Bookbuilding', ''),
        'IPO': 'S' if row.get('Oferta_inicial') == 'S' else 'N',
        'Vasos Comunicantes': 'S' if row.get('Oferta_vasos_comunicantes') == 'S' else 'N',
        'Sustentável': 'S' if row.get('Titulo_classificado_como_sustentavel') == 'S' else 'N',
        'Tipo Lastro': row.get('Tipo_lastro', ''),
        'Regime Fiduciário': 'S' if row.get('Regime_fiduciario') == 'S' else 'N',
        'Garantias': str(row.get('Descricao_garantias', ''))[:500] if row.get('Descricao_garantias') else '',
        'Lastro': str(row.get('Descricao_lastro', ''))[:500] if row.get('Descricao_lastro') else '',
        'Destinação Recursos': str(row.get('Destinacao_recursos', ''))[:500] if row.get('Destinacao_recursos') else '',
        'Agente Fiduciário': row.get('Agente_fiduciario', ''),
    }


def atualizar_com_scraping(dados_base: Dict, dados_scraping: Dict, preservar_anbima: bool = False) -> List[Dict]:
    """
    Atualiza dados base com dados do scraping.
    Retorna lista de dicts (1 por série).

    Args:
        dados_base: Dict com dados base (pode já ter dados ANBIMA)
        dados_scraping: Dict com dados do scraping
        preservar_anbima: Se True, não sobrescreve Taxa Final e Volume Final da ANBIMA
    """
    linhas = []

    # Verificar se é oferta sem bookbuilding (N = Não tem bookbuilding)
    sem_bookbuilding = dados_base.get('Bookbuilding', '') in ['N', 'Sem bookbuilding', 'Não']

    # Guardar dados ANBIMA para preservar
    taxa_anbima = dados_base.get('Taxa Final', '') if preservar_anbima else ''
    volume_anbima = dados_base.get('Volume Final', '') if preservar_anbima else ''

    series = dados_scraping.get('series', [])
    if not series:
        # Sem dados de série, retornar linha única
        rating = dados_scraping.get('rating', '')
        dados_base['Rating'] = rating if rating else 'TBD'
        dados_base['14.801'] = dados_scraping.get('lei_14801', '')

        # Taxa Final: ANBIMA tem prioridade
        if not taxa_anbima:
            # Sem ANBIMA, usar regra de bookbuilding
            if sem_bookbuilding:
                dados_base['Volume Final'] = dados_base.get('Volume Inicial', '')

        linhas.append(dados_base)
    else:
        # Uma linha por série
        for serie in series:
            linha = dados_base.copy()
            linha['Série'] = serie.get('numero', '')
            linha['Espécie'] = serie.get('especie', '')
            rating = dados_scraping.get('rating', '')
            linha['Rating'] = rating if rating else 'TBD'

            # Volume Final: ANBIMA tem prioridade, depois regra bookbuilding
            if volume_anbima:
                linha['Volume Final'] = volume_anbima
            elif sem_bookbuilding:
                linha['Volume Final'] = dados_base.get('Volume Inicial', '')
            else:
                vol_scraping = formatar_volume(serie.get('volume_final', ''))
                if vol_scraping:
                    linha['Volume Final'] = vol_scraping

            # Datas do scraping (ANBIMA não tem)
            linha['Data de Emissão'] = formatar_data(serie.get('data_emissao', ''))
            linha['Data de Vencimento'] = formatar_data(serie.get('data_vencimento', ''))

            # Taxa Teto: sempre do scraping
            linha['Taxa Teto'] = serie.get('taxa_teto', '')

            # Taxa Final: ANBIMA tem prioridade
            if taxa_anbima:
                linha['Taxa Final'] = taxa_anbima
            else:
                linha['Taxa Final'] = serie.get('taxa_final', '')

            linha['14.801'] = dados_scraping.get('lei_14801', '')

            # Calcular prazo
            if linha['Data de Emissão'] and linha['Data de Vencimento']:
                try:
                    linha['Prazo'] = calcular_prazo(
                        pd.to_datetime(linha['Data de Emissão'], format='%d/%m/%Y'),
                        pd.to_datetime(linha['Data de Vencimento'], format='%d/%m/%Y')
                    )
                except:
                    pass

            linhas.append(linha)

    return linhas


def salvar_csv(df: pd.DataFrame):
    """Salva o DataFrame em CSV único."""
    logger.info(f"Salvando CSV: {OUTPUT_CSV_PATH}")

    # Salvar com UTF-8 BOM para compatibilidade com Excel
    df.to_csv(OUTPUT_CSV_PATH, sep=';', encoding='utf-8-sig', index=False)

    # Contar por status
    total_pipeline = len(df[df['Status'].isin(STATUS_PIPELINE)]) if 'Status' in df.columns else 0
    total_registrada = len(df[df['Status'].isin(STATUS_REGISTRADA)]) if 'Status' in df.columns else 0

    logger.info(f"CSV salvo: {len(df)} registros ({total_pipeline} Pipeline, {total_registrada} Registrada)")


# =============================================================================
# FUNÇÃO PRINCIPAL
# =============================================================================

def processar_ofertas(fazer_scraping: bool = True, limite_scraping: int = None, anbima_path: str = None):
    """
    Função principal para processar ofertas.

    Args:
        fazer_scraping: Se True, faz scraping das páginas
        limite_scraping: Limite de ofertas para fazer scraping (para testes)
        anbima_path: Caminho do arquivo ANBIMA (.xls) para complementar dados
    """
    # Carregar ANBIMA se fornecido
    anbima_dict = {}
    if anbima_path:
        anbima_dict = carregar_anbima(anbima_path)
    logger.info("=" * 60)
    logger.info("Iniciando processamento de ofertas CVM")
    logger.info("=" * 60)

    # 1. Carregar CSV da CVM
    df_csv = carregar_csv()

    # 2. Filtrar produtos
    df_csv = filtrar_produtos(df_csv)

    # 3. Carregar base existente (CSV único)
    df_existente = carregar_base_existente()

    # 4. Identificar mudanças
    mudancas = identificar_mudancas(df_csv, df_existente)

    # 5. Processar novas ofertas
    novas_linhas = []
    chaves_para_scraping = mudancas['novas'] + mudancas['atualizadas'] + mudancas['encerradas']

    if limite_scraping:
        chaves_para_scraping = chaves_para_scraping[:limite_scraping]

    # Preparar scraper
    scraper = None
    if fazer_scraping and chaves_para_scraping:
        logger.info(f"Iniciando scraping de {len(chaves_para_scraping)} ofertas...")
        scraper = CVMScraper(headless=True)

    try:
        for chave in chaves_para_scraping:
            # Buscar dados do CSV
            row = df_csv[df_csv['Numero_Requerimento'] == chave].iloc[0]
            produto = row['Produto_Simplificado']

            # Processar dados do CSV
            dados_base = processar_linha_csv(row, produto)

            # 1. Primeiro: buscar dados na ANBIMA (para ofertas encerradas)
            tem_anbima = False
            if anbima_dict and chave in anbima_dict:
                dados_base = complementar_com_anbima(dados_base, anbima_dict)
                tem_anbima = True
                logger.info(f"  → Dados ANBIMA: Taxa={dados_base.get('Taxa Final', '')}")

            # 2. Depois: scraping apenas para dados faltantes (Rating, etc.)
            if scraper:
                # Se já tem ANBIMA, scraping é só para Rating e dados extras
                dados_scraping = scraper.scrape_oferta(chave)
                linhas = atualizar_com_scraping(dados_base, dados_scraping, preservar_anbima=tem_anbima)
            else:
                linhas = [dados_base]

            novas_linhas.extend(linhas)

            # Log de progresso
            logger.info(f"Processado: {chave} ({len(linhas)} linha(s))")

    finally:
        if scraper:
            scraper.close()

    # 6. Atualizar DataFrame único
    if novas_linhas:
        df_novas = pd.DataFrame(novas_linhas, columns=COLUNAS_EXCEL)

        # Remover ofertas atualizadas/encerradas da base existente
        chaves_remover = set(mudancas['atualizadas'] + mudancas['encerradas'])
        if len(df_existente) > 0:
            df_existente = df_existente[~df_existente['Chave'].isin(chaves_remover)]

        # Concatenar novas com existentes
        df_final = pd.concat([df_existente, df_novas], ignore_index=True)
    else:
        df_final = df_existente

    # 7. Salvar CSV
    salvar_csv(df_final)

    # Contadores para retorno
    total_pipeline = len(df_final[df_final['Status'].isin(STATUS_PIPELINE)]) if 'Status' in df_final.columns and len(df_final) > 0 else 0
    total_registrada = len(df_final[df_final['Status'].isin(STATUS_REGISTRADA)]) if 'Status' in df_final.columns and len(df_final) > 0 else 0

    logger.info("=" * 60)
    logger.info("Processamento concluído!")
    logger.info("=" * 60)

    return {
        'novas': len(mudancas['novas']),
        'atualizadas': len(mudancas['atualizadas']),
        'encerradas': len(mudancas['encerradas']),
        'total_pipeline': total_pipeline,
        'total_registrada': total_registrada,
    }


# =============================================================================
# EXECUÇÃO
# =============================================================================

if __name__ == "__main__":
    # Criar diretório de logs se não existir
    os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True)

    print("\n" + "=" * 60)
    print("PROCESSADOR DE OFERTAS CVM")
    print("=" * 60)

    # Lembrete ANBIMA
    print("\n⚠️  LEMBRETE: Atualize o arquivo ANBIMA antes de continuar!")
    print("   Baixe em: https://www.anbima.com.br/pt_br/informar/ofertas-publicas.htm")
    print("")

    # Solicitar caminho do arquivo ANBIMA
    anbima_path = input("Caminho do arquivo ANBIMA (.xls) [Enter para pular]: ").strip()

    if anbima_path:
        if not os.path.exists(anbima_path):
            print(f"⚠️  Arquivo não encontrado: {anbima_path}")
            anbima_path = None
        else:
            print(f"✓ Arquivo ANBIMA: {anbima_path}")
    else:
        print("⚠️  Sem ANBIMA - usando apenas scraping")
        anbima_path = None

    print("")

    # Processar ofertas
    # Para teste inicial, usar limite_scraping=5
    resultado = processar_ofertas(
        fazer_scraping=True,
        limite_scraping=5,
        anbima_path=anbima_path
    )

    print("\n" + "=" * 60)
    print("RESULTADO DO PROCESSAMENTO")
    print("=" * 60)
    print(f"Novas ofertas: {resultado['novas']}")
    print(f"Atualizadas: {resultado['atualizadas']}")
    print(f"Encerradas: {resultado['encerradas']}")
    print(f"Total Pipeline: {resultado['total_pipeline']}")
    print(f"Total Registrada: {resultado['total_registrada']}")
    print("=" * 60)
