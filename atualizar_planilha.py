import os
import json
import requests
import gspread
import pandas as pd

SPREADSHEET_ID = "1LgK6yLEFYZaOOTHil-r_FdQgSeJPUO_JBtamCfpi80"

def obter_tabela_completa_fundamentus():
    url = "https://www.fundamentus.com.br/resultado.php"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    response = requests.get(url, headers=headers)
    response.encoding = 'iso-8859-1'
    
    # Captura a tabela idêntica ao site do Fundamentus
    dfs = pd.read_html(response.text, decimal=',', thousands='.')
    df = dfs[0]
    
    # Tratamento de valores para garantir o envio sem erros no JSON
    df = df.fillna(0)
    return df

def atualizar_google_sheets():
    print("1/3 - Baixando a tabela completa de 21 colunas do Fundamentus...")
    df = obter_tabela_completa_fundamentus()

    print("2/3 - Autenticando com a API do Google...")
    creds_json_str = os.environ.get("GOOGLE_CREDENTIALS")
    creds_dict = json.loads(creds_json_str)
    
    gc = gspread.service_account_from_dict(creds_dict)
    sh = gc.open_by_key(SPREADSHEET_ID)
    
    aba_base = sh.worksheet("Base_Fundamentus")
    
    print("3/3 - Enviando todas as colunas para a planilha...")
    dados_envio = [df.columns.values.tolist()] + df.values.tolist()
    aba_base.clear()
    aba_base.update(dados_envio)
    
    print(f"✅ Sucesso! {len(df.columns)} colunas e {len(df)} ações atualizadas na aba Base_Fundamentus.")

if __name__ == "__main__":
    atualizar_google_sheets()
