import os
import json
import requests
import gspread
import pandas as pd

SPREADSHEET_ID = "1LgK6yLEfYZaOOTHiI-r_FdQggSeJPUO_JBtamCfpi80"

def obter_dados_fundamentus_direto():
    """Baixa e trata a tabela do Fundamentus via HTTP direto sem dependências instáveis."""
    url = "https://www.fundamentus.com.br/resultado.php"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    response = requests.get(url, headers=headers)
    
    # O Fundamentus usa codificação ISO-8859-1
    response.encoding = 'iso-8859-1'
    
    # Lê a tabela HTML direto para o pandas
    dfs = pd.read_html(response.text, decimal=',', thousands='.')
    df = dfs[0]
    
    return df

def atualizar_google_sheets():
    print("1/3 - Obtendo cotações e indicadores das ações no Fundamentus...")
    df = obter_dados_fundamentus_direto()
    
    # Mapeamento de colunas da tabela web do Fundamentus para a sua planilha
    colunas_mapeadas = {
        'Papel': 'Papel',
        'Cotação': 'Cotação',
        'P/L': 'P/L',
        'P/VP': 'P/VP',
        'PSR': 'PSR',
        'Div.Yield': 'DY (%)',
        'P/EBIT': 'P/EBIT',
        'P/Ativos': 'P/Ativos',
        'Mrg Ebit': 'Margem EBIT (%)',
        'Mrg.Liq': 'Margem Líquida (%)',
        'ROE': 'ROE (%)',
        'ROIC': 'ROIC (%)',
        'Div.Br/ Patrim': 'Dív. Líq / Patrimônio',
        'Cres.Rec.5a': 'Crescimento Rec. 5a (%)',
        'Liq.2meses': 'Liquidez Diária (R$)',
        'Patrim.Liq': 'Patrimônio Líquido'
    }
    
    cols_existentes = [c for c in colunas_mapeadas.keys() if c in df.columns]
    df_tratado = df[cols_existentes].rename(columns=colunas_mapeadas)
    
    # Tratamento de valores string percentuais caso venham com o símbolo %
    cols_pct = ['DY (%)', 'Margem EBIT (%)', 'Margem Líquida (%)', 'ROE (%)', 'ROIC (%)', 'Crescimento Rec. 5a (%)']
    for c in cols_pct:
        if c in df_tratado.columns:
            df_tratado[c] = df_tratado[c].astype(str).str.replace('%', '').str.replace('.', '').str.replace(',', '.')
            df_tratado[c] = pd.to_numeric(df_tratado[c], errors='coerce').fillna(0)

    # Limpeza final de nulos
    df_tratado = df_tratado.fillna(0)

    print("2/3 - Autenticando com a API do Google...")
    creds_json_str = os.environ.get("GOOGLE_CREDENTIALS")
    creds_dict = json.loads(creds_json_str)
    
    gc = gspread.service_account_from_dict(creds_dict)
    sh = gc.open_by_key(SPREADSHEET_ID)
    
    aba_base = sh.worksheet("Base_Fundamentus")
    
    print("3/3 - Enviando dados para o Google Sheets...")
    dados_envio = [df_tratado.columns.values.tolist()] + df_tratado.values.tolist()
    aba_base.clear()
    aba_base.update(dados_envio)
    
    print("✅ Sucesso! A aba Base_Fundamentus foi preenchida com todas as ações da B3.")

if __name__ == "__main__":
    atualizar_google_sheets()
