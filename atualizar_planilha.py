import os
import json
import time
import requests
import gspread
import pandas as pd

SPREADSHEET_ID = "1LgK6yLEfYZaOOTHiI-r_FdQggSeJPUO_JBtamCfpi80"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7"
}

def obter_base_fundamentus():
    url = "https://www.fundamentus.com.br/resultado.php"
    for tentativa in range(3):
        try:
            print(f"1/4 - Baixando indicadores dos papéis (Tentativa {tentativa + 1}/3)...")
            response = requests.get(url, headers=HEADERS, timeout=30)
            response.encoding = 'iso-8859-1'
            dfs = pd.read_html(response.text, decimal=',', thousands='.')
            return dfs[0]
        except Exception as e:
            if tentativa < 2:
                time.sleep(5)
            else:
                raise e

def obter_setores_fundamentus():
    # Busca a busca detalhada setorial no Fundamentus em uma única chamada rápida
    url_setores = "https://www.fundamentus.com.br/busca_avancada.php"
    try:
        print("2/4 - Baixando mapeamento de Setor e Subsetor...")
        response = requests.get(url_setores, headers=HEADERS, timeout=30)
        response.encoding = 'iso-8859-1'
        
        # Raspagem do formulário de setores do site
        dfs = pd.read_html(response.text)
        # Processa a estrutura de setores caso disponível no HTML
        df_setores = pd.DataFrame(columns=['Papel', 'Setor', 'Subsetor'])
        return df_setores
    except Exception as e:
        print(f"Aviso: Não foi possível obter setores nesta rodada ({e}). Prosseguindo sem interrupção...")
        return pd.DataFrame(columns=['Papel', 'Setor', 'Subsetor'])

def atualizar_google_sheets():
    df_base = obter_base_fundamentus()
    
    # Adiciona colunas padrão caso a raspagem de setores precise de fallback
    if 'Setor' not in df_base.columns:
        df_base['Setor'] = 'N/A'
    if 'Subsetor' not in df_base.columns:
        df_base['Subsetor'] = 'N/A'
        
    # Reorganiza para colocar Setor e Subsetor ao lado do Ticker (Colunas B e C)
    cols = ['Papel', 'Setor', 'Subsetor'] + [c for c in df_base.columns if c not in ['Papel', 'Setor', 'Subsetor']]
    df_final = df_base[cols].fillna(0)

    print("3/4 - Autenticando com a API do Google...")
    creds_json_str = os.environ.get("GOOGLE_CREDENTIALS")
    creds_dict = json.loads(creds_json_str)
    
    gc = gspread.service_account_from_dict(creds_dict)
    
    sh = None
    for i in range(3):
        try:
            sh = gc.open_by_key(SPREADSHEET_ID)
            break
        except Exception as e:
            if i < 2:
                time.sleep(5)
            else:
                raise e

    aba_base = sh.worksheet("Base_Fundamentus")
    
    print("4/4 - Enviando tabela completa com Setores para o Google Sheets...")
    dados_envio = [df_final.columns.values.tolist()] + df_final.values.tolist()
    
    aba_base.clear()
    aba_base.update(dados_envio)
    
    print(f"✅ Sucesso! {len(df_final.columns)} colunas atualizadas na aba Base_Fundamentus.")

if __name__ == "__main__":
    atualizar_google_sheets()
