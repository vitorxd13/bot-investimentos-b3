import os
import json
import time
import requests
import gspread
import pandas as pd

SPREADSHEET_ID = "1LgK6yLEfYZaOOTHil-r_FdQgSeJPUO_JBtamCfpi80"

def obter_tabela_completa_fundamentus():
    url = "https://www.fundamentus.com.br/resultado.php"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    response = requests.get(url, headers=headers)
    response.encoding = 'iso-8859-1'
    
    dfs = pd.read_html(response.text, decimal=',', thousands='.')
    df = dfs[0]
    df = df.fillna(0)
    return df

def atualizar_google_sheets():
    print("1/3 - Baixando a tabela completa de 21 colunas do Fundamentus...")
    df = obter_tabela_completa_fundamentus()

    print("2/3 - Autenticando com a API do Google...")
    creds_json_str = os.environ.get("GOOGLE_CREDENTIALS")
    creds_dict = json.loads(creds_json_str)
    
    gc = gspread.service_account_from_dict(creds_dict)
    
    # Tentativa de conexão com retry em caso de erro 503 do Google
    tentativas = 3
    sh = None
    for i in range(tentativas):
        try:
            sh = gc.open_by_key(SPREADSHEET_ID)
            break
        except gspread.exceptions.APIError as e:
            if i < tentativas - 1:
                print(f"Instabilidade temporária no Google (503). Re-tentando em 5 segundos... (Tentativa {i+1}/{tentativas})")
                time.sleep(5)
            else:
                raise e

    aba_base = sh.worksheet("Base_Fundamentus")
    
    print("3/3 - Enviando todas as 21 colunas para a planilha...")
    dados_envio = [df.columns.values.tolist()] + df.values.tolist()
    
    # Atualização com retry automático
    for i in range(tentativas):
        try:
            aba_base.clear()
            aba_base.update(dados_envio)
            break
        except gspread.exceptions.APIError as e:
            if i < tentativas - 1:
                print(f"Erro de envio (503). Re-tentando em 5 segundos... (Tentativa {i+1}/{tentativas})")
                time.sleep(5)
            else:
                raise e
    
    print(f"✅ Sucesso! {len(df.columns)} colunas e {len(df)} ações salvas na aba Base_Fundamentus.")

if __name__ == "__main__":
    atualizar_google_sheets()
