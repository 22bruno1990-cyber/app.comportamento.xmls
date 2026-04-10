from datetime import datetime
import hashlib
from pathlib import Path
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

    .metric-card {
        border-radius: 22px;
        padding: 20px;
        color: white;
        min-height: 130px;
        box-shadow: 0 14px 30px rgba(20, 32, 56, 0.12);
    }

    .metric-card .label {
        font-size: 0.82rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        opacity: 0.9;
        font-weight: 700;
    }

    .metric-card .value {
        font-size: 2.1rem;
        margin-top: 10px;
        font-weight: 800;
        line-height: 1;
    }

    .metric-card .sub {
        font-size: 0.92rem;
        margin-top: 10px;
        opacity: 0.92;
    }

    .blue { background: linear-gradient(135deg, #163660 0%, #1e5ea8 100%); }
    .red { background: linear-gradient(135deg, #5a1212 0%, #b02a2a 100%); }
    .orange { background: linear-gradient(135deg, #6b3a11 0%, #d97822 100%); }
    .gold { background: linear-gradient(135deg, #5b4a13 0%, #d0a11f 100%); }
    .green { background: linear-gradient(135deg, #0f5132 0%, #198754 100%); }

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

    if row["dup_hash"]:
        if row["mesmo_lote_hash"]:
            score = 60
            motivos.append("Mesmo XML reapresentado no mesmo lote")
        else:
            score = 100
            motivos.append("Mesmo XML reapresentado em lote diferente")
    elif row["dup_id_nfe"] and row["dup_chave_negocio"]:
        score = 70
        motivos.append("Mesma NF reapresentada")
    elif row["dup_chave_negocio"]:
        score = 60
        motivos.append("Chave de negocio duplicada")
    elif row["dup_id_nfe"]:
        score = 40
        motivos.append("ID da NF repetido")
    else:
        motivos.append("Sem indicios tecnicos")

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

    if row["grupo_paciente_prestador_proc_data"] >= 2 and not row["dup_hash"]:
        score += 70
        motivos.append("Mesmo paciente + prestador + procedimento + data")

    if row["grupo_guia"] >= 2 and not row["dup_hash"] and row["guia_atendimento"]:
        score += 60
        motivos.append("Mesma guia reaproveitada")

    if row["grupo_usuario_evento"] >= 3 and row["usuario_envio"]:
        score += 20
        motivos.append("Usuario repetindo padrao semelhante")

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
        motivos.append("Sem padrao comportamental suspeito")

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
    arquivos = sorted(DEMO_DIR.glob("*.xml"))[:limit]
    demo_files = []
    for caminho in arquivos:
        demo_files.append(
            {
                "name": caminho.name,
                "content": caminho.read_bytes(),
            }
        )
    return demo_files


def processar_arquivos(arquivos):
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
        "potencial_revisao": reapresentacao + duplicidade + comportamento,
        "valor_em_alerta": float(df.loc[df["score_final"] >= 60, "valor_nf_num"].sum()),
    }


def formatar_brl(valor):
    texto = f"{valor:,.2f}"
    texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


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
            <h1>Revele duplicidades e sinais de reapresentacao antes do reembolso sair.</h1>
            <p>
                Esta demo transforma XMLs de NF-e em uma fila priorizada de risco. Em minutos,
                o time identifica reapresentacoes, duplicidades tecnicas e padroes comportamentais
                suspeitos para auditoria, glosa e prevencao de perdas.
            </p>
            <div class="pill-row">
                <div class="pill">Upload em lote</div>
                <div class="pill">Priorizacao automatica</div>
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
                    Reembolsos podem ser aprovados com documentos reapresentados ou com padroes
                    repetitivos que passam despercebidos em analise manual.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            """
            <div class="glass-card">
                <div class="section-title">Solucao</div>
                <div class="section-copy">
                    O PSL le XMLs, cruza sinais tecnicos e comportamentais e prioriza os casos
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
                    Menos revisao cega, mais foco no que merece auditoria. O resultado sai em
                    formato operacional, pronto para investigacao ou integracao.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_empty_state():
    st.markdown("### Como demonstrar em 30 segundos")
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
    st.info("Voce pode subir XMLs reais ou usar a demo guiada para mostrar valor imediatamente.")


def render_results(df, origem):
    resumo = resumo_executivo(df)

    st.markdown(f"### Painel executivo")
    st.caption(f"Fonte analisada: {origem}")

    c1, c2, c3, c4, c5 = st.columns(5)
    render_metric(c1, "blue", "XMLs analisados", resumo["total"], "volume processado na rodada")
    render_metric(c2, "red", "Reapresentacao", resumo["reapresentacao"], "forte indicio tecnico")
    render_metric(c3, "orange", "Duplicidade", resumo["duplicidade"], "casos tecnicos relevantes")
    render_metric(c4, "gold", "Comportamental", resumo["comportamento"], "padroes suspeitos")
    render_metric(c5, "green", "Normais", resumo["normais"], "sem alerta relevante")

    a1, a2 = st.columns([1.2, 1])
    with a1:
        st.markdown(
            f"""
            <div class="insight-box">
                <strong>Resumo para decisor:</strong> {resumo["potencial_revisao"]} de {resumo["total"]} documentos
                foram priorizados para revisao, com <strong>{formatar_brl(resumo["valor_em_alerta"])}</strong>
                em valor associado a alertas de score 60+.
            </div>
            """,
            unsafe_allow_html=True,
        )
    with a2:
        top_classificacoes = df["classificacao_final"].value_counts().head(4)
        st.markdown(
            """
            <div class="glass-card">
                <div class="section-title">Distribuicao de alertas</div>
            """,
            unsafe_allow_html=True,
        )
        st.bar_chart(top_classificacoes)
        st.markdown("</div>", unsafe_allow_html=True)

    t1, t2, t3 = st.columns(3)
    with t1:
        st.markdown("#### Usuarios mais recorrentes")
        st.dataframe(df["usuario_envio"].replace("", "Nao informado").value_counts().head(5), use_container_width=True)
    with t2:
        st.markdown("#### Prestadores mais expostos")
        st.dataframe(df["prestador"].replace("", "Nao informado").value_counts().head(5), use_container_width=True)
    with t3:
        st.markdown("#### Pacientes mais recorrentes")
        st.dataframe(df["paciente"].replace("", "Nao informado").value_counts().head(5), use_container_width=True)

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
    st.markdown("## Modo de demonstracao")
    usar_demo = st.button("Carregar demo guiada", use_container_width=True)
    st.caption("A demo usa XMLs de exemplo ja publicados no repositorio.")
    st.markdown("---")
    st.markdown("## Como vender em reuniao")
    st.markdown(
        """
        - mostre o resumo executivo
        - abra os 10 casos priorizados
        - destaque o valor em alerta
        - exporte o CSV para provar operacionalizacao
        """
    )

uploaded_files = st.file_uploader(
    "Suba XMLs reais ou de teste",
    type=["xml"],
    accept_multiple_files=True,
    help="Voce pode usar seus XMLs ou acionar a demo guiada no menu lateral.",
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
else:
    render_empty_state()
