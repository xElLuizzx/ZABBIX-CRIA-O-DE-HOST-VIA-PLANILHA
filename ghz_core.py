# ghz_core.py
import datetime
import re
import pandas as pd
import requests
from bs4 import BeautifulSoup

MACRO_IP = "{$IP}"
MACRO_PORTA = "{$PP}"

def gerar_hosts(modo, fonte, caminho_saida=None):
    """
    Gera hosts Zabbix a partir de site ou planilha.
    Retorna o caminho do arquivo YAML gerado.
    """
    agora = datetime.datetime.now()
    data_tag = agora.strftime("%d-%m-%Y_%H-%M")

    if modo == "site":
        resp = requests.get(fonte, timeout=15)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        a_tags = soup.find_all("a", class_="cameraIcon")
        div_tags = soup.find_all("div", attrs={"dados_das_colunas": True})

        df = pd.DataFrame(columns=[
            "Nome", "IP", "Dns", "Porta",
            "MACRO 1", "VALOR 1",
            "MACRO 2", "VALOR 2"
        ])

        for a, div in zip(a_tags, div_tags):
            nome = a.get_text(strip=True).split(" - ")[0]
            title = div.get("data-original-title", "")

            # Regex para RTSP (qualquer usuário)
            match = re.search(
                r"rtsp://(.+?):(.+?)@(.+?):(\d+)/cam/realmonitor",
                title
            )
            if not match:
                continue

            usuario = match.group(1)
            senha = match.group(2)
            ip = match.group(3)
            porta = int(match.group(4))

            df.loc[len(df)] = [
                nome, ip, "", porta,
                MACRO_IP, ip,
                MACRO_PORTA, porta
            ]

    elif modo == "planilha":
        df = pd.read_excel(fonte)

    else:
        raise Exception("Modo inválido")

    yaml = f"""zabbix_export:
  version: '6.0'
  date: '{agora.isoformat()}'
  groups:
    - name: 'Template TCP'
  hosts:
"""

    for _, row in df.iterrows():
        yaml += f"""
    - host: '{row['Nome']}'
      name: '{row['Nome']}'
      templates:
        - name: 'TESTE DE PORTA TCP VARIAVEL - DVR'
      groups:
        - name: 'Template TCP'
      interfaces:
        - ip: {row['IP']}
          dns: {row['Dns']}
          port: '{int(row['Porta'])}'
          interface_ref: if1
      macros:
        - macro: '{row['MACRO 1']}'
          value: {row['VALOR 1']}
        - macro: '{row['MACRO 2']}'
          value: '{row['VALOR 2']}'
      inventory_mode: DISABLED
"""

    # Caminho de saída padrão se não informado
    if not caminho_saida:
        caminho_saida = f"HOSTS_ZABBIX_{data_tag}.yaml"

    with open(caminho_saida, "w", encoding="utf-8") as f:
        f.write(yaml)

    return caminho_saida

