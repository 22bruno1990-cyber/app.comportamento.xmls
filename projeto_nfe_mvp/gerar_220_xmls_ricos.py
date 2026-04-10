import os
import random
from datetime import datetime, timedelta

PASTA_XMLS = "xmls_ricos"
os.makedirs(PASTA_XMLS, exist_ok=True)

random.seed(42)

emitentes = [
    ("12345678000195", "Alpha Tecnologia LTDA"),
    ("98765432000111", "Beta Serviços SA"),
    ("45678912000166", "Gamma Logística ME"),
    ("74185296000188", "Delta Comércio LTDA"),
    ("85296374000155", "Omega Sistemas SA"),
    ("96385274100014", "Sigma Analytics LTDA"),
]

usuarios_envio = [
    "ana.silva",
    "bruno.mendes",
    "carla.santos",
    "diego.lima",
    "elaine.rocha",
    "felipe.costa",
]

pacientes = [
    ("Mariana Souza", "11122233344"),
    ("Carlos Pereira", "22233344455"),
    ("Fernanda Lima", "33344455566"),
    ("João Martins", "44455566677"),
    ("Patricia Alves", "55566677788"),
    ("Ricardo Gomes", "66677788899"),
    ("Camila Rocha", "77788899900"),
    ("Eduardo Silva", "88899900011"),
]

prestadores = [
    "Clínica Saúde Integrada",
    "Hospital Vida Plena",
    "Centro Médico Avançado",
    "Laboratório Diagnóstico Alfa",
    "OrtoCare Especialidades",
]

procedimentos = [
    "Consulta clínica",
    "Exame de sangue",
    "Ressonância magnética",
    "Fisioterapia",
    "Ultrassonografia",
    "Consulta ortopédica",
    "Tomografia",
    "Avaliação cardiológica",
]

eventos_clinicos = [
    "Atendimento ambulatorial",
    "Procedimento eletivo",
    "Retorno médico",
    "Exame complementar",
    "Sessão terapêutica",
]

cnpj_destinatario = "11222333000144"
nome_destinatario = "Operadora Benefícios Saúde SA"


def limpar_pasta():
    for arquivo in os.listdir(PASTA_XMLS):
        if arquivo.endswith(".xml"):
            os.remove(os.path.join(PASTA_XMLS, arquivo))


def gerar_chave_fake(numero: int) -> str:
    base = f"35{random.randint(100000000000, 999999999999)}{numero:09d}{random.randint(1000000000000000000, 9999999999999999999)}"
    return base[:44]


def gerar_guia():
    return f"GUIA{random.randint(100000, 999999)}"


def gerar_xml(registro: dict) -> str:
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<NFe xmlns="http://www.portalfiscal.inf.br/nfe">
  <infNFe Id="NFe{registro["chave"]}" versao="4.00">
    <ide>
      <cUF>35</cUF>
      <cNF>{random.randint(10000000, 99999999)}</cNF>
      <natOp>Prestacao de servico</natOp>
      <mod>55</mod>
      <serie>{registro["serie"]}</serie>
      <nNF>{registro["numero_nf"]}</nNF>
      <dhEmi>{registro["data_emissao"]}</dhEmi>
      <tpNF>1</tpNF>
      <idDest>1</idDest>
      <cMunFG>3550308</cMunFG>
      <tpImp>1</tpImp>
      <tpEmis>1</tpEmis>
      <finNFe>1</finNFe>
      <indFinal>1</indFinal>
      <indPres>1</indPres>
      <procEmi>0</procEmi>
      <verProc>1.0</verProc>
    </ide>

    <emit>
      <CNPJ>{registro["cnpj_emitente"]}</CNPJ>
      <xNome>{registro["razao_social_emitente"]}</xNome>
      <enderEmit>
        <xLgr>Rua Exemplo</xLgr>
        <nro>{random.randint(10, 999)}</nro>
        <xBairro>Centro</xBairro>
        <cMun>3550308</cMun>
        <xMun>Sao Paulo</xMun>
        <UF>SP</UF>
        <CEP>01000000</CEP>
        <cPais>1058</cPais>
        <xPais>Brasil</xPais>
      </enderEmit>
      <IE>{random.randint(100000000, 999999999)}</IE>
      <CRT>3</CRT>
    </emit>

    <dest>
      <CNPJ>{cnpj_destinatario}</CNPJ>
      <xNome>{nome_destinatario}</xNome>
      <enderDest>
        <xLgr>Av Beneficios</xLgr>
        <nro>1000</nro>
        <xBairro>Paulista</xBairro>
        <cMun>3550308</cMun>
        <xMun>Sao Paulo</xMun>
        <UF>SP</UF>
        <CEP>01310000</CEP>
        <cPais>1058</cPais>
        <xPais>Brasil</xPais>
      </enderDest>
      <indIEDest>9</indIEDest>
    </dest>

    <det nItem="1">
      <prod>
        <cProd>ITEM{random.randint(100,999)}</cProd>
        <xProd>{registro["procedimento"]}</xProd>
        <CFOP>5933</CFOP>
        <uCom>UN</uCom>
        <qCom>1.0000</qCom>
        <vUnCom>{registro["valor_nf"]:.2f}</vUnCom>
        <vProd>{registro["valor_nf"]:.2f}</vProd>
      </prod>
    </det>

    <total>
      <ICMSTot>
        <vProd>{registro["valor_nf"]:.2f}</vProd>
        <vNF>{registro["valor_nf"]:.2f}</vNF>
      </ICMSTot>
    </total>

    <pag>
      <detPag>
        <tPag>90</tPag>
        <vPag>{registro["valor_nf"]:.2f}</vPag>
      </detPag>
    </pag>

    <infAdic>
      <infCpl>
usuario_envio={registro["usuario_envio"]} |
paciente={registro["paciente"]} |
cpf_paciente={registro["cpf_paciente"]} |
prestador={registro["prestador"]} |
procedimento={registro["procedimento"]} |
data_atendimento={registro["data_atendimento"]} |
evento_clinico={registro["evento_clinico"]} |
guia_atendimento={registro["guia_atendimento"]} |
lote={registro["lote"]}
      </infCpl>
    </infAdic>
  </infNFe>
</NFe>
'''


def salvar(nome_arquivo: str, conteudo: str):
    caminho = os.path.join(PASTA_XMLS, nome_arquivo)
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(conteudo)


def criar_registro(numero_nf, serie, emitente, valor_nf, data_emissao, lote):
    paciente, cpf = random.choice(pacientes)
    return {
        "numero_nf": numero_nf,
        "serie": serie,
        "cnpj_emitente": emitente[0],
        "razao_social_emitente": emitente[1],
        "valor_nf": round(valor_nf, 2),
        "data_emissao": data_emissao.isoformat(),
        "chave": gerar_chave_fake(numero_nf),
        "lote": lote,
        "usuario_envio": random.choice(usuarios_envio),
        "paciente": paciente,
        "cpf_paciente": cpf,
        "prestador": random.choice(prestadores),
        "procedimento": random.choice(procedimentos),
        "data_atendimento": (data_emissao - timedelta(days=random.randint(0, 10))).date().isoformat(),
        "evento_clinico": random.choice(eventos_clinicos),
        "guia_atendimento": gerar_guia(),
    }


def main():
    limpar_pasta()

    base_data = datetime(2026, 1, 1, 10, 0, 0)

    registros = []

    # 180 normais
    for i in range(180):
        numero_nf = 1000 + i
        serie = 1
        emitente = random.choice(emitentes)
        valor_nf = random.uniform(150.0, 8500.0)
        data_emissao = base_data + timedelta(days=random.randint(0, 30), minutes=random.randint(0, 600))
        lote = random.choice(["lote_01", "lote_02", "lote_03", "lote_04"])

        registro = criar_registro(numero_nf, serie, emitente, valor_nf, data_emissao, lote)
        registros.append(registro)

    # salva os 180 normais
    for r in registros:
        salvar(f'NFe_{r["numero_nf"]}.xml', gerar_xml(r))

    # 20 duplicidades do mesmo lote / mesmo contexto
    for idx in range(20):
        base = registros[idx]
        dup = base.copy()
        salvar(f'NFe_DUP_MESMO_LOTE_{base["numero_nf"]}.xml', gerar_xml(dup))

    # 10 reapresentações em outro momento
    for idx in range(20, 30):
        base = registros[idx]
        reap = base.copy()
        nova_data = datetime.fromisoformat(base["data_emissao"]) + timedelta(days=12)
        reap["data_emissao"] = nova_data.isoformat()
        reap["lote"] = "lote_reapresentado"
        salvar(f'NFe_REAP_{base["numero_nf"]}.xml', gerar_xml(reap))

    # 10 comportamentais: mesmo paciente + prestador + procedimento + data_atendimento, mas notas diferentes
    for idx in range(30, 40):
        base = registros[idx]
        comp = base.copy()
        comp["numero_nf"] = 5000 + idx
        comp["chave"] = gerar_chave_fake(comp["numero_nf"])
        comp["usuario_envio"] = random.choice(usuarios_envio)
        comp["valor_nf"] = round(base["valor_nf"] + random.uniform(-15, 15), 2)
        comp["data_emissao"] = (datetime.fromisoformat(base["data_emissao"]) + timedelta(days=7)).isoformat()
        comp["lote"] = "lote_comportamental"
        # mantém paciente/prestador/procedimento/data_atendimento
        salvar(f'NFe_COMP_{comp["numero_nf"]}.xml', gerar_xml(comp))

    total = len([a for a in os.listdir(PASTA_XMLS) if a.endswith(".xml")])
    print(f"XMLs ricos gerados na pasta '{PASTA_XMLS}': {total}")


if __name__ == "__main__":
    main()
