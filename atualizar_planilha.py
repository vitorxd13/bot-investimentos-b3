import os
import json
import time
import requests
import gspread
import pandas as pd

SPREADSHEET_ID = "1LgK6yLEfYZaOOTHiI-r_FdQggSeJPUO_JBtamCfpi80"

def obter_tabela_completa_fundamentus():
    url = "https://www.fundamentus.com.br/resultado.php"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    
    for tentativa in range(3):
        try:
            print(f"1/3 - Baixando tabela do Fundamentus (Tentativa {tentativa + 1}/3)...")
            response = requests.get(url, headers=headers, timeout=30)
            response.encoding = 'iso-8859-1'
            dfs = pd.read_html(response.text, decimal=',', thousands='.')
            df = dfs[0]
            return df.fillna(0)
        except Exception as e:
            if tentativa < 2:
                time.sleep(5)
            else:
                raise e

def atualizar_google_sheets():
    df = obter_tabela_completa_fundamentus()

    print("2/3 - Autenticando com a API do Google...")
    creds_json_str = os.environ.get("GOOGLE_CREDENTIALS")
    creds_dict = json.loads(creds_json_str)
    
    gc = gspread.service_account_from_dict(creds_dict)
    sh = gc.open_by_key(SPREADSHEET_ID)
    aba_base = sh.worksheet("Base_Fundamentus")
    
    print("3/3 - Enviando dados limpos para o Google Sheets...")
    dados_envio = [df.columns.values.tolist()] + df.values.tolist()
    
    aba_base.clear()
    aba_base.update(dados_envio)
    
    print(f"✅ Sucesso! Tabela bruta com {len(df.columns)} colunas atualizada na aba Base_Fundamentus.")

if __name__ == "__main__":
    atualizar_google_sheets()
