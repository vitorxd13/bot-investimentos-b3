import os
import json
import gspread
import pandas as pd
import fundamentus

# ID da sua planilha extraído da URL do Google Sheets
SPREADSHEET_ID = "1LgK6yLEFYZaOOTHil-r_FdQgSeJPUO_JBtamCfpi80"

def atualizar_google_sheets():
    print("1/3 - Obtendo cotações e indicadores das ações no Fundamentus...")
    
    # Captura os dados do Fundamentus com compatibilidade de versão
    try:
        df = fundamentus.get_resultado()
    except AttributeError:
        df = fundamentus.get_resultado_raw()
        
    df = df.reset_index()
    
    colunas_mapeadas = {
        'papel': 'Papel',
        'cotacao': 'Cotação',
        'pl': 'P/L',
        'pvp': 'P/VP',
        'psr': 'PSR',
        'dy': 'DY (%)',
        'pebit': 'P/EBIT',
        'pa': 'P/Ativos',
        'mrgbruta': 'Margem Bruta (%)',
        'mrgebit': 'Margem EBIT (%)',
        'mrgliq': 'Margem Líquida (%)',
        'roe': 'ROE (%)',
        'roic': 'ROIC (%)',
        'divbpat': 'Dív. Líq / Patrimônio',
        'divlebit': 'Dív. Líq / EBIT',
        'cresrec5': 'Crescimento Rec. 5a (%)',
        'liquidez': 'Liquidez Diária (R$)',
        'patrim': 'Patrimônio Líquido'
    }
    
    cols_existentes = [c for c in colunas_mapeadas.keys() if c in df.columns]
    df_tratado = df[cols_existentes].rename(columns=colunas_mapeadas)
    
    # Converte decimais para percentuais (ex: 0.082 vira 8.2%)
    cols_pct = ['DY (%)', 'Margem Bruta (%)', 'Margem EBIT (%)', 'Margem Líquida (%)', 'ROE (%)', 'ROIC (%)', 'Crescimento Rec. 5a (%)']
    for c in cols_pct:
        if c in df_tratado.columns:
            df_tratado[c] = df_tratado[c] * 100

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
