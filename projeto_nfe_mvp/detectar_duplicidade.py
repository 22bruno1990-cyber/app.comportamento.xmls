import os
import hashlib
import pandas as pd
import xml.etree.ElementTree as ET

PASTA_XMLS = "xmls"
PASTA_SAIDA = "saida"
ARQUIVO_SAIDA = os.path.join(PASTA_SAIDA, "relatorio_duplicidade.csv")

NAMESPACE = {"nfe": "http://www.portalfiscal.inf.br/nfe"}


def ler_texto(root, xpath):
    elemento = root.find(xpath, NAMESPACE)
    return elemento.text.strip() if elemento is not None and elemento.text else ""


def gerar_hash_arquivo(caminho_arquivo):
    with open(caminho_arquivo, "rb") as f:
        conteudo = f.read()
    return hashlib.sha256(conteudo).hexdigest()


def extrair_dados_xml(caminho_arquivo):
    tree = ET.parse(caminho_arquivo)
    root = tree.getroot()

    infnfe = root.find(".//nfe:infNFe", NAMESPACE)
    id_nfe = infnfe.attrib.get("Id", "") if infnfe is not None else ""

    numero_nf = ler_texto(root, ".//nfe:nNF")
    serie = ler_texto(root, ".//nfe:serie")
    data_emissao = ler_texto(root, ".//nfe:dhEmi")
    cnpj_emitente = ler_texto(root, ".//nfe:emit/nfe:CNPJ")
    razao_social_emitente = ler_texto(root, ".//nfe:emit/nfe:xNome")
    cnpj_destinatario = ler_texto(root, ".//nfe:dest/nfe:CNPJ")
    valor_nf = ler_texto(root, ".//nfe:total/nfe:ICMSTot/nfe:vNF")
    info_adicional = ler_texto(root, ".//nfe:infAdic/nfe:infCpl")

    return {
        "id_nfe": id_nfe,
        "numero_nf": numero_nf,
        "serie": serie,
        "data_emissao": data_emissao,
        "cnpj_emitente": cnpj_emitente,
        "razao_social_emitente": razao_social_emitente,
        "cnpj_destinatario": cnpj_destinatario,
        "valor_nf": valor_nf,
        "info_adicional": info_adicional,
    }


def classificar_linha(row):
    motivos = []

    if row["dup_id_nfe"]:
        motivos.append("ID_NFE_DUPLICADO")

    if row["dup_chave_negocio"]:
        motivos.append("CHAVE_NEGOCIO_DUPLICADA")

    if row["dup_hash_arquivo"]:
        motivos.append("HASH_ARQUIVO_REPETIDO")

    if not motivos:
        return "NORMAL"

    return " | ".join(motivos)


def main():
    if not os.path.exists(PASTA_XMLS):
        print(f"A pasta '{PASTA_XMLS}' não existe.")
        print("Rode primeiro o script gerar_200_xmls.py")
        return

    arquivos_xml = [a for a in os.listdir(PASTA_XMLS) if a.lower().endswith(".xml")]

    if not arquivos_xml:
        print(f"Nenhum XML encontrado na pasta '{PASTA_XMLS}'.")
        return

    dados = []

    for arquivo in arquivos_xml:
        caminho = os.path.join(PASTA_XMLS, arquivo)

        try:
            hash_arquivo = gerar_hash_arquivo(caminho)
            dados_xml = extrair_dados_xml(caminho)

            dados.append({
                "arquivo": arquivo,
                "hash_arquivo": hash_arquivo,
                **dados_xml
            })

        except Exception as e:
            dados.append({
                "arquivo": arquivo,
                "hash_arquivo": "",
                "id_nfe": "",
                "numero_nf": "",
                "serie": "",
                "data_emissao": "",
                "cnpj_emitente": "",
                "razao_social_emitente": "",
                "cnpj_destinatario": "",
                "valor_nf": "",
                "info_adicional": f"ERRO_LEITURA_XML: {e}",
            })

    df = pd.DataFrame(dados)

    df["dup_id_nfe"] = df.duplicated(subset=["id_nfe"], keep=False) & (df["id_nfe"] != "")

    df["dup_chave_negocio"] = df.duplicated(
        subset=["numero_nf", "serie", "cnpj_emitente", "valor_nf"],
        keep=False
    ) & (df["numero_nf"] != "") & (df["cnpj_emitente"] != "")

    df["dup_hash_arquivo"] = df.duplicated(subset=["hash_arquivo"], keep=False) & (df["hash_arquivo"] != "")

    df["status_fraude"] = df.apply(classificar_linha, axis=1)

    os.makedirs(PASTA_SAIDA, exist_ok=True)
    df.to_csv(ARQUIVO_SAIDA, index=False, encoding="utf-8-sig")

    print("Análise concluída com sucesso.")
    print(f"Total de arquivos analisados: {len(df)}")
    print(f"Relatório gerado em: {ARQUIVO_SAIDA}")
    print("\nResumo dos status:")
    print(df["status_fraude"].value_counts())


if __name__ == "__main__":
    main()
