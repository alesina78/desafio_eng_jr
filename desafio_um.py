import subprocess
import sys

def run_command(command):
    print(f"\n🚀 Executando: {command}")
    result = subprocess.run(command, shell=True)
    if result.returncode != 0:
        print(f"❌ Erro ao executar: {command}")
        sys.exit(result.returncode)

def main():
    # 1. Testes unitários
    run_command("pytest tests/ -v --tb=short")
    
    # 2. Ingestão Bronze
    run_command("python src/ingestion/download_uci_data.py")
    
    # 3. Processamento Silver
    run_command("python src/transformations/process_silver.py")
    
    # 4. Construção Gold
    run_command("python src/gold/build_gold.py")
    
    print("\n✅ Pipeline completo executado com sucesso!")
    
    # ⏸️ Pausa para conferir os logs antes de subir o app
    input("\n⏸️ Pressione [ENTER] para iniciar o Cockpit Executivo (Streamlit)...")
    
    # 5. Iniciar o Streamlit
    print("\n📊 Iniciando o Cockpit Executivo (Streamlit)...")
    run_command("streamlit run app.py")

if __name__ == "__main__":
    main()