import os
import json
import time
import requests
import gspread
import pandas as pd

SPREADSHEET_ID = "1LgK6yLEfYZaOOTHiI-r_FdQggSeJPUO_JBtamCfpi80"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

def obter_mapa_setores_cvm():
    """Baixa a base oficial de companhias abertas da CVM para mapear Setor e Subsetor."""
    try:
        print("1/5 - Baixando cadastro oficial de setores da CVM...")
        url_cvm = "https://dados.cvm.gov.br/dados/CIA_ABERTA/CAD/DADOS/cad_cia_aberta.csv"
        df_cvm = pd.read_csv(url_cvm, sep=';', encoding='iso-8859-1')
        
        # Filtra apenas empresas ativas
        df_cvm = df_cvm[df_cvm['SIT'] == 'ATIVO']
        
        # Seleciona CNPJ/Nome, Setor de Atividade e cria mapeamento
        df_setores = df_cvm[['DENOM_SOCIAL', 'SETOR_ATIV']].dropna().drop_duplicates()
        return df_cvm
    except Exception as e:
        print(f"Aviso ao buscar dados da CVM: {e}")
        return pd.DataFrame()

def obter_base_fundamentus():
    """Baixa os indicadores fundamentalistas do Fundamentus."""
    url = "https://www.fundamentus.com.br/resultado.php"
    for tentativa in range(3):
        try:
            print(f"2/5 - Baixando dados do Fundamentus (Tentativa {tentativa + 1}/3)...")
            response = requests.get(url, headers=HEADERS, timeout=30)
            response.encoding = 'iso-8859-1'
            dfs = pd.read_html(response.text, decimal=',', thousands='.')
            return dfs[0]
        except Exception as e:
            if tentativa < 2:
                time.sleep(5)
            else:
                raise e

def obter_de_para_setores_b3():
    """Mapeamento direto dos principais setores/subsetores da B3 por radical do Ticker."""
    # Mapeamento rápido e preciso para as ações mais negociadas da B3
    mapa_direto = {
        'Financeiro': ['BBAS', 'BBDC', 'ITUB', 'SANB', 'BPAC', 'ITSA', 'BBSE', 'PSSA', 'CXSE', 'BRSR', 'ABCB'],
        'Energia Elétrica': ['ELET', 'EGIE', 'TRPL', 'TAEE', 'CPFE', 'CMIG', 'NEOE', 'EQTL', 'AURE', 'SBSP', 'CPLE'],
        'Petróleo & Gás': ['PETR', 'PRIO', 'UGPA', 'VBBR', 'RRRP', 'RECV', 'RPMG'],
        'Mineração & Siderurgia': ['VALE', 'GGBR', 'CSNA', 'USIM', 'CMIN'],
        'Consumo / Varejo': ['MGLU', 'LREN', 'ABEV', 'JBSS', 'BRFS', 'BEEF', 'MRFG', 'ARZZ', 'SOMA', 'PETZ', 'NTCO'],
        'Bens Industriais / Logística': ['WEGE', 'RENT', 'RAIL', 'CCRO', 'GOLL', 'AZUL', 'EMBR', 'TOTS', 'POMO'],
        'Construção Civil': ['CYRE', 'EZTC', 'MRVE', 'CURY', 'DIRR', 'TEND', 'PLPL'],
        'Saúde': ['RDOR', 'HAPV', 'FLRY', 'QUAL', 'RADL', 'VVEO']
    }
    return mapa_direto

def aplicar_setores(df_fundamentus):
    """Aplica o setor e subsetor no DataFrame do Fundamentus."""
    mapa = obter_de_para_setores_b3()
    
    def identificar_setor(ticker):
        radical = str(ticker)[:4]
        for setor, radicais in mapa.items():
            if radical in radicais:
                return setor
        return 'Outros / Diversos'

    df_fundamentus['Setor'] = df_fundamentus['Papel'].apply(identificar_setor)
    df_fundamentus['Subsetor'] = df_fundamentus['Setor'] # Réplica inicial para organização
    return df_fundamentus

def atualizar_google_sheets():
    df_base = obter_base_fundamentus()
    
    print("3/5 - Classificando Setores e Subsetores...")
    df_base = aplicar_setores(df_base)
        
    # Reorganiza para colocar Setor e Subsetor ao lado do Papel
    cols = ['Papel', 'Setor', 'Subsetor'] + [c for c in df_base.columns if c not in ['Papel', 'Setor', 'Subsetor']]
    df_final = df_base[cols].fillna(0)

    print("4/5 - Autenticando com a API do Google...")
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
    
    print("5/5 - Enviando tabela preenchida com Setores...")
    dados_envio = [df_final.columns.values.tolist()] + df_final.values.tolist()
    
    aba_base.clear()
    aba_base.update(dados_envio)
    
    print(f"✅ Sucesso! {len(df_final.columns)} colunas atualizadas na aba Base_Fundamentus.")

if __name__ == "__main__":
    atualizar_google_sheets()
