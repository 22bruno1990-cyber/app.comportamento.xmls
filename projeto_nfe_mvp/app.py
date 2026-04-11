from datetime import datetime
import hashlib
from pathlib import Path
import sqlite3
import xml.etree.ElementTree as ET

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="PSL | Antifraude NF-e",
    page_icon="shield",
    layout="wide",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;700;800&display=swap');

    html, body, [class*="css"]  {
        font-family: 'Manrope', sans-serif;
    }

    .stApp {
        background:
            radial-gradient(circle at top left, rgba(11, 94, 215, 0.12), transparent 28%),
            radial-gradient(circle at top right, rgba(255, 122, 69, 0.12), transparent 24%),
            linear-gradient(180deg, #f6f8fc 0%, #eef3fb 100%);
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    .hero {
        background: linear-gradient(135deg, #07111f 0%, #0b2d56 55%, #114581 100%);
        padding: 28px 30px;
        border-radius: 26px;
        color: white;
        box-shadow: 0 18px 50px rgba(7, 17, 31, 0.18);
        margin-bottom: 20px;
    }

    .hero-kicker {
        display: inline-block;
        font-size: 0.8rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #9fd1ff;
        margin-bottom: 10px;
    }

    .hero h1 {
        font-size: 3rem;
        line-height: 1.05;
        margin: 0 0 12px 0;
        font-weight: 800;
    }

    .hero p {
        font-size: 1.05rem;
        line-height: 1.6;
        color: #dbe8fb;
        margin-bottom: 0;
        max-width: 860px;
    }

    .pill-row {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        margin-top: 18px;
    }

    .pill {
        background: rgba(255,255,255,0.12);
        border: 1px solid rgba(255,255,255,0.14);
        border-radius: 999px;
        padding: 8px 14px;
        font-size: 0.9rem;
        font-weight: 700;
    }

    .glass-card {
        background: rgba(255, 255, 255, 0.78);
        border: 1px solid rgba(12, 36, 68, 0.08);
        border-radius: 22px;
        padding: 20px 22px;
        box-shadow: 0 16px 45px rgba(28, 48, 74, 0.08);
        backdrop-filter: blur(4px);
        height: 100%;
    }

    .section-title {
        font-size: 1.15rem;
        font-weight: 800;
        color: #10233c;
        margin-bottom: 6px;
    }

    .section-copy {
        color: #526273;
        font-size: 0.95rem;
        line-height: 1.55;
    }

    .soft-heading {
        color: #d7e0ee;
        font-size: 1.05rem;
        font-weight: 800;
        letter-spacing: -0.01em;
        margin: 10px 0 12px 0;
    }

    .metric-card {
        border-radius: 22px;
        padding: 20px;
        color: white;
        min-height: 168px;
        box-shadow: 0 14px 30px rgba(20, 32, 56, 0.12);
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        margin-bottom: 14px;
    }

    .metric-card .label {
        font-size: 0.74rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        opacity: 0.9;
        font-weight: 700;
        line-height: 1.25;
        min-height: 38px;
        word-break: normal;
        overflow-wrap: normal;
    }

    .metric-card .value {
        font-size: 2.1rem;
        margin-top: 12px;
        font-weight: 800;
        line-height: 1;
    }

    .metric-card .sub {
        font-size: 0.86rem;
        margin-top: 14px;
        opacity: 0.92;
        line-height: 1.35;
        min-height: 42px;
    }

    .blue { background: linear-gradient(135deg, #173761 0%, #275ea7 100%); }
    .red { background: linear-gradient(135deg, #102947 0%, #1a4778 100%); }
    .orange { background: linear-gradient(135deg, #22466f 0%, #3e78b8 100%); }
    .gold { background: linear-gradient(135deg, #35567f 0%, #5d89bf 100%); }
    .green { background: linear-gradient(135deg, #496b96 0%, #7ca4d5 100%); }

    .insight-box {
        border-left: 5px solid #1e5ea8;
        background: white;
        border-radius: 18px;
        padding: 18px 18px 18px 20px;
        box-shadow: 0 10px 28px rgba(28, 48, 74, 0.08);
        margin-bottom: 12px;
    }

    .insight-box strong {
        color: #0d2340;
    }

    .panel-card {
        background: rgba(255, 255, 255, 0.92);
        border: 1px solid rgba(12, 36, 68, 0.08);
        border-radius: 22px;
        padding: 20px 22px;
        box-shadow: 0 10px 28px rgba(28, 48, 74, 0.08);
        height: 100%;
        margin-top: 10px;
    }

    .summary-title,
    .chart-title {
        color: #152b4c;
        font-size: 1rem;
        font-weight: 800;
        margin-bottom: 10px;
    }

    .summary-copy {
        color: #4f6176;
        font-size: 0.96rem;
        line-height: 1.6;
    }

    .summary-copy strong {
        color: #152b4c;
    }

    .chart-wrap {
        margin-top: 6px;
    }

    .risk-strip {
        background: rgba(255, 255, 255, 0.92);
        border-radius: 22px;
        padding: 18px 22px;
        box-shadow: 0 10px 28px rgba(28, 48, 74, 0.08);
        margin-bottom: 14px;
        display: grid;
        grid-template-columns: minmax(180px, 240px) minmax(180px, 220px) 1fr;
        align-items: center;
        gap: 18px;
    }

    .risk-strip-title {
        font-size: 0.95rem;
        font-weight: 800;
        color: #0d2340;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }

    .risk-strip-value {
        font-size: 1.05rem;
        font-weight: 800;
        color: #142b4d;
        white-space: nowrap;
    }

    .risk-strip-copy {
        font-size: 0.95rem;
        color: #506176;
        line-height: 1.45;
    }

    @media (max-width: 900px) {
        .risk-strip {
            grid-template-columns: 1fr;
        }
    }

    .mini-tag {
        display: inline-block;
        margin-right: 8px;
        margin-bottom: 8px;
        padding: 6px 10px;
        border-radius: 999px;
        background: #e8f1ff;
        color: #18457b;
        font-size: 0.82rem;
        font-weight: 700;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

NAMESPACE = {"nfe": "http://www.portalfiscal.inf.br/nfe"}
BASE_DIR = Path(__file__).resolve().parent
DEMO_DIR = BASE_DIR / "xmls_ricos"
DB_DIR = BASE_DIR / "data"
DB_PATH = DB_DIR / "historico_nfe.db"


def gerar_hash(conteudo):
    return hashlib.sha256(conteudo).hexdigest()


def get_db_connection():
    DB_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def inicializar_banco():
    with get_db_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS nfe_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                arquivo TEXT,
                hash_arquivo TEXT,
                id_nfe TEXT,
                numero_nf TEXT,
                serie TEXT,
                data_emissao TEXT,
                cnpj_emitente TEXT,
                razao_social_emitente TEXT,
                cnpj_destinatario TEXT,
                valor_nf TEXT,
                valor_nf_num REAL,
                usuario_envio TEXT,
                paciente TEXT,
                cpf_paciente TEXT,
                prestador TEXT,
                procedimento TEXT,
                data_atendimento TEXT,
                evento_clinico TEXT,
                guia_atendimento TEXT,
                lote TEXT,
                score_final REAL,
                classificacao_final TEXT,
                origem_upload TEXT,
                analisado_em TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_docs_hash ON nfe_documents(hash_arquivo)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_docs_id_nfe ON nfe_documents(id_nfe)")
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_docs_business
            ON nfe_documents(numero_nf, serie, cnpj_emitente, valor_nf)
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_docs_behavior
            ON nfe_documents(cpf_paciente, prestador, procedimento, data_atendimento)
            """
        )
        conn.commit()


def load_history_stats():
    inicializar_banco()
    with get_db_connection() as conn:
        row = conn.execute(
            """
            SELECT
                COUNT(*) AS total_documentos,
                COUNT(DISTINCT hash_arquivo) AS hashes_unicos,
                COUNT(DISTINCT id_nfe) AS ids_unicos,
                MAX(analisado_em) AS ultima_analise
            FROM nfe_documents
            """
        ).fetchone()
    return {
        "total_documentos": row["total_documentos"] or 0,
        "hashes_unicos": row["hashes_unicos"] or 0,
        "ids_unicos": row["ids_unicos"] or 0,
        "ultima_analise": row["ultima_analise"] or "Sem histórico ainda",
    }


def query_scalar(conn, query, params):
    row = conn.execute(query, params).fetchone()
    return row[0] if row and row[0] is not None else 0


def enrich_historico(df):
    inicializar_banco()
    historico_cols = [
        "hist_hash_count",
        "hist_id_count",
        "hist_business_count",
        "hist_behavior_count",
        "ja_visto_historico",
        "motivo_historico",
    ]

    if df.empty:
        for coluna in historico_cols:
            df[coluna] = []
        return df

    hist_hash_count = []
    hist_id_count = []
    hist_business_count = []
    hist_behavior_count = []
    ja_visto = []
    motivos = []

    with get_db_connection() as conn:
        for _, row in df.iterrows():
            hash_count = query_scalar(
                conn,
                "SELECT COUNT(*) FROM nfe_documents WHERE hash_arquivo = ? AND hash_arquivo <> ''",
                (row["hash_arquivo"],),
            )
            id_count = query_scalar(
                conn,
                "SELECT COUNT(*) FROM nfe_documents WHERE id_nfe = ? AND id_nfe <> ''",
                (row["id_nfe"],),
            )
            business_count = query_scalar(
                conn,
                """
                SELECT COUNT(*)
                FROM nfe_documents
                WHERE numero_nf = ?
                  AND serie = ?
                  AND cnpj_emitente = ?
                  AND valor_nf = ?
                  AND numero_nf <> ''
                  AND cnpj_emitente <> ''
                """,
                (row["numero_nf"], row["serie"], row["cnpj_emitente"], row["valor_nf"]),
            )
            behavior_count = query_scalar(
                conn,
                """
                SELECT COUNT(*)
                FROM nfe_documents
                WHERE cpf_paciente = ?
                  AND prestador = ?
                  AND procedimento = ?
                  AND data_atendimento = ?
                  AND cpf_paciente <> ''
                  AND prestador <> ''
                  AND procedimento <> ''
                  AND data_atendimento <> ''
                """,
                (
                    row["cpf_paciente"],
                    row["prestador"],
                    row["procedimento"],
                    row["data_atendimento"],
                ),
            )

            row_motivos = []
            if hash_count:
                row_motivos.append(f"XML já visto {hash_count}x no histórico")
            if id_count:
                row_motivos.append(f"ID NFe já visto {id_count}x")
            if business_count:
                row_motivos.append(f"Chave de negócio já vista {business_count}x")
            if behavior_count:
                row_motivos.append(f"Padrão paciente/prestador já visto {behavior_count}x")

            hist_hash_count.append(int(hash_count))
            hist_id_count.append(int(id_count))
            hist_business_count.append(int(business_count))
            hist_behavior_count.append(int(behavior_count))
            ja_visto.append(bool(hash_count or id_count or business_count or behavior_count))
            motivos.append(" | ".join(row_motivos) if row_motivos else "Novo no histórico")

    df["hist_hash_count"] = hist_hash_count
    df["hist_id_count"] = hist_id_count
    df["hist_business_count"] = hist_business_count
    df["hist_behavior_count"] = hist_behavior_count
    df["ja_visto_historico"] = ja_visto
    df["motivo_historico"] = motivos
    return df


def salvar_lote_no_historico(df, origem_upload):
    inicializar_banco()
    colunas = [
        "arquivo",
        "hash_arquivo",
        "id_nfe",
        "numero_nf",
        "serie",
        "data_emissao",
        "cnpj_emitente",
        "razao_social_emitente",
        "cnpj_destinatario",
        "valor_nf",
        "valor_nf_num",
        "usuario_envio",
        "paciente",
        "cpf_paciente",
        "prestador",
        "procedimento",
        "data_atendimento",
        "evento_clinico",
        "guia_atendimento",
        "lote",
        "score_final",
        "classificacao_final",
    ]
    registros = df[colunas].fillna("").to_dict(orient="records")

    with get_db_connection() as conn:
        conn.executemany(
            """
            INSERT INTO nfe_documents (
                arquivo, hash_arquivo, id_nfe, numero_nf, serie, data_emissao, cnpj_emitente,
                razao_social_emitente, cnpj_destinatario, valor_nf, valor_nf_num, usuario_envio,
                paciente, cpf_paciente, prestador, procedimento, data_atendimento, evento_clinico,
                guia_atendimento, lote, score_final, classificacao_final, origem_upload
            )
            VALUES (
                :arquivo, :hash_arquivo, :id_nfe, :numero_nf, :serie, :data_emissao, :cnpj_emitente,
                :razao_social_emitente, :cnpj_destinatario, :valor_nf, :valor_nf_num, :usuario_envio,
                :paciente, :cpf_paciente, :prestador, :procedimento, :data_atendimento, :evento_clinico,
                :guia_atendimento, :lote, :score_final, :classificacao_final, :origem_upload
            )
            """,
            [{**registro, "origem_upload": origem_upload} for registro in registros],
        )
        conn.commit()
    return len(registros)


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
        if "=" not in parte:
            continue
        chave, valor = parte.split("=", 1)
        chave = chave.strip()
        valor = valor.strip()
        if chave in campos:
            campos[chave] = valor

    return campos


def ler_xml(conteudo):
    root = ET.fromstring(conteudo)

    def get(xpath):
        elemento = root.find(xpath, NAMESPACE)
        return elemento.text.strip() if elemento is not None and elemento.text else ""

    inf_nfe = root.find(".//nfe:infNFe", NAMESPACE)
    id_nfe = inf_nfe.attrib.get("Id", "") if inf_nfe is not None else ""
    inf_cpl = get(".//nfe:infAdic/nfe:infCpl")

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
    dados.update(extrair_campos_inf_cpl(inf_cpl))
    return dados


def calcular_score_tecnico(row):
    score = 0
    motivos = []

    if row["hist_hash_count"] > 0:
        score = 100
        motivos.append("XML idêntico já apareceu no histórico")
    elif row["dup_hash"]:
        if row["mesmo_lote_hash"]:
            score = 60
            motivos.append("Mesmo XML reapresentado no mesmo lote")
        else:
            score = 100
            motivos.append("Mesmo XML reapresentado em lote diferente")
    elif row["hist_id_count"] > 0 and row["hist_business_count"] > 0:
        score = 85
        motivos.append("Mesma NF já apareceu no histórico")
    elif row["hist_business_count"] > 0:
        score = 75
        motivos.append("Chave de negócio já apareceu no histórico")
    elif row["hist_id_count"] > 0:
        score = 55
        motivos.append("ID da NF já apareceu no histórico")
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
        motivos.append("Sem indícios técnicos")

    if score >= 90:
        nivel = "REAPRESENTACAO"
    elif score >= 60:
        nivel = "DUPLICIDADE"
    elif score >= 40:
        nivel = "ALERTA"
    else:
        nivel = "NORMAL"

    return pd.Series([score, nivel, " | ".join(motivos)])


def calcular_score_comportamental(row):
    score = 0
    motivos = []

    if row["hist_behavior_count"] >= 1 and not row["dup_hash"]:
        score += 35
        motivos.append("Padrão semelhante já apareceu no histórico")

    if row["grupo_paciente_prestador_proc_data"] >= 2 and not row["dup_hash"]:
        score += 70
        motivos.append("Mesmo paciente + prestador + procedimento + data")

    if row["grupo_guia"] >= 2 and not row["dup_hash"] and row["guia_atendimento"]:
        score += 60
        motivos.append("Mesma guia reaproveitada")

    if row["grupo_usuario_evento"] >= 3 and row["usuario_envio"]:
        score += 20
        motivos.append("Usuário repetindo padrão semelhante")

    if row["grupo_cpf_data"] >= 3 and row["cpf_paciente"]:
        score += 15
        motivos.append("Paciente concentrando eventos no dia")

    if row["grupo_prestador_data"] >= 5 and row["prestador"]:
        score += 10
        motivos.append("Prestador com alta recorrencia diaria")

    score = min(score, 100)

    if score >= 80:
        nivel = "COMPORTAMENTO SUSPEITO"
    elif score >= 40:
        nivel = "ALERTA COMPORTAMENTAL"
    else:
        nivel = "SEM ALERTA"

    if not motivos:
        motivos.append("Sem padrão comportamental suspeito")

    return pd.Series([score, nivel, " | ".join(motivos)])


def classificar_final(row):
    if row["nivel_risco_tecnico"] == "REAPRESENTACAO":
        return "REAPRESENTACAO"
    if row["nivel_risco_tecnico"] == "DUPLICIDADE":
        return "DUPLICIDADE"
    if row["risco_comportamental"] == "COMPORTAMENTO SUSPEITO":
        return "COMPORTAMENTO SUSPEITO"
    if row["risco_comportamental"] == "ALERTA COMPORTAMENTAL":
        return "ALERTA COMPORTAMENTAL"
    if row["nivel_risco_tecnico"] == "ALERTA":
        return "ALERTA"
    return "NORMAL"


def highlight_risco(row):
    classificacao = row["classificacao_final"]
    if classificacao == "REAPRESENTACAO":
        return ["background-color:#4e1212;color:#fff7f7"] * len(row)
    if classificacao == "COMPORTAMENTO SUSPEITO":
        return ["background-color:#632323;color:#fff7f7"] * len(row)
    if classificacao == "DUPLICIDADE":
        return ["background-color:#6a430e;color:#fff9f2"] * len(row)
    if classificacao == "ALERTA COMPORTAMENTAL":
        return ["background-color:#736115;color:#fffdf2"] * len(row)
    return [""] * len(row)


def carregar_demo(limit=24):
    todos = {caminho.name: caminho for caminho in DEMO_DIR.glob("*.xml")}
    nomes_prioritarios = [
        "NFe_REAP_1020.xml",
        "NFe_REAP_1021.xml",
        "NFe_REAP_1022.xml",
        "NFe_REAP_1023.xml",
        "NFe_DUP_MESMO_LOTE_1000.xml",
        "NFe_DUP_MESMO_LOTE_1001.xml",
        "NFe_DUP_MESMO_LOTE_1002.xml",
        "NFe_DUP_MESMO_LOTE_1003.xml",
        "NFe_COMP_5030.xml",
        "NFe_COMP_5031.xml",
        "NFe_COMP_5032.xml",
        "NFe_COMP_5033.xml",
        "NFe_1000.xml",
        "NFe_1001.xml",
        "NFe_1002.xml",
        "NFe_1003.xml",
    ]
    arquivos = [todos[nome] for nome in nomes_prioritarios if nome in todos]
    if len(arquivos) < limit:
        ja_usados = {arquivo.name for arquivo in arquivos}
        complementares = [caminho for caminho in sorted(todos.values()) if caminho.name not in ja_usados]
        arquivos.extend(complementares[: max(0, limit - len(arquivos))])

    demo_files = []
    for caminho in arquivos[:limit]:
        demo_files.append(
            {
                "name": caminho.name,
                "content": caminho.read_bytes(),
            }
        )
    return demo_files


def processar_arquivos(arquivos):
    inicializar_banco()
    dados = []

    for arquivo in arquivos:
        if isinstance(arquivo, dict):
            nome = arquivo["name"]
            conteudo = arquivo["content"]
        else:
            nome = arquivo.name
            conteudo = arquivo.read()

        try:
            info = ler_xml(conteudo)
            info["arquivo"] = nome
            info["hash_arquivo"] = gerar_hash(conteudo)
            info["data_upload"] = datetime.now()
            dados.append(info)
        except Exception:
            continue

    if not dados:
        return pd.DataFrame()

    df = pd.DataFrame(dados)

    df["valor_nf_num"] = pd.to_numeric(df["valor_nf"], errors="coerce").fillna(0)
    df["data_upload"] = pd.to_datetime(df["data_upload"])
    df["data_emissao_dt"] = pd.to_datetime(df["data_emissao"], errors="coerce")
    df["data_atendimento_dt"] = pd.to_datetime(df["data_atendimento"], errors="coerce")

    df["dup_id_nfe"] = df.duplicated(subset=["id_nfe"], keep=False) & (df["id_nfe"] != "")
    df["dup_chave_negocio"] = df.duplicated(
        subset=["numero_nf", "serie", "cnpj_emitente", "valor_nf"],
        keep=False,
    ) & (df["numero_nf"] != "") & (df["cnpj_emitente"] != "")
    df["dup_hash"] = df.duplicated(subset=["hash_arquivo"], keep=False) & (df["hash_arquivo"] != "")
    df = enrich_historico(df)

    df["grupo_hash_lote"] = df.groupby(["hash_arquivo", "lote"])["arquivo"].transform("count")
    df["mesmo_lote_hash"] = df["dup_hash"] & (df["grupo_hash_lote"] >= 2)

    df[["score_tecnico", "nivel_risco_tecnico", "motivo_tecnico"]] = df.apply(
        calcular_score_tecnico,
        axis=1,
    )

    df["grupo_paciente_prestador_proc_data"] = df.groupby(
        ["cpf_paciente", "prestador", "procedimento", "data_atendimento"]
    )["arquivo"].transform("count")
    df["grupo_guia"] = df.groupby(["guia_atendimento"])["arquivo"].transform("count")
    df["grupo_usuario_evento"] = df.groupby(
        ["usuario_envio", "prestador", "procedimento", "data_atendimento"]
    )["arquivo"].transform("count")
    df["grupo_cpf_data"] = df.groupby(["cpf_paciente", "data_atendimento"])["arquivo"].transform("count")
    df["grupo_prestador_data"] = df.groupby(["prestador", "data_atendimento"])["arquivo"].transform("count")

    df[["score_comportamental", "risco_comportamental", "motivo_comportamental"]] = df.apply(
        calcular_score_comportamental,
        axis=1,
    )

    df["score_final"] = df[["score_tecnico", "score_comportamental"]].max(axis=1)
    df["classificacao_final"] = df.apply(classificar_final, axis=1)
    return df.sort_values(by="score_final", ascending=False).reset_index(drop=True)


def resumo_executivo(df):
    total = len(df)
    reapresentacao = int((df["classificacao_final"] == "REAPRESENTACAO").sum())
    duplicidade = int((df["classificacao_final"] == "DUPLICIDADE").sum())
    comportamento = int(
        df["classificacao_final"].isin(["COMPORTAMENTO SUSPEITO", "ALERTA COMPORTAMENTAL"]).sum()
    )
    normais = int((df["classificacao_final"] == "NORMAL").sum())

    return {
        "total": total,
        "reapresentacao": reapresentacao,
        "duplicidade": duplicidade,
        "comportamento": comportamento,
        "normais": normais,
        "vistos_historico": int(df["ja_visto_historico"].sum()),
        "potencial_revisao": reapresentacao + duplicidade + comportamento,
        "valor_em_alerta": float(df.loc[df["score_final"] >= 60, "valor_nf_num"].sum()),
        "valor_fraude_forte": float(df.loc[df["classificacao_final"] == "REAPRESENTACAO", "valor_nf_num"].sum()),
        "valor_duplicidade": float(df.loc[df["classificacao_final"] == "DUPLICIDADE", "valor_nf_num"].sum()),
        "valor_suspeito": float(
            df.loc[df["classificacao_final"].isin(["COMPORTAMENTO SUSPEITO", "ALERTA COMPORTAMENTAL"]), "valor_nf_num"].sum()
        ),
    }


def formatar_brl(valor):
    texto = f"{valor:,.2f}"
    texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def categoria_trilha_risco(classificacao):
    if classificacao == "REAPRESENTACAO":
        return "FRAUDE FORTE"
    if classificacao == "DUPLICIDADE":
        return "DUPLICIDADE"
    if classificacao in {"COMPORTAMENTO SUSPEITO", "ALERTA COMPORTAMENTAL", "ALERTA"}:
        return "SUSPEITO"
    return "NORMAL"


def resumo_categoria(df, categoria):
    base = df[df["categoria_trilha"] == categoria]
    return {
        "quantidade": int(len(base)),
        "valor": float(base["valor_nf_num"].sum()),
        "top": base.head(5),
    }


def render_metric(coluna, classe, label, value, sub):
    coluna.markdown(
        f"""
        <div class="metric-card {classe}">
            <div class="label">{label}</div>
            <div class="value">{value}</div>
            <div class="sub">{sub}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_hero():
    st.markdown(
        """
        <div class="hero">
            <div class="hero-kicker">PSL | Revenue Protection</div>
            <h1>Revele duplicidades e sinais de reapresentação antes do reembolso sair.</h1>
            <p>
                Esta demo transforma XMLs de NF-e em uma fila priorizada de risco. Em minutos,
                o time identifica reapresentações, duplicidades técnicas e padrões comportamentais
                suspeitos para auditoria, glosa e prevenção de perdas.
            </p>
            <div class="pill-row">
                <div class="pill">Upload em lote</div>
                <div class="pill">Priorização automática</div>
                <div class="pill">CSV para auditoria</div>
                <div class="pill">Demo pronta para comprador</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_pitch():
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            """
            <div class="glass-card">
                <div class="section-title">Problema</div>
                <div class="section-copy">
                    Reembolsos podem ser aprovados com documentos reapresentados ou com padrões
                    repetitivos que passam despercebidos em análise manual.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            """
            <div class="glass-card">
                <div class="section-title">Solução</div>
                <div class="section-copy">
                    O PSL lê XMLs, cruza sinais técnicos e comportamentais, consulta o histórico e prioriza os casos
                    com maior chance de perda financeira.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            """
            <div class="glass-card">
                <div class="section-title">Valor para comprador</div>
                <div class="section-copy">
                    Menos revisão cega, mais foco no que merece auditoria. O resultado sai em
                    formato operacional, pronto para investigação, memória histórica ou integração.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_empty_state():
    st.markdown('<div class="soft-heading">Como demonstrar em 30 segundos</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="glass-card">
            <span class="mini-tag">1. Clique em "Carregar demo guiada"</span>
            <span class="mini-tag">2. Veja a fila de risco pronta</span>
            <span class="mini-tag">3. Abra o Top 10 riscos</span>
            <span class="mini-tag">4. Exporte o CSV</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.info("Você pode subir XMLs reais ou usar a demo guiada para mostrar valor imediatamente.")


def render_results(df, origem):
    resumo = resumo_executivo(df)
    df = df.copy()
    df["categoria_trilha"] = df["classificacao_final"].apply(categoria_trilha_risco)

    st.markdown(f"### Painel executivo")
    st.caption(f"Fonte analisada: {origem}")

    c1, c2, c3 = st.columns(3)
    render_metric(c1, "blue", "XMLs analisados", resumo["total"], "volume processado")
    render_metric(c2, "red", "Reapresentação", resumo["reapresentacao"], "forte indício técnico")
    render_metric(c3, "orange", "Duplicidade", resumo["duplicidade"], "casos técnicos relevantes")

    c4, c5, c6 = st.columns(3)
    render_metric(c4, "gold", "Comportamental", resumo["comportamento"], "padrões suspeitos")
    render_metric(c5, "blue", "Já vistos", resumo["vistos_historico"], "matches no histórico")
    render_metric(c6, "green", "Normais", resumo["normais"], "sem alerta relevante")

    a1, a2 = st.columns(2)
    with a1:
        st.markdown(
            f"""
            <div class="panel-card">
                <div class="summary-title">Resumo para decisor</div>
                <div class="summary-copy">
                    <strong>{resumo["potencial_revisao"]}</strong> de <strong>{resumo["total"]}</strong> documentos foram
                    priorizados para revisão, com <strong>{formatar_brl(resumo["valor_em_alerta"])}</strong> em valor
                    associado a alertas de score 60+. O histórico já reconheceu
                    <strong>{resumo["vistos_historico"]}</strong> documento(s) com vínculo anterior.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with a2:
        top_classificacoes = df["classificacao_final"].value_counts().head(4)
        max_valor = max(int(top_classificacoes.max()), 1) if not top_classificacoes.empty else 1
        st.markdown(
            """
            <div class="panel-card">
                <div class="chart-title">Distribuição de alertas</div>
                <div class="chart-wrap"></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        for categoria, quantidade in top_classificacoes.items():
            label_col, progress_col, value_col = st.columns([1.2, 4, 0.5])
            label_col.markdown(f"**{categoria}**")
            progress_col.progress(int((int(quantidade) / max_valor) * 100))
            value_col.markdown(f"**{int(quantidade)}**")

    r1, r2, r3 = st.columns(3)
    fraude = resumo_categoria(df, "FRAUDE FORTE")
    suspeito = resumo_categoria(df, "SUSPEITO")
    duplicado = resumo_categoria(df, "DUPLICIDADE")
    render_metric(r1, "red", "Valor evitável | fraude", formatar_brl(fraude["valor"]), f'{fraude["quantidade"]} caso(s) críticos')
    render_metric(r2, "gold", "Valor em suspeita", formatar_brl(suspeito["valor"]), f'{suspeito["quantidade"]} caso(s) suspeitos')
    render_metric(r3, "orange", "Valor em duplicidade", formatar_brl(duplicado["valor"]), f'{duplicado["quantidade"]} caso(s) duplicados')

    t1, t2, t3 = st.columns(3)
    with t1:
        st.markdown("#### Usuários mais recorrentes")
        st.dataframe(df["usuario_envio"].replace("", "Não informado").value_counts().head(5), use_container_width=True)
    with t2:
        st.markdown("#### Prestadores mais expostos")
        st.dataframe(df["prestador"].replace("", "Não informado").value_counts().head(5), use_container_width=True)
    with t3:
        st.markdown("#### Pacientes mais recorrentes")
        st.dataframe(df["paciente"].replace("", "Não informado").value_counts().head(5), use_container_width=True)

    st.markdown("### Trilha de risco")
    st.caption("Separação executiva dos casos para demonstrar fraude forte, suspeita e duplicidade com valor potencial evitado.")

    trilhas = [
        ("FRAUDE FORTE", "red", "Fraudes fortes com maior potencial de bloqueio imediato"),
        ("SUSPEITO", "gold", "Casos suspeitos para revisão especializada"),
        ("DUPLICIDADE", "orange", "Duplicidades técnicas e reapresentações relevantes"),
    ]
    colunas_trilha = [
        "arquivo",
        "paciente",
        "prestador",
        "valor_nf",
        "score_final",
        "classificacao_final",
        "motivo_historico",
        "motivo_tecnico",
        "motivo_comportamental",
    ]
    for categoria, classe, descricao in trilhas:
        dados_categoria = df[df["categoria_trilha"] == categoria].head(5)
        valor_categoria = float(df.loc[df["categoria_trilha"] == categoria, "valor_nf_num"].sum())
        st.markdown(
            f"""
            <div class="risk-strip" style="border-left:6px solid {'#1a4778' if classe == 'red' else '#5d89bf' if classe == 'gold' else '#3e78b8'};">
                <div class="risk-strip-title">{categoria}</div>
                <div class="risk-strip-value">{len(dados_categoria)} caso(s) · {formatar_brl(valor_categoria)}</div>
                <div class="risk-strip-copy">{descricao}.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if not dados_categoria.empty:
            st.dataframe(dados_categoria[colunas_trilha], use_container_width=True)

    st.markdown("### Casos priorizados")
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
        "categoria_trilha",
        "motivo_historico",
        "motivo_tecnico",
        "motivo_comportamental",
    ]
    st.dataframe(df[colunas_top].head(10), use_container_width=True)

    st.markdown("### Base completa para auditoria")
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
        "ja_visto_historico",
        "motivo_historico",
        "hist_hash_count",
        "hist_id_count",
        "hist_business_count",
        "hist_behavior_count",
        "grupo_paciente_prestador_proc_data",
        "grupo_guia",
        "grupo_usuario_evento",
        "id_nfe",
    ]
    st.dataframe(
        df[colunas_exibicao].style.apply(highlight_risco, axis=1),
        use_container_width=True,
    )

    csv = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "Baixar relatorio CSV",
        data=csv,
        file_name="resultado_antifraude_nfe.csv",
        mime="text/csv",
    )


render_hero()
render_pitch()

with st.sidebar:
    historico = load_history_stats()
    st.markdown("## Modo de demonstração")
    usar_demo = st.button("Carregar demo guiada", use_container_width=True)
    st.caption("A demo usa XMLs de exemplo já publicados no repositório.")
    st.markdown("---")
    st.markdown("## Memória do produto")
    st.markdown(
        f"""
        - documentos salvos: **{historico["total_documentos"]}**
        - hashes únicos: **{historico["hashes_unicos"]}**
        - IDs únicos: **{historico["ids_unicos"]}**
        - última ingestão: **{historico["ultima_analise"]}**
        """
    )

uploaded_files = st.file_uploader(
    "Suba XMLs reais ou de teste",
    type=["xml"],
    accept_multiple_files=True,
    help="Você pode usar seus XMLs ou acionar a demo guiada no menu lateral.",
)

origem = None
df = pd.DataFrame()

if usar_demo:
    df = processar_arquivos(carregar_demo())
    origem = "Demo guiada com XMLs de exemplo"
elif uploaded_files:
    df = processar_arquivos(uploaded_files)
    origem = f"Upload manual de {len(uploaded_files)} arquivo(s)"

if not df.empty:
    render_results(df, origem)
    if st.button("Registrar este lote no histórico", use_container_width=True):
        salvos = salvar_lote_no_historico(df, origem)
        st.success(f"{salvos} documento(s) foram gravados no histórico antifraude.")
else:
    render_empty_state()
