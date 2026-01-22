import requests
import pandas as pd
import time
import os
import argparse
import sys
from inputimeout import inputimeout, TimeoutOccurred

# --- Configurações Globais ---
# Família Apidae (abelhas) = 4334
# País Brasil = BR
BASE_URL = "https://api.gbif.org/v1/occurrence/search"
TAXON_KEY = 4334
COUNTRY = "BR"
PAGE_SIZE = 300  # Limite máximo seguro por página síncrona
OUTPUT_DIR = "data/raw"
START_YEAR = 2000
END_YEAR = 2023

def setup_directories():
    """Cria o diretório de saída se não existir."""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"[sistema] Diretório '{OUTPUT_DIR}' verificado/criado.")

def fetch_data_by_year(year):
    """Busca dados de um ano específico lidando com paginação da API."""
    offset = 0
    end_of_records = False
    all_records = []
    
    print(f"--- Iniciando extração para o ano {year} ---")

    while not end_of_records:
        params = {
            "familyKey": TAXON_KEY,
            "country": COUNTRY,
            "year": year,
            "limit": PAGE_SIZE,
            "offset": offset,
            "hasCoordinate": "true", # Apenas dados com lat/long
            "hasGeospatialIssue": "false"
        }

        try:
            response = requests.get(BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            results = data.get("results", [])
            all_records.extend(results)
            
            # Controle de paginação
            end_of_records = data.get("endOfRecords")
            count = len(results)
            
            # Se vier vazio, forçamos o fim
            if count == 0:
                end_of_records = True
            
            # Feedback visual simples (um ponto por página pra não poluir o terminal)
            sys.stdout.write(".") 
            sys.stdout.flush()
            
            offset += PAGE_SIZE
            
            # Gentileza com a API (para evitar rate limiting)
            time.sleep(0.3)

        except Exception as e:
            print(f"\n[erro] Falha na requisição: {e}")
            break
    
    print(f"\n[concluido] Ano {year}: {len(all_records)} registros baixados.")
    return all_records

def save_data(records, year, export_excel=False):
    """Salva os dados em Parquet (padrão) e opcionalmente em Excel."""
    if not records:
        print(f"[aviso] Nenhum dado encontrado para {year}.")
        return

    df = pd.DataFrame(records)
    
    # Selecionando colunas úteis para reduzir tamanho do arquivo
    cols_interest = [
        'key', 'scientificName', 'decimalLatitude', 'decimalLongitude',
        'eventDate', 'year', 'month', 'day', 
        'stateProvince', 'municipality', 'basisOfRecord'
    ]
    
    # Garante que só pegamos colunas que realmente vieram na resposta
    existing_cols = [c for c in cols_interest if c in df.columns]
    df = df[existing_cols]
    
    # Garante tipo numérico para o ano
    if 'year' in df.columns:
        df['year'] = pd.to_numeric(df['year'], errors='coerce')
    
    # 1. Salvar Parquet (Sempre)
    parquet_path = f"{OUTPUT_DIR}/gbif_apidae_br_{year}.parquet"
    df.to_parquet(parquet_path, index=False)
    print(f"[arquivo] Parquet salvo: {parquet_path}")

    # 2. Salvar Excel (Opcional)
    if export_excel:
        excel_path = f"{OUTPUT_DIR}/gbif_apidae_br_{year}.xlsx"
        print(f"[processando] Gerando Excel para {year} (pode demorar)...")
        df.to_excel(excel_path, index=False)
        print(f"[arquivo] Excel salvo: {excel_path}")

if __name__ == "__main__":
    # Configuração de argumentos de linha de comando
    parser = argparse.ArgumentParser(description="Script de Ingestão GBIF - Data2Eco")
    parser.add_argument('--years', nargs='+', type=int, help='Lista de anos (ex: 2015 2020)')
    parser.add_argument('--excel', action='store_true', help='Gera arquivo .xlsx além do parquet')
    args = parser.parse_args()
    
    setup_directories()
    
    years_to_process = []
    export_excel = args.excel

    # --- Lógica Híbrida com Timeout ---
    if args.years:
        # 1. Modo Robô: Argumentos passados via comando
        years_to_process = args.years
        print(f"[modo] Argumentos detectados. Processando anos: {years_to_process}")
    
    else:
        # 2. Modo Interativo: Pergunta com timeout
        print("\n" + "="*60)
        print(f" NENHUM ANO INFORMADO. MODO AUTOMÁTICO INICIARÁ EM 10 SEGUNDOS.")
        print(f" Padrão: Processar de {START_YEAR} a {END_YEAR}.")
        print(" Digite os anos desejados (ex: 2015 2018) para interromper.")
        print("="*60 + "\n")

        try:
            # Tenta esperar input por 10 segundos
            resposta = inputimeout(prompt='>> Digite agora ou aguarde: ', timeout=10)
            
            if resposta.strip():
                # Usuário digitou algo
                years_to_process = [int(ano) for ano in resposta.split()]
                print(f"[manual] Você escolheu os anos: {years_to_process}")
            else:
                # Usuário deu Enter vazio
                raise TimeoutOccurred 

        except TimeoutOccurred:
            # Tempo acabou
            print("\n[timeout] Tempo esgotado! Iniciando modo automático completo.")
            years_to_process = range(START_YEAR, END_YEAR + 1)
            
        except ValueError:
             print("\n[erro] Você digitou algo que não é número. Indo para o padrão.")
             years_to_process = range(START_YEAR, END_YEAR + 1)

        # Pergunta sobre Excel (só aparece se não foi timeout total)
        if not export_excel and not args.years:
            try:
                resp_excel = inputimeout(prompt='>> Gerar Excel também? (s/n) [5s]: ', timeout=5)
                if resp_excel.lower() == 's':
                    export_excel = True
            except TimeoutOccurred:
                print("\n[timeout] Sem resposta para Excel. Gerando apenas Parquet.")

    # --- Execução Principal ---
    print(f"\n--- Iniciando processamento de {len(years_to_process)} ano(s) ---\n")
    
    for year in years_to_process:
        records = fetch_data_by_year(year)
        save_data(records, year, export_excel=export_excel)
        
    print("\n--- Processo finalizado com sucesso ---")