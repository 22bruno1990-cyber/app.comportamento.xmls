import streamlit as st
import pandas as pd
import hashlib
import xml.etree.ElementTree as ET
from datetime import datetime

st.set_page_config(page_title="Plataforma Antifraude de Reembolsos", layout="wide")

st.markdown("""
<style>
.metric-card {
    padding: 16px;
    border-radius: 14px;
    text-align: center;
    font-weight: 700;
    margin-bottom: 8px;
}
.red {background-color:#2a0000;color:#ff6b6b;}
.orange {background-color:#2a1a00;color:#ffb347;}
yellow {background-color:#2a2a00;color:#ffe066;}
.green {background-color:#002a00;color:#5be37d;}
</style>
""", unsafe_allow_html=True)

st.title("🚨 Plataforma Antifraude de Reembolsos (NF-e)")
st.caption("Detecção técnica + comportamento suspeito + priorização automática")

uploaded_files = st.file_uploader(
    "Selecione os arquivos XML",
    type=["xml"],
    accept_multiple_files=True
)

NAMESPACE = {"nfe": "http://www.portalfiscal.inf.br/nfe"}


def gerar_hash(conteudo):
    return hashlib.sha256(conteudo).hexdigest()


def extrair_campos_inf_cpl(texto):
    campos = {
        "usuario_envio": "",
        "paciente": "",
        "cpf_paciente": "",
        "prestador": "",
        "procedimento": "",
        "data_atendimento": "",
        "evento_clinico": "",
        "guia_atendimento": "",
        "lote": "",
    }

    if not texto:
        return campos

    partes = texto.replace("\n", " ").split("|")
    for parte in partes:
        if "=" in parte:
            chave, valor = parte.split("=", 1)
            chave = chave.strip()
            valor = valor.strip()
            if chave in campos:
                campos[chave] = valor

    return campos


def ler_xml(conteudo):
    root = ET.fromstring(conteudo)

    def get(xpath):
        el = root.find(xpath, NAMESPACE)
        return el.text.strip() if el is not None and el.text else ""

    infnfe = root.find(".//nfe:infNFe", NAMESPACE)
    id_nfe = infnfe.attrib.get("Id", "") if infnfe is not None else ""

    inf_cpl = get(".//nfe:infAdic/nfe:infCpl")
    campos_extras = extrair_campos_inf_cpl(inf_cpl)

    dados = {
        "id_nfe": id_nfe,
        "numero_nf": get(".//nfe:nNF"),
        "serie": get(".//nfe:serie"),
        "data_emissao": get(".//nfe:dhEmi"),
        "cnpj_emitente": get(".//nfe:emit/nfe:CNPJ"),
        "razao_social_emitente": get(".//nfe:emit/nfe:xNome"),
        "cnpj_destinatario": get(".//nfe:dest/nfe:CNPJ"),
        "valor_nf": get(".//nfe:total/nfe:ICMSTot/nfe:vNF"),
        "inf_cpl": inf_cpl,
    }

    dados.update(campos_extras)
    return dados


def calcular_score_tecnico(row):
    score = 0
    motivos = []

    if row["dup_hash"]:
        if row["mesmo_lote_hash"]:
            score = 60
            motivos.append("Mesmo XML no mesmo lote")
        else:
            score = 100
            motivos.append("Mesmo XML em lote diferente")

    elif row["dup_id_nfe"] and row["dup_chave_negocio"]:
        score = 70
        motivos.append("Mesma NF reapresentada")

    elif row["dup_chave_negocio"]:
        score = 60
        motivos.append("Chave de negócio duplicada")

    elif row["dup_id_nfe"]:
        score = 40
        motivos.append("ID da NF repetido")

    else:
        score = 0
        motivos.append("Sem indícios técnicos")

    if score >= 90:
        nivel = "🔴 REAPRESENTAÇÃO"
    elif score >= 60:
        nivel = "🟠 DUPLICIDADE"
    elif score >= 40:
        nivel = "🟡 ALERTA"
    else:
        nivel = "🟢 NORMAL"

    return pd.Series([score, nivel, " | ".join(motivos)])


def calcular_score_comportamental(row):
    score = 0
    motivos = []

    if row["grupo_paciente_prestador_proc_data"] >= 2 and not row["dup_hash"]:
        score += 70
        motivos.append("Mesmo paciente + prestador + procedimento + data")

    if row["grupo_guia"] >= 2 and not row["dup_hash"]:
        score += 60
        motivos.append("Mesma guia reaproveitada")

    if row["grupo_usuario_evento"] >= 3:
        score += 20
        motivos.append("Usuário repetindo padrão semelhante")

    if row["grupo_cpf_data"] >= 3:
        score += 15
        motivos.append("Paciente concentrando eventos no dia")

    if row["grupo_prestador_data"] >= 5:
        score += 10
        motivos.append("Prestador com alta recorrência diária")

    if score > 100:
        score = 100

    if score >= 80:
        nivel = "🔴 COMPORTAMENTO SUSPEITO"
    elif score >= 40:
        nivel = "🟡 ALERTA COMPORTAMENTAL"
    else:
        nivel = "🟢 SEM ALERTA"

    if not motivos:
        motivos.append("Sem padrão comportamental suspeito")

    return pd.Series([score, nivel, " | ".join(motivos)])


def classificar_final(row):
    if row["nivel_risco_tecnico"] == "🔴 REAPRESENTAÇÃO":
        return "🔴 REAPRESENTAÇÃO"

    if row["nivel_risco_tecnico"] == "🟠 DUPLICIDADE":
        return "🟠 DUPLICIDADE"

    if row["risco_comportamental"] == "🔴 COMPORTAMENTO SUSPEITO":
        return "🔴 COMPORTAMENTO SUSPEITO"

    if row["risco_comportamental"] == "🟡 ALERTA COMPORTAMENTAL":
        return "🟡 ALERTA COMPORTAMENTAL"

    if row["nivel_risco_tecnico"] == "🟡 ALERTA":
        return "🟡 ALERTA"

    return "🟢 NORMAL"


def highlight_risco(row):
    classificacao = row["classificacao_final"]
    if classificacao == "🔴 REAPRESENTAÇÃO":
        return ["background-color:#330000"] * len(row)
    if classificacao == "🔴 COMPORTAMENTO SUSPEITO":
        return ["background-color:#2a0000"] * len(row)
    if classificacao == "🟠 DUPLICIDADE":
        return ["background-color:#2a1a00"] * len(row)
    if classificacao == "🟡 ALERTA COMPORTAMENTAL":
        return ["background-color:#2a2a00"] * len(row)
    return [""] * len(row)


if uploaded_files:
    dados = []

    for arquivo in uploaded_files:
        conteudo = arquivo.read()
        try:
            info = ler_xml(conteudo)
            info["arquivo"] = arquivo.name
            info["hash_arquivo"] = gerar_hash(conteudo)
            info["data_upload"] = datetime.now()
            dados.append(info)
        except Exception as e:
            st.warning(f"Falha ao ler {arquivo.name}: {e}")

    if dados:
        df = pd.DataFrame(dados)

        df["valor_nf_num"] = pd.to_numeric(df["valor_nf"], errors="coerce").fillna(0)
        df["data_upload"] = pd.to_datetime(df["data_upload"])
        df["data_emissao_dt"] = pd.to_datetime(df["data_emissao"], errors="coerce")
        df["data_atendimento_dt"] = pd.to_datetime(df["data_atendimento"], errors="coerce")

        df["dup_id_nfe"] = df.duplicated(subset=["id_nfe"], keep=False)
        df["dup_chave_negocio"] = df.duplicated(
            subset=["numero_nf", "serie", "cnpj_emitente", "valor_nf"],
            keep=False
        )
        df["dup_hash"] = df.duplicated(subset=["hash_arquivo"], keep=False)

        df["grupo_hash_lote"] = df.groupby(["hash_arquivo", "lote"])["arquivo"].transform("count")
        df["mesmo_lote_hash"] = (df["dup_hash"]) & (df["grupo_hash_lote"] >= 2)

        df[["score_tecnico", "nivel_risco_tecnico", "motivo_tecnico"]] = df.apply(
            calcular_score_tecnico, axis=1
        )

        df["grupo_paciente_prestador_proc_data"] = df.groupby(
            ["cpf_paciente", "prestador", "procedimento", "data_atendimento"]
        )["arquivo"].transform("count")

        df["grupo_guia"] = df.groupby(["guia_atendimento"])["arquivo"].transform("count")

        df["grupo_usuario_evento"] = df.groupby(
            ["usuario_envio", "prestador", "procedimento", "data_atendimento"]
        )["arquivo"].transform("count")

        df["grupo_cpf_data"] = df.groupby(
            ["cpf_paciente", "data_atendimento"]
        )["arquivo"].transform("count")

        df["grupo_prestador_data"] = df.groupby(
            ["prestador", "data_atendimento"]
        )["arquivo"].transform("count")

        df[["score_comportamental", "risco_comportamental", "motivo_comportamental"]] = df.apply(
            calcular_score_comportamental, axis=1
        )

        df["score_final"] = df[["score_tecnico", "score_comportamental"]].max(axis=1)
        df["classificacao_final"] = df.apply(classificar_final, axis=1)

        total = len(df)
        reapresentacao = (df["classificacao_final"] == "🔴 REAPRESENTAÇÃO").sum()
        duplicidade = (df["classificacao_final"] == "🟠 DUPLICIDADE").sum()
        comp_suspeito = (df["classificacao_final"] == "🔴 COMPORTAMENTO SUSPEITO").sum()
        alerta_comp = (df["classificacao_final"] == "🟡 ALERTA COMPORTAMENTAL").sum()
        normais = (df["classificacao_final"] == "🟢 NORMAL").sum()

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.markdown(f'<div class="metric-card">📊 Total<br>{total}</div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="metric-card red">🔴 Reapresentação<br>{reapresentacao}</div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="metric-card orange">🟠 Duplicidade<br>{duplicidade}</div>', unsafe_allow_html=True)
        c4.markdown(f'<div class="metric-card yellow">🟡 Comportamento<br>{comp_suspeito + alerta_comp}</div>', unsafe_allow_html=True)
        c5.markdown(f'<div class="metric-card green">🟢 Normais<br>{normais}</div>', unsafe_allow_html=True)

        st.subheader("🔥 Top ofensores")

        col1, col2, col3 = st.columns(3)
        top_usuario = df["usuario_envio"].value_counts().head(5)
        top_prestador = df["prestador"].value_counts().head(5)
        top_paciente = df["paciente"].value_counts().head(5)

        col1.markdown("### 👤 Usuários")
        col1.dataframe(top_usuario, use_container_width=True)

        col2.markdown("### 🏥 Prestadores")
        col2.dataframe(top_prestador, use_container_width=True)

        col3.markdown("### 🧑 Pacientes")
        col3.dataframe(top_paciente, use_container_width=True)

        st.subheader("🧠 Top 10 riscos")
        colunas_top = [
            "arquivo",
            "usuario_envio",
            "paciente",
            "prestador",
            "procedimento",
            "data_atendimento",
            "valor_nf",
            "score_tecnico",
            "score_comportamental",
            "score_final",
            "classificacao_final",
            "motivo_tecnico",
            "motivo_comportamental",
        ]
        st.dataframe(
            df[colunas_top].sort_values(by="score_final", ascending=False).head(10),
            use_container_width=True
        )

        st.subheader("Resultados completos")
        colunas_exibicao = [
            "arquivo",
            "numero_nf",
            "serie",
            "cnpj_emitente",
            "razao_social_emitente",
            "usuario_envio",
            "paciente",
            "cpf_paciente",
            "prestador",
            "procedimento",
            "data_atendimento",
            "evento_clinico",
            "guia_atendimento",
            "lote",
            "valor_nf",
            "score_tecnico",
            "nivel_risco_tecnico",
            "motivo_tecnico",
            "score_comportamental",
            "risco_comportamental",
            "motivo_comportamental",
            "score_final",
            "classificacao_final",
            "grupo_paciente_prestador_proc_data",
            "grupo_guia",
            "grupo_usuario_evento",
            "id_nfe",
        ]

        df_exibicao = df[colunas_exibicao].sort_values(by="score_final", ascending=False)
        st.dataframe(df_exibicao.style.apply(highlight_risco, axis=1), use_container_width=True)

        csv = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "Baixar CSV",
            data=csv,
            file_name="resultado_antifraude_xml_rico.csv",
            mime="text/csv",
            key="download_xml_rico"
        )
    else:
        st.warning("Nenhum XML válido")
else:
    st.info("Faça upload dos XMLs")
