import sys
sys.tracebacklimit = 0

import os
import pandas as pd
import requests
import datetime
from bs4 import BeautifulSoup
import re

# ================= CONFIG =================
MACRO_IP = "{$IP}"
MACRO_PORTA = "{$PP}"

# ================= DATA ===================
agora = datetime.datetime.now()
data_tag = agora.strftime("%d-%m-%Y_%H-%M")

# ================= MENU ===================
print("\n=== GERADOR DE HOSTS ZABBIX ===")
print("1 - SITE (CityCam / Web)")
print("2 - PLANILHA DVR")

opcao = input("Escolha a opção: ").strip()

# =====================================================
# ================= OPÇÃO 1 - SITE ====================
# =====================================================
if opcao == "1":
    url = input("\nDigite a URL do site: ").strip()

    if not url.startswith("http"):
        print("[ERRO] URL inválida")
        sys.exit()

    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        html = resp.text
        print("[OK] Site acessado")
    except Exception as e:
        print(f"[ERRO] Falha ao acessar site: {e}")
        sys.exit()

    soup = BeautifulSoup(html, "html.parser")

    a_tags = soup.find_all("a", class_="cameraIcon")
    div_tags = soup.find_all("div", attrs={"dados_das_colunas": True})

    if not a_tags or not div_tags:
        print("[ERRO] Estrutura do site não reconhecida")
        sys.exit()

    df = pd.DataFrame(columns=["Nome", "IP", "Dns", "Porta",
                               "MACRO 1", "VALOR 1",
                               "MACRO 2", "VALOR 2"])

    for a, div in zip(a_tags, div_tags):
        try:
            nome = a.get_text(strip=True).split(" - ")[0]
            title = div.get("data-original-title", "")

            match = re.search(
                r"rtsp://admin:(.+)@(.+):(\d+)/cam/realmonitor",
                title
            )

            if not match:
                print("[AVISO] RTSP fora do padrão")
                continue

            ip = match.group(2)
            porta = int(match.group(3))

            df.loc[len(df)] = [
                nome,
                ip,
                "",
                porta,
                MACRO_IP,
                ip,
                MACRO_PORTA,
                porta
            ]

            print(f"[OK] {nome} -> {ip}:{porta}")

        except Exception as e:
            print(f"[ERRO] Falha ao processar câmera: {e}")

# =====================================================
# ================= OPÇÃO 2 - PLANILHA ================
# =====================================================
elif opcao == "2":
    pasta = os.path.dirname(os.path.abspath(__file__))
    planilhas = [f for f in os.listdir(pasta) if f.lower().endswith(".xlsx")]

    # ===== NÃO ACHOU PLANILHA → CRIA BASE =====
    if not planilhas:
        print("[AVISO] Nenhuma planilha encontrada.")
        print("[INFO] Criando planilha BASE...")

        colunas = [
            "Nome", "IP", "Dns", "Porta",
            "MACRO 1", "VALOR 1",
            "MACRO 2", "VALOR 2"
        ]

        df_base = pd.DataFrame([{
            "Nome": "EXEMPLO-DVR-01",
            "IP": "192.168.0.10",
            "Dns": "dvr.exemplo.local",
            "Porta": 37777,
            "MACRO 1": MACRO_IP,
            "VALOR 1": "192.168.0.10",
            "MACRO 2": MACRO_PORTA,
            "VALOR 2": 37777
        }], columns=colunas)

        nome_base = "BASE.xlsx"
        df_base.to_excel(os.path.join(pasta, nome_base), index=False)

        print(f"[OK] Planilha base criada: {nome_base}")
        print("Preencha a planilha e execute novamente.")
        sys.exit()

    # ===== LISTA PLANILHAS =====
    print("\nPlanilhas encontradas:")
    for i, p in enumerate(planilhas, start=1):
        print(f"{i} - {p}")

    escolha = input("Escolha o número da planilha: ").strip()

    if not escolha.isdigit() or not (1 <= int(escolha) <= len(planilhas)):
        print("[ERRO] Opção inválida")
        sys.exit()

    arquivo = planilhas[int(escolha) - 1]

    try:
        df = pd.read_excel(os.path.join(pasta, arquivo))
        print(f"[OK] Planilha '{arquivo}' carregada")
    except Exception as e:
        print(f"[ERRO] Falha ao ler planilha: {e}")
        sys.exit()

    # ===== VALIDA COLUNAS =====
    colunas_necessarias = {
        "Nome", "IP", "Dns", "Porta",
        "MACRO 1", "VALOR 1",
        "MACRO 2", "VALOR 2"
    }

    if not colunas_necessarias.issubset(df.columns):
        print("[ERRO] Planilha fora do padrão.")
        print("Colunas obrigatórias:")
        for c in colunas_necessarias:
            print(f" - {c}")
        sys.exit()

else:
    print("[ERRO] Opção inválida")
    sys.exit()

# =====================================================
# ================= GERADOR YAML ======================
# =====================================================
yaml = f"""zabbix_export:
  version: '6.0'
  date: '{agora.isoformat()}'
  groups:
    - name: 'Template TCP'
  hosts:
"""

for i, row in df.iterrows():
    try:
        porta = int(row["Porta"])
    except:
        print(f"[ERRO] Porta inválida na linha {i+1}")
        continue

    yaml += f"""
    - host: 'TESTE PORTA TCP VARIAVEL - {row["Nome"]}'
      name: '{row["Nome"]}'
      templates:
        - name: 'TESTE DE PORTA TCP VARIAVEL - DVR'
      groups:
        - name: 'Template TCP'
      interfaces:
        - ip: {row["IP"]}
          dns: {row["Dns"]}
          port: '{porta}'
          interface_ref: if1
      macros:
        - macro: '{row["MACRO 1"]}'
          value: {row["VALOR 1"]}
        - macro: '{row["MACRO 2"]}'
          value: '{row["VALOR 2"]}'
      inventory_mode: DISABLED
"""

nome_yaml = f"HOSTS_ZABBIX_{data_tag}.yaml"

with open(nome_yaml, "w", encoding="utf-8") as f:
    f.write(yaml)

print(f"\n[OK] YAML gerado: {nome_yaml}")
print("=== PROCESSO FINALIZADO ===")
