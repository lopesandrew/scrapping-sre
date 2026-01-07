"""
Setup inicial do projeto CVM Automation
Execute este script uma vez para configurar o ambiente
"""

import os
import sys

def criar_estrutura_diretorios():
    """Cria estrutura de diretórios do projeto"""
    diretorios = [
        'data/raw',
        'data/processed',
        'data/backup',
        'logs',
        'scripts'
    ]
    
    print("Criando estrutura de diretórios...")
    for diretorio in diretorios:
        os.makedirs(diretorio, exist_ok=True)
        # Criar arquivo .gitkeep para manter diretórios vazios no git
        gitkeep_path = os.path.join(diretorio, '.gitkeep')
        if not os.path.exists(gitkeep_path):
            open(gitkeep_path, 'a').close()
        print(f"  ✓ {diretorio}/")
    
    print("✓ Estrutura de diretórios criada com sucesso!\n")


def verificar_dependencias():
    """Verifica se as dependências estão instaladas"""
    print("Verificando dependências...")
    
    dependencias = {
        'pandas': 'pandas',
        'requests': 'requests',
        'openpyxl': 'openpyxl'
    }
    
    faltando = []
    
    for nome_import, nome_pacote in dependencias.items():
        try:
            __import__(nome_import)
            print(f"  ✓ {nome_pacote}")
        except ImportError:
            print(f"  ✗ {nome_pacote} - NÃO INSTALADO")
            faltando.append(nome_pacote)
    
    if faltando:
        print(f"\n⚠️  Dependências faltando: {', '.join(faltando)}")
        print("\nPara instalar, execute:")
        print("  pip install -r requirements.txt")
        return False
    else:
        print("\n✓ Todas as dependências estão instaladas!\n")
        return True


def criar_config_exemplo():
    """Cria arquivo de configuração exemplo"""
    config_content = """# Configuração do projeto CVM Automation
# Copie este arquivo para config.ini e ajuste conforme necessário

[PATHS]
data_raw = data/raw
data_processed = data/processed
data_backup = data/backup
logs = logs

[CVM]
url_ofertas = https://dados.cvm.gov.br/dados/OFERTA/DISTRIB/DADOS/oferta_distribuicao.zip
timeout = 60

[PROCESSAMENTO]
# Salvar backup antes de atualizar
criar_backup = True
# Manter últimos N backups
max_backups = 30

[EMAIL]
# Configurações de notificação (opcional)
enviar_notificacao = False
smtp_server = smtp.gmail.com
smtp_port = 587
remetente = seu_email@gmail.com
destinatario = seu_email@bocom.com.br

[AGENDAMENTO]
horario_execucao = 08:00
dias_semana = segunda,terca,quarta,quinta,sexta
"""
    
    config_file = 'config.example.ini'
    
    if not os.path.exists(config_file):
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(config_content)
        print(f"✓ Arquivo de configuração exemplo criado: {config_file}\n")
    else:
        print(f"⚠️  {config_file} já existe (não sobrescrito)\n")


def exibir_proximos_passos():
    """Exibe próximos passos após setup"""
    print("="*70)
    print("SETUP CONCLUÍDO!")
    print("="*70)
    print("\n📋 PRÓXIMOS PASSOS:\n")
    print("1. Testar conexão com a CVM:")
    print("   python scripts/teste_rapido_cvm.py\n")
    print("2. (Opcional) Configurar parâmetros:")
    print("   - Copiar config.example.ini para config.ini")
    print("   - Ajustar paths e configurações\n")
    print("3. Configurar agendamento automático:")
    print("   - Ver docs/AGENDAMENTO_AUTOMATICO.md\n")
    print("4. Integrar com base Excel existente:")
    print("   - Adaptar script cvm_ofertas_automacao.py\n")
    print("="*70)


def main():
    """Função principal do setup"""
    print("\n" + "="*70)
    print("SETUP - Projeto CVM Automation")
    print("="*70 + "\n")
    
    # 1. Criar estrutura de diretórios
    criar_estrutura_diretorios()
    
    # 2. Verificar dependências
    deps_ok = verificar_dependencias()
    
    # 3. Criar arquivo de configuração exemplo
    criar_config_exemplo()
    
    # 4. Exibir próximos passos
    exibir_proximos_passos()
    
    # 5. Status final
    if not deps_ok:
        print("\n⚠️  ATENÇÃO: Instale as dependências antes de continuar!")
        sys.exit(1)
    else:
        print("\n✅ Ambiente configurado com sucesso!")
        sys.exit(0)


if __name__ == "__main__":
    main()
