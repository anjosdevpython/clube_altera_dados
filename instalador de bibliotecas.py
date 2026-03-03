# instalador_direto_sem_dependencias.py

import subprocess
import sys
import time

# Lista das bibliotecas necessárias
BIBLIOTECAS = [
    'selenium',
    'webdriver-manager',
    'ttkbootstrap',
    'Pillow',
]

def obter_pacotes_instalados():
    """Obtém a lista de pacotes instalados usando o pip list"""
    try:
        # Executa 'pip list' e captura a saída
        resultado = subprocess.check_output(
            [sys.executable, '-m', 'pip', 'list'], 
            text=True, 
            stderr=subprocess.DEVNULL,
            timeout=30
        )
        
        # Extrai os nomes dos pacotes (ignora cabeçalho e linhas vazias)
        pacotes = []
        for linha in resultado.split('\n')[2:]:  # Pula as duas primeiras linhas (cabeçalho)
            if linha.strip():
                nome_pacote = linha.split()[0].strip().lower()
                pacotes.append(nome_pacote)
                
        return set(pacotes)
    
    except subprocess.TimeoutExpired:
        print("⚠️ Timeout ao verificar pacotes instalados.")
        return set()
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Erro ao verificar pacotes instalados: {e}")
        return set()
    except Exception as e:
        print(f"⚠️ Erro inesperado ao verificar pacotes: {e}")
        return set()

def instalar_pacote(nome_pacote, tentativas=2):
    """Instala um pacote específico com retry"""
    for tentativa in range(tentativas):
        try:
            print(f'⏳ Instalando {nome_pacote}... (tentativa {tentativa + 1}/{tentativas})')
            
            # Comando de instalação com timeout
            resultado = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', nome_pacote, '--no-warn-script-location'],
                capture_output=True,
                text=True,
                timeout=300  # 5 minutos de timeout
            )
            
            if resultado.returncode == 0:
                print(f'✅ {nome_pacote} instalado com sucesso!')
                return True
            else:
                print(f'⚠️ Erro na instalação de {nome_pacote}: {resultado.stderr.strip()}')
                if tentativa < tentativas - 1:
                    print(f'🔄 Tentando novamente em 2 segundos...')
                    time.sleep(2)
                    
        except subprocess.TimeoutExpired:
            print(f'⏰ Timeout na instalação de {nome_pacote}')
            if tentativa < tentativas - 1:
                print(f'🔄 Tentando novamente...')
                time.sleep(2)
        except Exception as e:
            print(f'❌ Erro inesperado ao instalar {nome_pacote}: {e}')
            if tentativa < tentativas - 1:
                print(f'🔄 Tentando novamente...')
                time.sleep(2)
    
    return False

def verificar_pip():
    """Verifica se o pip está funcionando corretamente"""
    try:
        resultado = subprocess.run(
            [sys.executable, '-m', 'pip', '--version'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if resultado.returncode == 0:
            print(f'✅ pip está funcionando: {resultado.stdout.strip()}')
            return True
        else:
            print(f'❌ Problema com pip: {resultado.stderr.strip()}')
            return False
            
    except Exception as e:
        print(f'❌ Erro ao verificar pip: {e}')
        return False

def atualizar_pip():
    """Tenta atualizar o pip se necessário"""
    try:
        print('🔄 Verificando se pip precisa ser atualizado...')
        subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'],
            capture_output=True,
            timeout=60
        )
        print('✅ pip atualizado com sucesso!')
        return True
    except Exception as e:
        print(f'⚠️ Não foi possível atualizar pip: {e}')
        return False

def instalar_bibliotecas():
    """Função principal para instalar todas as bibliotecas"""
    print('🚀 Iniciando instalação das dependências...\n')
    
    # Verificar se pip está funcionando
    if not verificar_pip():
        print('❌ pip não está funcionando corretamente. Abortando.')
        return
    
    # Tentar atualizar pip
    atualizar_pip()
    print()
    
    # Obter pacotes já instalados
    print('📋 Verificando pacotes já instalados...')
    instalados = obter_pacotes_instalados()
    print(f'✅ Encontrados {len(instalados)} pacotes instalados\n')
    
    # Contadores para relatório final
    ja_instalados = 0
    instalados_com_sucesso = 0
    falharam = []
    
    # Instalar cada biblioteca
    for bib in BIBLIOTECAS:
        bib_normalizada = bib.strip().lower()
        
        if bib_normalizada in instalados:
            print(f'➡️ {bib} já está instalado')
            ja_instalados += 1
        else:
            if instalar_pacote(bib):
                instalados_com_sucesso += 1
            else:
                print(f'❌ Falha na instalação de {bib}')
                falharam.append(bib)
        
        print()  # Linha em branco para separar
    
    # Relatório final
    print('=' * 50)
    print('📊 RELATÓRIO FINAL:')
    print(f'✅ Já instalados: {ja_instalados}')
    print(f'✅ Instalados com sucesso: {instalados_com_sucesso}')
    print(f'❌ Falharam: {len(falharam)}')
    
    if falharam:
        print(f'\n⚠️ Pacotes que falharam na instalação:')
        for pacote in falharam:
            print(f'   - {pacote}')
        print('\n💡 Você pode tentar instalar manualmente com:')
        print(f'   pip install {" ".join(falharam)}')
    else:
        print('\n🎉 Todas as dependências estão instaladas!')
    
    print('=' * 50)

if __name__ == '__main__':
    try:
        instalar_bibliotecas()
    except KeyboardInterrupt:
        print('\n\n⏹️ Instalação interrompida pelo usuário.')
    except Exception as e:
        print(f'\n\n💥 Erro crítico inesperado: {e}')
        print('Por favor, tente executar novamente ou instale manualmente.')