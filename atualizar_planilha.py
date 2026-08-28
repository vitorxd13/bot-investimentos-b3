import os
import json
import time
import requests
import gspread
import pandas as pd
from bs4 import BeautifulSoup

SPREADSHEET_ID = "1LgK6yLEfYZaOOTHiI-r_FdQggSeJPUO_JBtamCfpi80"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

def obter_mapa_setores_fundamentus():
    """Raspagem oficial da árvore de setores e subsetores do Fundamentus."""
    print("1/4 - Baixando mapa completo de Setores e Subsetores do Fundamentus...")
    url_busca = "https://www.fundamentus.com.br/busca_avancada.php"
    
    mapa_ticker_setor = {}
    
    try:
        response = requests.get(url_busca, headers=HEADERS, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Pega todas as opções do menu suspenso de setores do site
        select_setor = soup.find('select', {'name': 'setor'})
        if not select_setor:
            return mapa_ticker_setor

        opcoes = select_setor.find_all('option')
        
        for opt in opcoes:
            setor_id = opt.get('value')
            setor_nome = opt.text.strip()
            
            if not setor_id or setor_id == '0':
                continue
                
            url_setor = f"https://www.fundamentus.com.br/resultado.php?setor={setor_id}"
            res_setor = requests.get(url_setor, headers=HEADERS, timeout=30)
            res_setor.encoding = 'iso-8859-1'
            
            try:
                dfs = pd.read_html(res_setor.text)
                if dfs and len(dfs) > 0:
                    df_setor = dfs[0]
                    for ticker in df_setor['Papel']:
                        mapa_ticker_setor[str(ticker).strip()] = setor_nome
            except Exception:
                continue
            
            time.sleep(0.2) # Pausa rápida para não sobrecarregar o site
            
    except Exception as e:
        print(f"Aviso ao rastrear setores: {e}")
        
    return mapa_ticker_setor

def obter_base_fundamentus():
    url = "https://www.fundamentus.com.br/resultado.php"
    for tentativa in range(3):
        try:
            print(f"2/4 - Baixando indicadores dos papéis (Tentativa {tentativa + 1}/3)...")
            response = requests.get(url, headers=HEADERS, timeout=30)
            response.encoding = 'iso-8859-1'
            dfs = pd.read_html(response.text, decimal=',', thousands='.')
            return dfs[0]
        except Exception as e:
            if tentativa < 2:
                time.sleep(5)
            else:
                raise e

def atualizar_google_sheets():
    # 1. Busca os setores reais do site
    mapa_setores = obter_mapa_setores_fundamentus()
    
    # 2. Busca a tabela de indicadores
    df_base = obter_base_fundamentus()
    
    print("3/4 - Vinculando setores oficiais a cada ação...")
    df_base['Setor'] = df_base['Papel'].map(mapa_setores).fillna('Não Classificado')
    df_base['Subsetor'] = df_base['Setor']
    
    # Organiza colunas colocando Setor e Subsetor logo após o Papel
    cols = ['Papel', 'Setor', 'Subsetor'] + [c for c in df_base.columns if c not in ['Papel', 'Setor', 'Subsetor']]
    df_final = df_base[cols].fillna(0)

    print("4/4 - Autenticando e enviando para o Google Sheets...")
    creds_json_str = os.environ.get("GOOGLE_CREDENTIALS")
    creds_dict = json.loads(creds_json_str)
    
    gc = gspread.service_account_from_dict(creds_dict)
    sh = gc.open_by_key(SPREADSHEET_ID)
    aba_base = sh.worksheet("Base_Fundamentus")
    
    dados_envio = [df_final.columns.values.tolist()] + df_final.values.tolist()
    aba_base.clear()
    aba_base.update(dados_envio)
    
    print(f"✅ Sucesso! Tabela atualizada com setores oficiais do Fundamentus.")

if __name__ == "__main__":
    atualizar_google_sheets()
