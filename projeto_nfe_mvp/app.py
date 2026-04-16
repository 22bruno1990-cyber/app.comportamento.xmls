from datetime import datetime
import base64
import hashlib
import hmac
import os
from pathlib import Path
import re
import sqlite3
import uuid
import xml.etree.ElementTree as ET

import pandas as pd
try:
    import psycopg
    from psycopg.rows import dict_row
except Exception:  # pragma: no cover
    psycopg = None
    dict_row = None
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

    h3, h4 {
        color: #152b4c !important;
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
        min-height: 260px;
        margin-top: 10px;
    }

    .panel-block {
        margin-top: 2.2rem;
    }

    .section-gap {
        height: 1.6rem;
    }

    .section-gap-lg {
        height: 3.1rem;
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

    .chart-text {
        color: #223a5b;
        font-size: 0.88rem;
        font-weight: 800;
        letter-spacing: 0.03em;
    }

    .chart-row {
        display: grid;
        grid-template-columns: 150px 1fr 42px;
        align-items: center;
        gap: 14px;
        margin: 16px 0;
    }

    .chart-label {
        color: #223a5b;
        font-size: 0.9rem;
        font-weight: 800;
        letter-spacing: 0.03em;
        text-transform: uppercase;
    }

    .chart-track {
        width: 100%;
        height: 14px;
        background: #d7e3f3;
        border-radius: 999px;
        overflow: hidden;
    }

    .chart-fill {
        height: 100%;
        border-radius: 999px;
        background: linear-gradient(90deg, #2f73c6 0%, #5f96d8 100%);
    }

    .chart-value {
        color: #223a5b;
        font-size: 0.95rem;
        font-weight: 800;
        text-align: right;
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

    .stTextInput label,
    .stTextInput div[data-testid="stWidgetLabel"],
    .stRadio label,
    .stRadio div[data-testid="stWidgetLabel"],
    .stFileUploader label,
    .stFileUploader div[data-testid="stWidgetLabel"],
    .stMarkdown h3,
    .stMarkdown h4,
    .stCaptionContainer,
    div[data-testid="stCaptionContainer"] {
        color: #152b4c !important;
    }

    .stTextInput input {
        color: #152b4c !important;
    }

    .stTextInput > div > div,
    .stTextInput div[data-baseweb="input"] {
        background: #eef4ff !important;
        border: 1px solid #b8cdee !important;
        border-radius: 16px !important;
        box-shadow: none !important;
    }

    .stTextInput input::placeholder {
        color: #6c84a5 !important;
    }

    .stTextInput [data-testid="stMarkdownContainer"] p,
    .stTextInput svg {
        color: #5b7fb0 !important;
        fill: #5b7fb0 !important;
    }

    .stButton > button,
    .stForm button {
        background: linear-gradient(135deg, #5b86bf 0%, #7fa7d8 100%) !important;
        color: #ffffff !important;
        border: 1px solid #6f96ca !important;
        border-radius: 16px !important;
        box-shadow: 0 10px 24px rgba(77, 117, 170, 0.18) !important;
    }

    .stButton > button:hover,
    .stForm button:hover {
        background: linear-gradient(135deg, #4f79b0 0%, #729ccd 100%) !important;
        border-color: #5b86bf !important;
    }

    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3,
    section[data-testid="stSidebar"] .stMarkdown h4,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] div[data-testid="stWidgetLabel"],
    section[data-testid="stSidebar"] div[data-testid="stCaptionContainer"] {
        color: #f2f6ff !important;
    }

    section[data-testid="stSidebar"] .stCaptionContainer {
        color: #c9d8f2 !important;
    }

    .login-page .stApp {
        color-scheme: dark;
        background:
            linear-gradient(180deg, rgba(2, 8, 26, 0.66) 0%, rgba(3, 10, 30, 0.82) 100%),
            radial-gradient(circle at 50% 20%, rgba(86, 214, 255, 0.18), transparent 18%);
        background-attachment: fixed;
    }

    .login-page [data-testid="stAppViewContainer"] {
        color-scheme: dark;
        background:
            linear-gradient(180deg, rgba(2, 8, 26, 0.68) 0%, rgba(3, 10, 30, 0.84) 100%);
    }

    .login-stage {
        min-height: calc(100vh - 3rem);
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .login-stage [data-testid="stForm"] {
        color-scheme: dark;
        background: rgba(8, 18, 42, 0.56);
        border: 1px solid rgba(173, 205, 245, 0.24);
        backdrop-filter: blur(18px);
        border-radius: 24px;
        padding: 10px 16px 10px 16px;
        box-shadow: 0 28px 64px rgba(4, 12, 32, 0.42);
        max-width: 360px;
        margin: 0 auto;
    }

    .login-title {
        color: #f7fbff;
        font-size: 1.08rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 4px;
    }

    .login-copy {
        color: #c6d7ef;
        font-size: 0.88rem;
        line-height: 1.45;
        text-align: center;
        margin-bottom: 14px;
    }

    .login-helper {
        color: #b0c7e6;
        font-size: 0.8rem;
        text-align: center;
        margin-top: 6px;
    }

    .login-stage .stTextInput label,
    .login-stage .stTextInput div[data-testid="stWidgetLabel"] {
        color: #eef4ff !important;
    }

    .login-stage .stTextInput > div > div,
    .login-stage .stTextInput div[data-baseweb="input"],
    .login-stage .stTextInput div[data-baseweb="input"] > div,
    .login-stage .stTextInput div[data-baseweb="base-input"],
    .login-stage .stTextInput div[data-baseweb="base-input"] > div,
    .login-stage [data-testid="stTextInputRootElement"],
    .login-stage [data-testid="stTextInputRootElement"] > div {
        color-scheme: dark !important;
        background: transparent !important;
        background-color: rgba(7, 19, 44, 0.72) !important;
        border: 1px solid rgba(141, 177, 224, 0.42) !important;
        border-radius: 14px !important;
    }

    .login-stage .stTextInput input,
    .login-stage [data-testid="stTextInputRootElement"] input {
        color-scheme: dark !important;
        color: #f4f8ff !important;
        caret-color: #f4f8ff !important;
        background: transparent !important;
        background-color: transparent !important;
        background-image: none !important;
        box-shadow: none !important;
        -webkit-text-fill-color: #f4f8ff !important;
        -webkit-box-shadow: 0 0 0 1000px rgba(7, 19, 44, 0.001) inset !important;
        -webkit-appearance: none !important;
        appearance: none !important;
    }

    .login-stage input[type="text"],
    .login-stage input[type="password"] {
        background: transparent !important;
        background-color: transparent !important;
        background-image: none !important;
        color: #f4f8ff !important;
        -webkit-text-fill-color: #f4f8ff !important;
        -webkit-box-shadow: 0 0 0 1000px rgba(7, 19, 44, 0.001) inset !important;
        -webkit-appearance: none !important;
    }

    .login-stage input:-webkit-autofill,
    .login-stage input:-webkit-autofill:hover,
    .login-stage input:-webkit-autofill:focus,
    .login-stage input:-webkit-autofill:active {
        -webkit-text-fill-color: #f4f8ff !important;
        -webkit-box-shadow: 0 0 0 1000px rgba(7, 19, 44, 0.001) inset !important;
        transition: background-color 9999s ease-in-out 0s;
    }

    .login-stage [data-baseweb="input"]::before,
    .login-stage [data-baseweb="base-input"]::before,
    .login-stage [data-baseweb="input"]::after,
    .login-stage [data-baseweb="base-input"]::after {
        background: transparent !important;
    }

    .login-stage .stTextInput input::placeholder {
        color: rgba(233, 241, 255, 0.70) !important;
    }

    .login-stage .stTextInput [data-testid="stMarkdownContainer"] p,
    .login-stage .stTextInput svg {
        color: #d9e7ff !important;
        fill: #d9e7ff !important;
    }

    .login-stage .stButton > button,
    .login-stage .stForm button {
        min-height: 46px !important;
        font-weight: 800 !important;
    }

    .login-stage .stForm {
        margin-top: 0 !important;
    }

    .login-stage [data-testid="stForm"] {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }

    .login-stage .stTextInput {
        margin-bottom: 0.35rem !important;
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
ASSETS_DIR = BASE_DIR / "assets"
LOGIN_LOGO_PATH = ASSETS_DIR / "solvyx-login.png"
ESTETICA_KEYWORDS = [
    "estet",
    "beauty",
    "harmon",
    "cosmet",
    "spa",
    "wellness",
    "laser",
    "skin",
    "face",
    "corpo",
]
CONSULTA_CAMUFLADA_KEYWORDS = [
    "dermat",
    "nutri",
    "consulta",
    "avaliacao",
]


def get_database_url():
    try:
        if "DATABASE_URL" in st.secrets:
            return st.secrets["DATABASE_URL"]
    except Exception:
        pass
    return os.getenv("DATABASE_URL", "").strip()


def is_postgres():
    database_url = get_database_url()
    return bool(database_url) and database_url.startswith(("postgres://", "postgresql://"))


def adapt_query(query):
    if not is_postgres():
        return query
    adapted = query.replace("?", "%s")
    adapted = re.sub(r":([A-Za-z_][A-Za-z0-9_]*)", r"%(\1)s", adapted)
    return adapted


def image_to_base64(path):
    if not path.exists():
        return ""
    return base64.b64encode(path.read_bytes()).decode("utf-8")

SEGMENT_COPY = {
    "Saúde": {
        "hero_title": "Revele duplicidades e sinais de reapresentação antes do reembolso sair.",
        "hero_text": (
            "Esta demo transforma XMLs de NF-e em uma fila priorizada de risco. Em minutos, "
            "o time identifica reapresentações, duplicidades técnicas e padrões comportamentais "
            "suspeitos para auditoria, glosa e prevenção de perdas."
        ),
        "pill_4": "Demo pronta para comprador",
        "problem": (
            "Reembolsos podem ser aprovados com documentos reapresentados ou com padrões "
            "repetitivos que passam despercebidos em análise manual."
        ),
        "solution": (
            "O PSL lê XMLs, cruza sinais técnicos e comportamentais, consulta o histórico, "
            "detecta abuso de serviço, crescimento exponencial, quebra de NF e possível estético camuflado, "
            "e prioriza os casos com maior chance de perda financeira."
        ),
        "value": (
            "Menos revisão cega, mais foco no que merece auditoria. O resultado sai em "
            "formato operacional, pronto para investigação, memória histórica ou integração."
        ),
        "empty_info": "Você pode subir XMLs reais ou usar a demo guiada para mostrar valor imediatamente.",
        "panel_title": "Painel executivo",
        "source_prefix": "Fonte analisada",
        "summary_title": "Resumo para decisor",
        "summary_copy": (
            "<strong>{potencial}</strong> de <strong>{total}</strong> documentos foram "
            "priorizados para revisão, com <strong>{valor}</strong> em valor associado a alertas "
            "de score 60+. O histórico já reconheceu <strong>{vistos}</strong> documento(s) com vínculo anterior."
        ),
        "distribution_title": "Distribuição de alertas",
        "risk_caption": "Separação executiva dos casos para demonstrar fraude forte, suspeita e duplicidade com valor potencial evitado.",
        "legend": (
            "Legenda rápida: abuso de serviço = valor acima da mediana do procedimento; "
            "quebra de NF = fracionamento do valor em 2x, 3x ou 4x dentro do mesmo contexto; "
            "crescimento exponencial = salto do ticket médio com volume semelhante; "
            "estético camuflado = indício estético no prestador + grupo familiar concentrado no mesmo lote."
        ),
        "upload_label": "Suba XMLs reais ou de teste",
        "upload_help": "Você pode usar seus XMLs ou acionar a demo guiada no menu lateral.",
        "demo_origin": "Demo guiada com XMLs de exemplo",
        "manual_origin": "Upload manual de {qtd} arquivo(s)",
        "field_labels": {
            "paciente": "paciente",
            "cpf_paciente": "cpf_paciente",
            "prestador": "prestador",
            "procedimento": "procedimento",
            "data_atendimento": "data_atendimento",
            "evento_clinico": "evento_clinico",
            "guia_atendimento": "guia_atendimento",
            "top_recurrence_title": "Pacientes mais recorrentes",
            "top_exposed_title": "Prestadores mais expostos",
        },
    },
    "Contas a pagar": {
        "hero_title": "Revele duplicidades, fracionamentos e reapresentações antes do pagamento sair.",
        "hero_text": (
            "Esta demo transforma XMLs de NF-e em uma fila priorizada de risco. Em minutos, "
            "o financeiro identifica notas reapresentadas, duplicidades técnicas, fracionamentos "
            "de cobrança e padrões suspeitos para auditoria e prevenção de pagamentos indevidos."
        ),
        "pill_4": "Demo pronta para financeiro",
        "problem": (
            "Pagamentos podem ser liberados com notas reapresentadas, cobranças fracionadas "
            "ou padrões repetitivos que passam despercebidos na conferência manual."
        ),
        "solution": (
            "O PSL lê XMLs, cruza sinais técnicos e comportamentais, consulta o histórico, "
            "detecta cobrança acima da referência, crescimento anômalo, quebra de NF e "
            "reapresentações antes da saída do pagamento."
        ),
        "value": (
            "Menos conferência cega, mais foco no que realmente merece revisão. O resultado sai "
            "em formato operacional, pronto para investigação, memória histórica ou integração com contas a pagar."
        ),
        "empty_info": "Você pode subir XMLs reais de fornecedores ou usar a demo guiada para mostrar valor imediatamente.",
        "panel_title": "Painel executivo",
        "source_prefix": "Base analisada",
        "summary_title": "Resumo para decisor",
        "summary_copy": (
            "<strong>{potencial}</strong> de <strong>{total}</strong> documentos foram "
            "priorizados para revisão, com <strong>{valor}</strong> em valor associado a alertas "
            "de score 60+. O histórico já reconheceu <strong>{vistos}</strong> documento(s) com possível vínculo anterior."
        ),
        "distribution_title": "Distribuição de alertas",
        "risk_caption": "Separação executiva dos casos para demonstrar pagamento indevido, suspeita operacional e duplicidade com valor potencial evitado.",
        "legend": (
            "Legenda rápida: abuso de serviço = cobrança acima da mediana da referência; "
            "quebra de NF = fracionamento do valor em 2x, 3x ou 4x dentro do mesmo contexto; "
            "crescimento exponencial = salto do ticket médio com volume semelhante; "
            "estético camuflado = heurística aplicável quando houver padrão de serviço possivelmente camuflado."
        ),
        "upload_label": "Suba XMLs de fornecedores ou de teste",
        "upload_help": "Você pode usar XMLs reais de contas a pagar ou acionar a demo guiada no menu lateral.",
        "demo_origin": "Demo guiada com XMLs de exemplo",
        "manual_origin": "Upload manual de {qtd} arquivo(s)",
        "field_labels": {
            "paciente": "favorecido",
            "cpf_paciente": "doc_favorecido",
            "prestador": "fornecedor",
            "procedimento": "categoria_cobranca",
            "data_atendimento": "data_referencia",
            "evento_clinico": "natureza_evento",
            "guia_atendimento": "referencia_interna",
            "top_recurrence_title": "Favorecidos mais recorrentes",
            "top_exposed_title": "Fornecedores mais expostos",
        },
    },
}


def gerar_hash(conteudo):
    return hashlib.sha256(conteudo).hexdigest()


def normalizar_texto(valor):
    return (valor or "").strip().lower()


def extrair_sobrenome(nome):
    partes = [parte for parte in (nome or "").replace("-", " ").split() if parte]
    return partes[-1].lower() if len(partes) >= 2 else ""


def get_db_connection():
    if is_postgres():
        if psycopg is None:
            raise RuntimeError("psycopg não está instalado. Adicione a dependência para usar PostgreSQL.")
        return psycopg.connect(get_database_url(), row_factory=dict_row)
    DB_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def db_execute(conn, query, params=None):
    if is_postgres():
        with conn.cursor() as cur:
            if params is None:
                cur.execute(adapt_query(query))
            else:
                cur.execute(adapt_query(query), params)
        return None
    return conn.execute(query, params or ())


def db_fetchone(conn, query, params=None):
    if is_postgres():
        with conn.cursor() as cur:
            if params is None:
                cur.execute(adapt_query(query))
            else:
                cur.execute(adapt_query(query), params)
            return cur.fetchone()
    return conn.execute(query, params or ()).fetchone()


def db_fetchall(conn, query, params=None):
    if is_postgres():
        with conn.cursor() as cur:
            if params is None:
                cur.execute(adapt_query(query))
            else:
                cur.execute(adapt_query(query), params)
            return cur.fetchall()
    return conn.execute(query, params or ()).fetchall()


def db_executemany(conn, query, seq_params):
    if is_postgres():
        with conn.cursor() as cur:
            cur.executemany(adapt_query(query), seq_params)
        return None
    return conn.executemany(query, seq_params)


def hash_password(password, salt=None):
    salt = salt or os.urandom(16)
    password_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 150000)
    return f"{salt.hex()}${password_hash.hex()}"


def verify_password(password, stored_hash):
    try:
        salt_hex, password_hash_hex = stored_hash.split("$", 1)
        recalculated = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            150000,
        ).hex()
        return hmac.compare_digest(recalculated, password_hash_hex)
    except Exception:
        return False


def get_admin_credentials():
    admin_username = ""
    admin_password = ""
    try:
        admin_username = st.secrets.get("ADMIN_USERNAME", "")
        admin_password = st.secrets.get("ADMIN_PASSWORD", "")
    except Exception:
        pass
    admin_username = admin_username or os.getenv("ADMIN_USERNAME", "")
    admin_password = admin_password or os.getenv("ADMIN_PASSWORD", "")
    return admin_username.strip(), admin_password.strip()


def inicializar_banco():
    with get_db_connection() as conn:
        if is_postgres():
            db_execute(
                conn,
                """
                CREATE TABLE IF NOT EXISTS nfe_documents (
                    id BIGSERIAL PRIMARY KEY,
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
                    valor_nf_num DOUBLE PRECISION,
                    usuario_envio TEXT,
                    paciente TEXT,
                    cpf_paciente TEXT,
                    prestador TEXT,
                    procedimento TEXT,
                    data_atendimento TEXT,
                    evento_clinico TEXT,
                    guia_atendimento TEXT,
                    lote TEXT,
                    score_final DOUBLE PRECISION,
                    classificacao_final TEXT,
                    origem_upload TEXT,
                    analisado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
            )
        else:
            db_execute(
                conn,
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
                """,
            )
        db_execute(conn, "CREATE INDEX IF NOT EXISTS idx_docs_hash ON nfe_documents(hash_arquivo)")
        db_execute(conn, "CREATE INDEX IF NOT EXISTS idx_docs_id_nfe ON nfe_documents(id_nfe)")
        db_execute(
            conn,
            """
            CREATE INDEX IF NOT EXISTS idx_docs_business
            ON nfe_documents(numero_nf, serie, cnpj_emitente, valor_nf)
            """,
        )
        db_execute(
            conn,
            """
            CREATE INDEX IF NOT EXISTS idx_docs_behavior
            ON nfe_documents(cpf_paciente, prestador, procedimento, data_atendimento)
            """,
        )
        if is_postgres():
            db_execute(
                conn,
                """
                CREATE TABLE IF NOT EXISTS app_users (
                    id BIGSERIAL PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'master',
                    active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
            )
            db_execute(
                conn,
                """
                CREATE TABLE IF NOT EXISTS upload_batches (
                    id BIGSERIAL PRIMARY KEY,
                    batch_ref TEXT UNIQUE NOT NULL,
                    batch_name TEXT,
                    origem_upload TEXT,
                    segment TEXT,
                    uploaded_by TEXT,
                    total_documentos INTEGER,
                    total_alertas INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
            )
        else:
            db_execute(
                conn,
                """
                CREATE TABLE IF NOT EXISTS app_users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'master',
                    active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """,
            )
            db_execute(
                conn,
                """
                CREATE TABLE IF NOT EXISTS upload_batches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    batch_ref TEXT UNIQUE NOT NULL,
                    batch_name TEXT,
                    origem_upload TEXT,
                    segment TEXT,
                    uploaded_by TEXT,
                    total_documentos INTEGER,
                    total_alertas INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """,
            )
        conn.commit()
    bootstrap_admin_user()


def bootstrap_admin_user():
    admin_username, admin_password = get_admin_credentials()
    if not admin_username or not admin_password:
        return

    with get_db_connection() as conn:
        existing = db_fetchone(
            conn,
            "SELECT username, password_hash FROM app_users WHERE username = ?",
            (admin_username,),
        )
        if existing:
            if not verify_password(admin_password, existing["password_hash"]):
                db_execute(
                    conn,
                    "UPDATE app_users SET password_hash = ?, role = 'admin', active = TRUE WHERE username = ?",
                    (hash_password(admin_password), admin_username),
                )
                conn.commit()
            return

        db_execute(
            conn,
            """
            INSERT INTO app_users (username, password_hash, role, active)
            VALUES (?, ?, 'admin', TRUE)
            """,
            (admin_username, hash_password(admin_password)),
        )
        conn.commit()


def load_history_stats():
    inicializar_banco()
    with get_db_connection() as conn:
        row = db_fetchone(
            conn,
            """
            SELECT
                COUNT(*) AS total_documentos,
                COUNT(DISTINCT hash_arquivo) AS hashes_unicos,
                COUNT(DISTINCT id_nfe) AS ids_unicos,
                MAX(analisado_em) AS ultima_analise
            FROM nfe_documents
            """
        )
    return {
        "total_documentos": row["total_documentos"] or 0,
        "hashes_unicos": row["hashes_unicos"] or 0,
        "ids_unicos": row["ids_unicos"] or 0,
        "ultima_analise": row["ultima_analise"] or "Sem histórico ainda",
    }


def authenticate_user(username, password):
    inicializar_banco()
    if not username or not password:
        return None

    with get_db_connection() as conn:
        user = db_fetchone(
            conn,
            """
            SELECT username, password_hash, role, active
            FROM app_users
            WHERE username = ?
            """,
            (username.strip(),),
        )

    if not user:
        return None
    if not bool(user["active"]):
        return None
    if not verify_password(password, user["password_hash"]):
        return None
    return {"username": user["username"], "role": user["role"]}


def registrar_lote_upload(df, origem_upload, segment, uploaded_by):
    inicializar_banco()
    batch_ref = f"lote_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    batch_name = ""
    if "lote" in df.columns:
        nomes_lote = sorted({str(valor).strip() for valor in df["lote"].fillna("") if str(valor).strip()})
        if nomes_lote:
            batch_name = ", ".join(nomes_lote[:3])
    if not batch_name:
        batch_name = batch_ref

    total_alertas = int((df["score_final"] >= 60).sum()) if "score_final" in df.columns else 0

    with get_db_connection() as conn:
        db_execute(
            conn,
            """
            INSERT INTO upload_batches (
                batch_ref, batch_name, origem_upload, segment, uploaded_by, total_documentos, total_alertas
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                batch_ref,
                batch_name,
                origem_upload,
                segment,
                uploaded_by,
                int(len(df)),
                total_alertas,
            ),
        )
        conn.commit()
    return batch_ref


def load_batch_history(limit=12):
    inicializar_banco()
    with get_db_connection() as conn:
        rows = db_fetchall(
            conn,
            f"""
            SELECT batch_ref, batch_name, segment, uploaded_by, total_documentos, total_alertas, created_at
            FROM upload_batches
            ORDER BY created_at DESC
            LIMIT {int(limit)}
            """,
        )
    normalizados = []
    for row in rows:
        if isinstance(row, dict):
            normalizados.append(row)
        else:
            normalizados.append(dict(row))
    lotes_df = pd.DataFrame(normalizados)
    if lotes_df.empty:
        return lotes_df

    valor_total = []
    valor_alerta = []
    with get_db_connection() as conn:
        for batch_ref in lotes_df["batch_ref"]:
            like_ref = f"%batch_ref={batch_ref}%"
            valor_total.append(
                float(
                    query_scalar(
                        conn,
                        "SELECT COALESCE(SUM(valor_nf_num), 0) FROM nfe_documents WHERE origem_upload LIKE ?",
                        (like_ref,),
                    )
                )
            )
            valor_alerta.append(
                float(
                    query_scalar(
                        conn,
                        """
                        SELECT COALESCE(SUM(valor_nf_num), 0)
                        FROM nfe_documents
                        WHERE origem_upload LIKE ?
                          AND score_final >= 60
                        """,
                        (like_ref,),
                    )
                )
            )
    lotes_df["valor_total"] = valor_total
    lotes_df["valor_alerta"] = valor_alerta
    return lotes_df


def load_batch_documents(batch_ref):
    inicializar_banco()
    with get_db_connection() as conn:
        rows = db_fetchall(
            conn,
            """
            SELECT
                arquivo,
                paciente,
                prestador,
                procedimento,
                valor_nf,
                valor_nf_num,
                score_final,
                classificacao_final,
                analisado_em
            FROM nfe_documents
            WHERE origem_upload LIKE ?
            ORDER BY score_final DESC, valor_nf_num DESC, analisado_em DESC
            """,
            (f"%batch_ref={batch_ref}%",),
        )
    normalizados = []
    for row in rows:
        if isinstance(row, dict):
            normalizados.append(row)
        else:
            normalizados.append(dict(row))
    df = pd.DataFrame(normalizados)
    if not df.empty:
        df["motivo_tecnico"] = "Disponível no detalhe da análise original"
        df["motivo_comportamental"] = "Disponível no detalhe da análise original"
    return df


def render_login_cover():
    logo_base64 = image_to_base64(LOGIN_LOGO_PATH)
    st.markdown(
        """
        <style>
        section[data-testid="stSidebar"] {display: none !important;}
        header[data-testid="stHeader"] {display: none !important;}
        .block-container {
            padding-top: 0 !important;
            padding-bottom: 0 !important;
            max-width: none !important;
            min-height: 100vh !important;
            display: flex !important;
            flex-direction: column !important;
            justify-content: flex-start !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    if logo_base64:
        st.markdown(
            f"""
            <style>
            .stApp, [data-testid="stAppViewContainer"] {{
                background:
                    linear-gradient(180deg, rgba(2, 8, 26, 0.60) 0%, rgba(3, 10, 30, 0.82) 100%),
                    url("data:image/png;base64,{logo_base64}") center center / cover no-repeat fixed !important;
            }}
            </style>
            """,
            unsafe_allow_html=True,
        )

    st.markdown('<div style="height: 22vh;"></div>', unsafe_allow_html=True)
    _, center_col, _ = st.columns([1.6, 1, 1.6])
    with center_col:
        admin_username, admin_password = get_admin_credentials()
        if admin_username and admin_password:
            with st.form("login_cover_form"):
                username_input = st.text_input("Usuário", key="cover_username")
                password_input = st.text_input("Senha", type="password", key="cover_password")
                entrou = st.form_submit_button("Entrar", use_container_width=True)
            st.markdown(
                '<div class="login-helper">Acesso restrito a usuários autorizados.</div>',
                unsafe_allow_html=True,
            )
            if entrou:
                auth_user = authenticate_user(username_input, password_input)
                if auth_user:
                    st.session_state["auth_user"] = auth_user
                    st.rerun()
                else:
                    st.error("Usuário ou senha inválidos.")
        else:
            st.warning("Faltam `ADMIN_USERNAME` e `ADMIN_PASSWORD` no Secrets para liberar o acesso autenticado.")


def query_scalar(conn, query, params):
    row = db_fetchone(conn, query, params)
    if not row:
        return 0
    if isinstance(row, dict):
        valor = next(iter(row.values()), 0)
        return valor if valor is not None else 0
    return row[0] if row[0] is not None else 0


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


def carregar_referencias_crescimento(df):
    referencias = {}
    grupos = (
        df[["prestador", "procedimento"]]
        .dropna()
        .drop_duplicates()
        .to_dict(orient="records")
    )

    with get_db_connection() as conn:
        for grupo in grupos:
            prestador = grupo["prestador"]
            procedimento = grupo["procedimento"]
            if not prestador or not procedimento:
                continue

            row = db_fetchone(
                conn,
                """
                SELECT
                    COUNT(*) AS total_registros,
                    AVG(qtd_lote) AS media_qtd_lote,
                    AVG(valor_medio_lote) AS media_valor_lote
                FROM (
                    SELECT
                        lote,
                        COUNT(*) AS qtd_lote,
                        AVG(valor_nf_num) AS valor_medio_lote
                    FROM nfe_documents
                    WHERE prestador = ?
                      AND procedimento = ?
                      AND lote <> ''
                      AND valor_nf_num > 0
                    GROUP BY lote
                ) base
                """,
                (prestador, procedimento),
            )

            referencias[(prestador, procedimento)] = {
                "total_registros": int(row["total_registros"] or 0),
                "media_qtd_lote": float(row["media_qtd_lote"] or 0),
                "media_valor_lote": float(row["media_valor_lote"] or 0),
            }

    return referencias


def carregar_referencias_quebra(df):
    referencias = {}
    grupos = (
        df[["prestador", "procedimento"]]
        .dropna()
        .drop_duplicates()
        .to_dict(orient="records")
    )

    with get_db_connection() as conn:
        for grupo in grupos:
            prestador = grupo["prestador"]
            procedimento = grupo["procedimento"]
            if not prestador or not procedimento:
                continue

            row = db_fetchone(
                conn,
                """
                SELECT MAX(valor_nf_num) AS max_valor
                FROM nfe_documents
                WHERE prestador = ?
                  AND procedimento = ?
                  AND valor_nf_num > 0
                """,
                (prestador, procedimento),
            )

            referencias[(prestador, procedimento)] = float(row["max_valor"] or 0)

    return referencias


def enrich_advanced_patterns(df):
    if df.empty:
        return df

    df["sobrenome_paciente"] = df["paciente"].apply(extrair_sobrenome)
    df["prestador_texto_base"] = (
        df["prestador"].fillna("").map(normalizar_texto)
        + " "
        + df["razao_social_emitente"].fillna("").map(normalizar_texto)
    ).str.strip()
    df["flag_prestador_estetico"] = df["prestador_texto_base"].apply(
        lambda texto: any(keyword in texto for keyword in ESTETICA_KEYWORDS)
    )
    df["flag_consulta_camuflada"] = df["procedimento"].fillna("").map(normalizar_texto).apply(
        lambda texto: any(keyword in texto for keyword in CONSULTA_CAMUFLADA_KEYWORDS)
    )
    df["grupo_familia_prestador_lote"] = df.groupby(
        ["sobrenome_paciente", "prestador", "lote"]
    )["arquivo"].transform("count")

    df["procedimento_ref_qtd"] = df.groupby("procedimento")["arquivo"].transform("count")
    df["procedimento_ref_mediana"] = df.groupby("procedimento")["valor_nf_num"].transform("median")
    df["procedimento_ref_media"] = df.groupby("procedimento")["valor_nf_num"].transform("mean")

    df["abuso_servico_pct"] = 0.0
    mascara_abuso = (
        (df["procedimento"] != "")
        & (df["procedimento_ref_qtd"] >= 4)
        & (df["procedimento_ref_mediana"] > 0)
        & (df["valor_nf_num"] >= df["procedimento_ref_mediana"] * 1.7)
        & ((df["valor_nf_num"] - df["procedimento_ref_mediana"]) >= 200)
    )
    df.loc[mascara_abuso, "abuso_servico_pct"] = (
        ((df.loc[mascara_abuso, "valor_nf_num"] / df.loc[mascara_abuso, "procedimento_ref_mediana"]) - 1) * 100
    ).round(1)
    df["flag_abuso_servico"] = mascara_abuso

    df["flag_estetico_camuflado"] = (
        (df["flag_prestador_estetico"])
        & (df["flag_consulta_camuflada"])
        & (df["sobrenome_paciente"] != "")
        & (df["grupo_familia_prestador_lote"] >= 2)
    )

    df["grupo_prestador_proc_lote_qtd"] = df.groupby(["prestador", "procedimento", "lote"])["arquivo"].transform("count")
    df["grupo_prestador_proc_lote_valor_medio"] = df.groupby(["prestador", "procedimento", "lote"])["valor_nf_num"].transform("mean")
    df["flag_crescimento_lote_atual"] = False
    df["quebra_nf_fator"] = 0
    df["valor_referencia_quebra"] = 0.0
    df["quebra_nf_gap_pct"] = 0.0
    df["flag_quebra_nf"] = False

    referencias = carregar_referencias_crescimento(df)
    referencias_quebra = carregar_referencias_quebra(df)
    hist_media_qtd_lote = []
    hist_media_valor_lote = []
    crescimento_pct = []
    flag_crescimento = []

    for _, row in df.iterrows():
        referencia = referencias.get((row["prestador"], row["procedimento"]), {})
        media_qtd = float(referencia.get("media_qtd_lote", 0))
        media_valor = float(referencia.get("media_valor_lote", 0))

        qtd_atual = float(row["grupo_prestador_proc_lote_qtd"] or 0)
        valor_atual = float(row["grupo_prestador_proc_lote_valor_medio"] or 0)

        volume_semelhante = media_qtd >= 3 and qtd_atual >= 3 and qtd_atual >= media_qtd * 0.7 and qtd_atual <= media_qtd * 1.3
        aumento_desproporcional = media_valor > 0 and valor_atual >= media_valor * 1.6
        crescimento_flag = bool(
            row["prestador"]
            and row["procedimento"]
            and row["lote"]
            and volume_semelhante
            and aumento_desproporcional
        )

        hist_media_qtd_lote.append(round(media_qtd, 2))
        hist_media_valor_lote.append(round(media_valor, 2))
        crescimento_pct.append(round(((valor_atual / media_valor) - 1) * 100, 1) if media_valor > 0 else 0.0)
        flag_crescimento.append(crescimento_flag)

    df["hist_media_qtd_lote"] = hist_media_qtd_lote
    df["hist_media_valor_lote"] = hist_media_valor_lote
    df["crescimento_pct"] = crescimento_pct
    df["flag_crescimento_exponencial"] = flag_crescimento

    # Detecta explosão entre lotes dentro da própria amostra atual
    referencia_lote_atual = {}
    agrupado = (
        df.groupby(["prestador", "procedimento", "lote"], dropna=False)
        .agg(qtd_lote=("arquivo", "count"), valor_medio=("valor_nf_num", "mean"))
        .reset_index()
    )
    for (prestador, procedimento), grupo in agrupado.groupby(["prestador", "procedimento"], dropna=False):
        grupo = grupo[(grupo["prestador"] != "") & (grupo["procedimento"] != "")]
        if len(grupo) < 2:
            continue
        grupo = grupo.sort_values("valor_medio")
        base = grupo.iloc[0]
        topo = grupo.iloc[-1]
        volume_semelhante = base["qtd_lote"] >= 2 and topo["qtd_lote"] >= 2 and topo["qtd_lote"] >= base["qtd_lote"] * 0.7 and topo["qtd_lote"] <= base["qtd_lote"] * 1.3
        crescimento_desproporcional = base["valor_medio"] > 0 and topo["valor_medio"] >= base["valor_medio"] * 1.8
        if volume_semelhante and crescimento_desproporcional:
            referencia_lote_atual[(prestador, procedimento, topo["lote"])] = round(((topo["valor_medio"] / base["valor_medio"]) - 1) * 100, 1)

    for idx, row in df.iterrows():
        chave = (row["prestador"], row["procedimento"], row["lote"])
        if chave in referencia_lote_atual:
            df.at[idx, "flag_crescimento_lote_atual"] = True
            if df.at[idx, "crescimento_pct"] <= 0:
                df.at[idx, "crescimento_pct"] = referencia_lote_atual[chave]
            if df.at[idx, "flag_crescimento_exponencial"] is False:
                df.at[idx, "flag_crescimento_exponencial"] = True

    # Detecta possível quebra / fracionamento de NF em 2x, 3x ou 4x
    grupos_quebra = (
        df.groupby(["prestador", "procedimento", "lote"], dropna=False)
        .agg(
            valor_max_lote=("valor_nf_num", "max"),
            qtd_lote=("arquivo", "count"),
        )
        .reset_index()
    )
    referencia_quebra_lote = {}
    for _, linha in grupos_quebra.iterrows():
        chave = (linha["prestador"], linha["procedimento"], linha["lote"])
        historico_max = referencias_quebra.get((linha["prestador"], linha["procedimento"]), 0.0)
        referencia_quebra_lote[chave] = max(float(linha["valor_max_lote"] or 0), float(historico_max or 0))

    for prestador, procedimento, lote in grupos_quebra[["prestador", "procedimento", "lote"]].itertuples(index=False, name=None):
        if not prestador or not procedimento or not lote:
            continue

        mascara_grupo = (
            (df["prestador"] == prestador)
            & (df["procedimento"] == procedimento)
            & (df["lote"] == lote)
        )
        referencia = referencia_quebra_lote.get((prestador, procedimento, lote), 0.0)
        if referencia < 300:
            continue

        base_grupo = df.loc[mascara_grupo].copy()
        if len(base_grupo) < 3:
            continue

        for fator in (2, 3, 4):
            alvo = referencia / fator
            tolerancia = alvo * 0.12
            candidatos_idx = base_grupo.index[
                (base_grupo["valor_nf_num"] > 0)
                & (base_grupo["valor_nf_num"] < referencia * 0.85)
                & ((base_grupo["valor_nf_num"] - alvo).abs() <= tolerancia)
            ].tolist()
            if len(candidatos_idx) < fator:
                continue

            sobrenomes = (
                df.loc[candidatos_idx, "sobrenome_paciente"]
                .replace("", pd.NA)
                .dropna()
            )
            possui_familia = not sobrenomes.empty and sobrenomes.nunique() < len(sobrenomes)
            if not possui_familia:
                continue

            for idx in candidatos_idx:
                gap_pct = abs((df.at[idx, "valor_nf_num"] / alvo) - 1) * 100 if alvo > 0 else 0
                df.at[idx, "flag_quebra_nf"] = True
                df.at[idx, "quebra_nf_fator"] = fator
                df.at[idx, "valor_referencia_quebra"] = round(referencia, 2)
                df.at[idx, "quebra_nf_gap_pct"] = round(gap_pct, 1)

    return df


def salvar_lote_no_historico(df, origem_upload, segment="Saúde", uploaded_by="sistema"):
    inicializar_banco()
    batch_ref = registrar_lote_upload(df, origem_upload, segment, uploaded_by)
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
        db_executemany(
            conn,
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
            [
                {
                    **registro,
                    "origem_upload": f"{origem_upload} | batch_ref={batch_ref} | uploaded_by={uploaded_by}",
                }
                for registro in registros
            ],
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

    if row["flag_estetico_camuflado"]:
        score += 65
        motivos.append(
            "Possível tratamento estético camuflado: prestador com indício estético e grupo familiar no mesmo lote"
        )

    if row["flag_quebra_nf"]:
        score += 58
        motivos.append(
            f'Possível quebra de NF: valor compatível com fracionamento em {int(row["quebra_nf_fator"])}x da referência de {formatar_brl(row["valor_referencia_quebra"])}'
        )

    if row["flag_crescimento_exponencial"]:
        score += 55
        origem_crescimento = "no lote atual" if row.get("flag_crescimento_lote_atual") else "vs. histórico"
        motivos.append(
            f'Crescimento exponencial do ticket medio (+{row["crescimento_pct"]:.1f}%) {origem_crescimento}'
        )

    if row["flag_abuso_servico"]:
        score += 45
        motivos.append(
            f'Abuso de serviço: valor {row["abuso_servico_pct"]:.1f}% acima da mediana do procedimento'
        )

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
    if row["flag_estetico_camuflado"] and row["flag_quebra_nf"]:
        return "ESTETICO + QUEBRA"
    if row["flag_quebra_nf"] and row["flag_crescimento_exponencial"]:
        return "QUEBRA + CRESCIMENTO"
    if row["flag_quebra_nf"] and row["flag_abuso_servico"]:
        return "QUEBRA + ABUSO"
    if row["flag_quebra_nf"]:
        return "QUEBRA DE NF"
    if row["flag_estetico_camuflado"]:
        return "ESTETICO CAMUFLADO"
    if row["flag_crescimento_exponencial"] and row["flag_abuso_servico"]:
        return "ABUSO + CRESCIMENTO"
    if row["flag_crescimento_exponencial"]:
        return "CRESCIMENTO EXPONENCIAL"
    if row["flag_abuso_servico"]:
        return "ABUSO DE SERVICO"
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
    if classificacao in {"ESTETICO + QUEBRA", "QUEBRA + CRESCIMENTO", "QUEBRA + ABUSO", "QUEBRA DE NF"}:
        return ["background-color:#3f2a67;color:#f7f4ff"] * len(row)
    if classificacao == "ESTETICO CAMUFLADO":
        return ["background-color:#53376a;color:#fff7ff"] * len(row)
    if classificacao in {"ABUSO + CRESCIMENTO", "CRESCIMENTO EXPONENCIAL"}:
        return ["background-color:#5f3b18;color:#fff8f1"] * len(row)
    if classificacao == "ABUSO DE SERVICO":
        return ["background-color:#6a5318;color:#fffdf2"] * len(row)
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

    # Injeta dois lotes sintéticos para demonstrar crescimento exponencial e abuso de serviço
    def ajustar_xml(
        conteudo,
        novo_valor=None,
        novo_lote=None,
        overrides_inf_cpl=None,
        novo_emitente=None,
    ):
        root = ET.fromstring(conteudo)
        valor_el = root.find(".//nfe:total/nfe:ICMSTot/nfe:vNF", NAMESPACE)
        inf_cpl_el = root.find(".//nfe:infAdic/nfe:infCpl", NAMESPACE)
        emitente_el = root.find(".//nfe:emit/nfe:xNome", NAMESPACE)
        if novo_valor is not None and valor_el is not None:
            valor_el.text = f"{novo_valor:.2f}"
        if novo_emitente is not None and emitente_el is not None:
            emitente_el.text = novo_emitente
        if inf_cpl_el is not None and inf_cpl_el.text:
            partes = [parte.strip() for parte in inf_cpl_el.text.replace("\n", " ").split("|")]
            mapa = {}
            for parte in partes:
                if "=" in parte:
                    chave, valor = parte.split("=", 1)
                    mapa[chave.strip()] = valor.strip()
            if novo_lote is not None:
                mapa["lote"] = novo_lote
            if overrides_inf_cpl:
                mapa.update(overrides_inf_cpl)
            novas_partes = []
            ordem = [
                "usuario_envio",
                "paciente",
                "cpf_paciente",
                "prestador",
                "procedimento",
                "data_atendimento",
                "evento_clinico",
                "guia_atendimento",
                "lote",
            ]
            for chave in ordem:
                if chave in mapa:
                    novas_partes.append(f"{chave}={mapa[chave]}")
            inf_cpl_el.text = " |\n".join(novas_partes)
        return ET.tostring(root, encoding="utf-8", xml_declaration=True)

    base_crescimento = todos.get("NFe_1000.xml")
    base_crescimento_2 = todos.get("NFe_DUP_MESMO_LOTE_1000.xml")
    if base_crescimento and base_crescimento_2:
        demo_files.extend(
            [
                {
                    "name": "DEMO_CRESC_BASE_01.xml",
                    "content": ajustar_xml(base_crescimento.read_bytes(), novo_valor=980.0, novo_lote="lote_demo_base"),
                },
                {
                    "name": "DEMO_CRESC_BASE_02.xml",
                    "content": ajustar_xml(base_crescimento_2.read_bytes(), novo_valor=1015.0, novo_lote="lote_demo_base"),
                },
                {
                    "name": "DEMO_CRESC_ALTO_01.xml",
                    "content": ajustar_xml(base_crescimento.read_bytes(), novo_valor=3480.0, novo_lote="lote_demo_explosao"),
                },
                {
                    "name": "DEMO_CRESC_ALTO_02.xml",
                    "content": ajustar_xml(base_crescimento_2.read_bytes(), novo_valor=3590.0, novo_lote="lote_demo_explosao"),
                },
            ]
        )

    base_estetica_1 = todos.get("NFe_1001.xml")
    base_estetica_2 = todos.get("NFe_1004.xml")
    base_estetica_3 = todos.get("NFe_1008.xml")
    if base_estetica_1 and base_estetica_2 and base_estetica_3:
        demo_files.extend(
            [
                {
                    "name": "DEMO_ESTETICA_FAMILIA_01.xml",
                    "content": ajustar_xml(
                        base_estetica_1.read_bytes(),
                        novo_valor=1480.0,
                        novo_lote="lote_estetica_familia",
                        novo_emitente="Clinica Derma Beauty Integrada",
                        overrides_inf_cpl={
                            "paciente": "Mariana Souza",
                            "cpf_paciente": "11122233344",
                            "prestador": "Derma Beauty Estetica Integrada",
                            "procedimento": "Consulta dermatologica",
                            "data_atendimento": "2026-02-03",
                            "evento_clinico": "Consulta ambulatorial",
                            "guia_atendimento": "GUIAEST001",
                        },
                    ),
                },
                {
                    "name": "DEMO_ESTETICA_FAMILIA_02.xml",
                    "content": ajustar_xml(
                        base_estetica_2.read_bytes(),
                        novo_valor=1520.0,
                        novo_lote="lote_estetica_familia",
                        novo_emitente="Clinica Derma Beauty Integrada",
                        overrides_inf_cpl={
                            "paciente": "Carlos Souza",
                            "cpf_paciente": "22233344455",
                            "prestador": "Derma Beauty Estetica Integrada",
                            "procedimento": "Consulta dermatologica",
                            "data_atendimento": "2026-02-03",
                            "evento_clinico": "Consulta ambulatorial",
                            "guia_atendimento": "GUIAEST002",
                        },
                    ),
                },
                {
                    "name": "DEMO_ESTETICA_FAMILIA_03.xml",
                    "content": ajustar_xml(
                        base_estetica_3.read_bytes(),
                        novo_valor=1380.0,
                        novo_lote="lote_estetica_familia",
                        novo_emitente="Centro Nutri Wellness Estetica",
                        overrides_inf_cpl={
                            "paciente": "Fernanda Lima",
                            "cpf_paciente": "33344455566",
                            "prestador": "Nutri Wellness Estetica Avancada",
                            "procedimento": "Consulta nutricional",
                            "data_atendimento": "2026-02-05",
                            "evento_clinico": "Consulta ambulatorial",
                            "guia_atendimento": "GUIAEST003",
                        },
                    ),
                },
                {
                    "name": "DEMO_ESTETICA_FAMILIA_04.xml",
                    "content": ajustar_xml(
                        base_estetica_1.read_bytes(),
                        novo_valor=1415.0,
                        novo_lote="lote_estetica_familia",
                        novo_emitente="Centro Nutri Wellness Estetica",
                        overrides_inf_cpl={
                            "paciente": "Ricardo Lima",
                            "cpf_paciente": "44455566677",
                            "prestador": "Nutri Wellness Estetica Avancada",
                            "procedimento": "Consulta nutricional",
                            "data_atendimento": "2026-02-05",
                            "evento_clinico": "Consulta ambulatorial",
                            "guia_atendimento": "GUIAEST004",
                        },
                    ),
                },
            ]
        )

    base_quebra_1 = todos.get("NFe_1002.xml")
    base_quebra_2 = todos.get("NFe_1005.xml")
    base_quebra_3 = todos.get("NFe_1006.xml")
    if base_quebra_1 and base_quebra_2 and base_quebra_3:
        demo_files.extend(
            [
                {
                    "name": "DEMO_QUEBRA_BASE_01.xml",
                    "content": ajustar_xml(
                        base_quebra_1.read_bytes(),
                        novo_valor=500.0,
                        novo_lote="lote_quebra_nf",
                        novo_emitente="Clinica Prime Derma",
                        overrides_inf_cpl={
                            "paciente": "Patricia Costa",
                            "cpf_paciente": "55511122233",
                            "prestador": "Clinica Prime Derma",
                            "procedimento": "Consulta dermatologica",
                            "data_atendimento": "2026-02-10",
                            "evento_clinico": "Consulta ambulatorial",
                            "guia_atendimento": "GUIAQBR001",
                        },
                    ),
                },
                {
                    "name": "DEMO_QUEBRA_MEIO_01.xml",
                    "content": ajustar_xml(
                        base_quebra_2.read_bytes(),
                        novo_valor=250.0,
                        novo_lote="lote_quebra_nf",
                        novo_emitente="Clinica Prime Derma",
                        overrides_inf_cpl={
                            "paciente": "Marcos Costa",
                            "cpf_paciente": "55511122244",
                            "prestador": "Clinica Prime Derma",
                            "procedimento": "Consulta dermatologica",
                            "data_atendimento": "2026-02-10",
                            "evento_clinico": "Consulta ambulatorial",
                            "guia_atendimento": "GUIAQBR002",
                        },
                    ),
                },
                {
                    "name": "DEMO_QUEBRA_MEIO_02.xml",
                    "content": ajustar_xml(
                        base_quebra_3.read_bytes(),
                        novo_valor=250.0,
                        novo_lote="lote_quebra_nf",
                        novo_emitente="Clinica Prime Derma",
                        overrides_inf_cpl={
                            "paciente": "Renata Costa",
                            "cpf_paciente": "55511122255",
                            "prestador": "Clinica Prime Derma",
                            "procedimento": "Consulta dermatologica",
                            "data_atendimento": "2026-02-10",
                            "evento_clinico": "Consulta ambulatorial",
                            "guia_atendimento": "GUIAQBR003",
                        },
                    ),
                },
                {
                    "name": "DEMO_QUEBRA_BASE_02.xml",
                    "content": ajustar_xml(
                        base_quebra_1.read_bytes(),
                        novo_valor=600.0,
                        novo_lote="lote_quebra_nf_tripla",
                        novo_emitente="Centro Nutri Care",
                        overrides_inf_cpl={
                            "paciente": "Luciana Pereira",
                            "cpf_paciente": "66622233344",
                            "prestador": "Centro Nutri Care",
                            "procedimento": "Consulta nutricional",
                            "data_atendimento": "2026-02-12",
                            "evento_clinico": "Consulta ambulatorial",
                            "guia_atendimento": "GUIAQBR004",
                        },
                    ),
                },
                {
                    "name": "DEMO_QUEBRA_TERCO_01.xml",
                    "content": ajustar_xml(
                        base_quebra_2.read_bytes(),
                        novo_valor=200.0,
                        novo_lote="lote_quebra_nf_tripla",
                        novo_emitente="Centro Nutri Care",
                        overrides_inf_cpl={
                            "paciente": "Ricardo Pereira",
                            "cpf_paciente": "66622233355",
                            "prestador": "Centro Nutri Care",
                            "procedimento": "Consulta nutricional",
                            "data_atendimento": "2026-02-12",
                            "evento_clinico": "Consulta ambulatorial",
                            "guia_atendimento": "GUIAQBR005",
                        },
                    ),
                },
                {
                    "name": "DEMO_QUEBRA_TERCO_02.xml",
                    "content": ajustar_xml(
                        base_quebra_3.read_bytes(),
                        novo_valor=200.0,
                        novo_lote="lote_quebra_nf_tripla",
                        novo_emitente="Centro Nutri Care",
                        overrides_inf_cpl={
                            "paciente": "Fernanda Pereira",
                            "cpf_paciente": "66622233366",
                            "prestador": "Centro Nutri Care",
                            "procedimento": "Consulta nutricional",
                            "data_atendimento": "2026-02-12",
                            "evento_clinico": "Consulta ambulatorial",
                            "guia_atendimento": "GUIAQBR006",
                        },
                    ),
                },
                {
                    "name": "DEMO_QUEBRA_TERCO_03.xml",
                    "content": ajustar_xml(
                        base_quebra_1.read_bytes(),
                        novo_valor=200.0,
                        novo_lote="lote_quebra_nf_tripla",
                        novo_emitente="Centro Nutri Care",
                        overrides_inf_cpl={
                            "paciente": "Tiago Pereira",
                            "cpf_paciente": "66622233377",
                            "prestador": "Centro Nutri Care",
                            "procedimento": "Consulta nutricional",
                            "data_atendimento": "2026-02-12",
                            "evento_clinico": "Consulta ambulatorial",
                            "guia_atendimento": "GUIAQBR007",
                        },
                    ),
                },
            ]
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
    df = enrich_advanced_patterns(df)

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
        df["classificacao_final"].isin(
            [
                "COMPORTAMENTO SUSPEITO",
                "ALERTA COMPORTAMENTAL",
                "ALERTA",
                "ESTETICO CAMUFLADO",
                "ESTETICO + QUEBRA",
                "ABUSO DE SERVICO",
                "CRESCIMENTO EXPONENCIAL",
                "ABUSO + CRESCIMENTO",
                "QUEBRA DE NF",
                "QUEBRA + ABUSO",
                "QUEBRA + CRESCIMENTO",
            ]
        ).sum()
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
            df.loc[
                df["classificacao_final"].isin(
                    [
                        "COMPORTAMENTO SUSPEITO",
                        "ALERTA COMPORTAMENTAL",
                        "ALERTA",
                        "ESTETICO CAMUFLADO",
                        "ESTETICO + QUEBRA",
                        "ABUSO DE SERVICO",
                        "CRESCIMENTO EXPONENCIAL",
                        "ABUSO + CRESCIMENTO",
                        "QUEBRA DE NF",
                        "QUEBRA + ABUSO",
                        "QUEBRA + CRESCIMENTO",
                    ]
                ),
                "valor_nf_num",
            ].sum()
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
    if classificacao in {
        "COMPORTAMENTO SUSPEITO",
        "ALERTA COMPORTAMENTAL",
        "ALERTA",
        "ESTETICO CAMUFLADO",
        "ESTETICO + QUEBRA",
        "ABUSO DE SERVICO",
        "CRESCIMENTO EXPONENCIAL",
        "ABUSO + CRESCIMENTO",
        "QUEBRA DE NF",
        "QUEBRA + ABUSO",
        "QUEBRA + CRESCIMENTO",
    }:
        return "SUSPEITO"
    return "NORMAL"


def resumo_categoria(df, categoria):
    base = df[df["categoria_trilha"] == categoria]
    return {
        "quantidade": int(len(base)),
        "valor": float(base["valor_nf_num"].sum()),
        "top": base.head(5),
    }


def build_column_config(copy):
    field_labels = copy["field_labels"]
    return {
        "arquivo": st.column_config.TextColumn(
            "arquivo",
            help="Nome do XML processado nesta rodada.",
        ),
        "paciente": st.column_config.TextColumn(
            field_labels["paciente"],
        ),
        "cpf_paciente": st.column_config.TextColumn(
            field_labels["cpf_paciente"],
        ),
        "prestador": st.column_config.TextColumn(
            field_labels["prestador"],
        ),
        "procedimento": st.column_config.TextColumn(
            field_labels["procedimento"],
        ),
        "data_atendimento": st.column_config.TextColumn(
            field_labels["data_atendimento"],
        ),
        "evento_clinico": st.column_config.TextColumn(
            field_labels["evento_clinico"],
        ),
        "guia_atendimento": st.column_config.TextColumn(
            field_labels["guia_atendimento"],
        ),
        "score_tecnico": st.column_config.NumberColumn(
            "score_tecnico",
            help="Pontuação dos indícios técnicos, como XML repetido, ID da NF já visto ou chave de negócio duplicada.",
            format="%d",
        ),
        "nivel_risco_tecnico": st.column_config.TextColumn(
            "nivel_risco_tecnico",
            help="Faixa de risco da análise técnica.",
        ),
        "score_comportamental": st.column_config.NumberColumn(
            "score_comportamental",
            help="Pontuação dos padrões suspeitos de comportamento, como abuso de serviço, crescimento exponencial, quebra de NF ou possível estético camuflado.",
            format="%d",
        ),
        "risco_comportamental": st.column_config.TextColumn(
            "risco_comportamental",
            help="Faixa de risco comportamental calculada pelo sistema.",
        ),
        "score_final": st.column_config.NumberColumn(
            "score_final",
            help="Maior score entre a análise técnica e a análise comportamental.",
            format="%d",
        ),
        "classificacao_final": st.column_config.TextColumn(
            "classificacao_final",
            help="Resultado final priorizado do caso: duplicidade, reapresentação, abuso de serviço, crescimento exponencial, quebra de NF, estético camuflado ou normal.",
        ),
        "motivo_tecnico": st.column_config.TextColumn(
            "motivo_tecnico",
            help="Explica quais regras técnicas fizeram o caso ser sinalizado.",
        ),
        "motivo_comportamental": st.column_config.TextColumn(
            "motivo_comportamental",
            help="Explica quais padrões de comportamento elevaram o risco do caso.",
        ),
        "motivo_historico": st.column_config.TextColumn(
            "motivo_historico",
            help="Mostra se já houve ocorrência semelhante no histórico salvo.",
        ),
        "flag_abuso_servico": st.column_config.CheckboxColumn(
            "flag_abuso_servico",
            help="Marca quando o valor do procedimento ficou muito acima da mediana do grupo no lote.",
        ),
        "abuso_servico_pct": st.column_config.NumberColumn(
            "abuso_servico_pct",
            help="Percentual acima da mediana do procedimento usado para sinalizar abuso de serviço.",
            format="%.1f%%",
        ),
        "flag_crescimento_exponencial": st.column_config.CheckboxColumn(
            "flag_crescimento_exponencial",
            help="Marca crescimento desproporcional do ticket médio com volume semelhante.",
        ),
        "flag_quebra_nf": st.column_config.CheckboxColumn(
            "flag_quebra_nf",
            help="Marca possível fracionamento de uma cobrança em 2x, 3x ou 4x dentro do mesmo contexto de prestador e procedimento.",
        ),
        "quebra_nf_fator": st.column_config.NumberColumn(
            "quebra_nf_fator",
            help="Indica em quantas partes a cobrança parece ter sido quebrada.",
            format="%d",
        ),
        "valor_referencia_quebra": st.column_config.NumberColumn(
            "valor_referencia_quebra",
            help="Maior valor de referência usado para detectar o possível fracionamento da cobrança.",
            format="R$ %.2f",
        ),
        "quebra_nf_gap_pct": st.column_config.NumberColumn(
            "quebra_nf_gap_pct",
            help="Diferença percentual entre o valor encontrado e a fração esperada da referência.",
            format="%.1f%%",
        ),
        "flag_estetico_camuflado": st.column_config.CheckboxColumn(
            "flag_estetico_camuflado",
            help="Marca possível tratamento estético camuflado com indício estético no prestador e grupo familiar concentrado no mesmo lote.",
        ),
        "flag_crescimento_lote_atual": st.column_config.CheckboxColumn(
            "flag_crescimento_lote_atual",
            help="Indica que o salto de valor foi detectado comparando lotes dentro da própria amostra enviada.",
        ),
        "crescimento_pct": st.column_config.NumberColumn(
            "crescimento_pct",
            help="Percentual de crescimento do valor médio por prestador e procedimento.",
            format="%.1f%%",
        ),
        "categoria_trilha": st.column_config.TextColumn(
            "categoria_trilha",
            help="Agrupamento executivo do caso na trilha de risco.",
        ),
        "hist_hash_count": st.column_config.NumberColumn(
            "hist_hash_count",
            help="Quantidade de vezes que o mesmo hash de XML já apareceu no histórico.",
            format="%d",
        ),
        "hist_id_count": st.column_config.NumberColumn(
            "hist_id_count",
            help="Quantidade de ocorrências do mesmo ID de NF no histórico.",
            format="%d",
        ),
        "hist_business_count": st.column_config.NumberColumn(
            "hist_business_count",
            help="Quantidade de vezes que a mesma chave de negócio apareceu no histórico.",
            format="%d",
        ),
        "hist_behavior_count": st.column_config.NumberColumn(
            "hist_behavior_count",
            help="Quantidade de padrões semelhantes já vistos no histórico para paciente, prestador, procedimento e data.",
            format="%d",
        ),
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


def render_hero(copy):
    st.markdown(
        f"""
        <div class="hero">
            <div class="hero-kicker">PSL | Revenue Protection</div>
            <h1>{copy["hero_title"]}</h1>
            <p>
                {copy["hero_text"]}
            </p>
            <div class="pill-row">
                <div class="pill">Upload em lote</div>
                <div class="pill">Priorização automática</div>
                <div class="pill">CSV para auditoria</div>
                <div class="pill">{copy["pill_4"]}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_pitch(copy):
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            f"""
            <div class="glass-card">
                <div class="section-title">Problema</div>
                <div class="section-copy">
                    {copy["problem"]}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""
            <div class="glass-card">
                <div class="section-title">Solução</div>
                <div class="section-copy">
                    {copy["solution"]}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"""
            <div class="glass-card">
                <div class="section-title">Valor para comprador</div>
                <div class="section-copy">
                    {copy["value"]}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_empty_state(copy):
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
    st.info(copy["empty_info"])


def render_results(df, origem, copy):
    resumo = resumo_executivo(df)
    df = df.copy()
    df["categoria_trilha"] = df["classificacao_final"].apply(categoria_trilha_risco)
    column_config = build_column_config(copy)

    st.markdown(f'### {copy["panel_title"]}')
    st.caption(f'{copy["source_prefix"]}: {origem}')

    c1, c2, c3 = st.columns(3)
    render_metric(c1, "blue", "XMLs analisados", resumo["total"], "volume processado")
    render_metric(c2, "red", "Reapresentação", resumo["reapresentacao"], "forte indício técnico")
    render_metric(c3, "orange", "Duplicidade", resumo["duplicidade"], "casos técnicos relevantes")

    c4, c5, c6 = st.columns(3)
    render_metric(c4, "gold", "Comportamental", resumo["comportamento"], "padrões suspeitos")
    render_metric(c5, "blue", "Já vistos", resumo["vistos_historico"], "matches no histórico")
    render_metric(c6, "green", "Normais", resumo["normais"], "sem alerta relevante")

    st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)

    a1, a2 = st.columns(2)
    with a1:
        st.markdown(
            f"""
            <div class="panel-card panel-block">
                <div class="summary-title">{copy["summary_title"]}</div>
                <div class="summary-copy">
                    {copy["summary_copy"].format(
                        potencial=resumo["potencial_revisao"],
                        total=resumo["total"],
                        valor=formatar_brl(resumo["valor_em_alerta"]),
                        vistos=resumo["vistos_historico"],
                    )}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with a2:
        distribuicao_alertas = pd.Series(
            {
                "REAPRESENTACAO": resumo["reapresentacao"],
                "DUPLICIDADE": resumo["duplicidade"],
                "SUSPEITO": resumo["comportamento"],
                "NORMAL": resumo["normais"],
            }
        )
        distribuicao_alertas = distribuicao_alertas[distribuicao_alertas > 0]
        max_valor = max(int(distribuicao_alertas.max()), 1) if not distribuicao_alertas.empty else 1
        rows = []
        for categoria, quantidade in distribuicao_alertas.items():
            largura = (int(quantidade) / max_valor) * 100
            rows.append(
                f'<div class="chart-row">'
                f'<div class="chart-label">{categoria}</div>'
                f'<div class="chart-track"><div class="chart-fill" style="width:{largura:.2f}%"></div></div>'
                f'<div class="chart-value">{int(quantidade)}</div>'
                f'</div>'
            )
        st.markdown(
            f'<div class="panel-card panel-block">'
            f'<div class="chart-title">{copy["distribution_title"]}</div>'
            f'<div class="chart-wrap">{"".join(rows)}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="section-gap-lg"></div>', unsafe_allow_html=True)

    r1, r2, r3 = st.columns(3)
    fraude = resumo_categoria(df, "FRAUDE FORTE")
    suspeito = resumo_categoria(df, "SUSPEITO")
    duplicado = resumo_categoria(df, "DUPLICIDADE")
    render_metric(r1, "red", "Valor evitável | fraude", formatar_brl(fraude["valor"]), f'{fraude["quantidade"]} caso(s) críticos')
    render_metric(r2, "gold", "Valor em suspeita", formatar_brl(suspeito["valor"]), f'{suspeito["quantidade"]} caso(s) suspeitos')
    render_metric(r3, "orange", "Valor em duplicidade", formatar_brl(duplicado["valor"]), f'{duplicado["quantidade"]} caso(s) duplicados')

    st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
    st.info(copy["legend"])
    st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)

    t1, t2, t3 = st.columns(3)
    with t1:
        st.markdown("#### Usuários mais recorrentes")
        st.dataframe(df["usuario_envio"].replace("", "Não informado").value_counts().head(5), use_container_width=True)
    with t2:
        st.markdown(f'#### {copy["field_labels"]["top_exposed_title"]}')
        top_prestadores = df["prestador"].replace("", "Não informado").value_counts().head(5)
        top_prestadores.index.name = copy["field_labels"]["prestador"]
        top_prestadores.name = "quantidade"
        st.dataframe(top_prestadores, use_container_width=True)
    with t3:
        st.markdown(f'#### {copy["field_labels"]["top_recurrence_title"]}')
        top_recorrentes = df["paciente"].replace("", "Não informado").value_counts().head(5)
        top_recorrentes.index.name = copy["field_labels"]["paciente"]
        top_recorrentes.name = "quantidade"
        st.dataframe(top_recorrentes, use_container_width=True)

    st.markdown("### Trilha de risco")
    st.caption(copy["risk_caption"])

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
        resumo_cat = resumo_categoria(df, categoria)
        dados_categoria = df[df["categoria_trilha"] == categoria].copy()
        valor_categoria = resumo_cat["valor"]
        quantidade_total = resumo_cat["quantidade"]
        st.markdown(
            f"""
            <div class="risk-strip" style="border-left:6px solid {'#1a4778' if classe == 'red' else '#5d89bf' if classe == 'gold' else '#3e78b8'};">
                <div class="risk-strip-title">{categoria}</div>
                <div class="risk-strip-value">{quantidade_total} caso(s) · {formatar_brl(valor_categoria)}</div>
                <div class="risk-strip-copy">{descricao}.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if not dados_categoria.empty:
            st.caption(f"Lista completa da categoria: {quantidade_total} caso(s).")
            st.dataframe(
                dados_categoria[colunas_trilha].sort_values(by=["score_final", "valor_nf"], ascending=[False, False]),
                column_config=column_config,
                use_container_width=True,
            )

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
        "flag_abuso_servico",
        "flag_crescimento_exponencial",
        "flag_quebra_nf",
        "flag_estetico_camuflado",
        "categoria_trilha",
        "motivo_historico",
        "motivo_tecnico",
        "motivo_comportamental",
    ]
    st.dataframe(df[colunas_top].head(10), column_config=column_config, use_container_width=True)

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
        "flag_abuso_servico",
        "abuso_servico_pct",
        "procedimento_ref_mediana",
        "procedimento_ref_media",
        "flag_crescimento_exponencial",
        "flag_quebra_nf",
        "quebra_nf_fator",
        "valor_referencia_quebra",
        "quebra_nf_gap_pct",
        "flag_estetico_camuflado",
        "flag_crescimento_lote_atual",
        "crescimento_pct",
        "hist_media_qtd_lote",
        "hist_media_valor_lote",
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
        column_config=column_config,
        use_container_width=True,
    )

    csv = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "Baixar relatorio CSV",
        data=csv,
        file_name="resultado_antifraude_nfe.csv",
        mime="text/csv",
    )

if "auth_user" not in st.session_state:
    st.session_state["auth_user"] = None

if not st.session_state["auth_user"]:
    render_login_cover()
    st.stop()

with st.sidebar:
    historico = load_history_stats()
    segmento = st.radio("Segmento da apresentação", list(SEGMENT_COPY.keys()), index=0)
    copy = SEGMENT_COPY[segmento]
    st.markdown("## Sessão")
    st.success(
        f'Conectado como **{st.session_state["auth_user"]["username"]}** ({st.session_state["auth_user"]["role"]})'
    )
    if st.button("Encerrar sessão", use_container_width=True):
        st.session_state["auth_user"] = None
        st.rerun()
    st.markdown("---")
    st.markdown("---")
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
        - último lote processado: **{historico["ultima_analise"]}**
        """
    )

render_hero(copy)
render_pitch(copy)
st.markdown("### Histórico de lotes")
lotes_df = load_batch_history()
if lotes_df.empty:
    st.caption("Nenhum lote registrado ainda.")
else:
    lotes_exibicao = lotes_df.copy()
    lotes_exibicao["valor_total"] = lotes_exibicao["valor_total"].apply(formatar_brl)
    lotes_exibicao["valor_alerta"] = lotes_exibicao["valor_alerta"].apply(formatar_brl)
    st.dataframe(lotes_exibicao, use_container_width=True, hide_index=True)

    opcoes_lote = {
        f'{row["batch_name"]} · {row["created_at"]} · {row["total_documentos"]} XMLs': row["batch_ref"]
        for _, row in lotes_df.iterrows()
    }
    lote_label = st.selectbox("Selecionar lote", list(opcoes_lote.keys()))
    lote_ref = opcoes_lote[lote_label]
    lote_atual = lotes_df[lotes_df["batch_ref"] == lote_ref].iloc[0]
    docs_lote = load_batch_documents(lote_ref)

    st.markdown("#### Detalhe do lote")
    d1, d2, d3, d4 = st.columns(4)
    d1.metric("XMLs", int(lote_atual["total_documentos"]))
    d2.metric("Alertas", int(lote_atual["total_alertas"]))
    d3.metric("Valor total", formatar_brl(float(lote_atual["valor_total"])))
    d4.metric("Valor em alerta", formatar_brl(float(lote_atual["valor_alerta"])))
    st.caption(
        f'Segmento: {lote_atual["segment"]} | Enviado por: {lote_atual["uploaded_by"]} | Referência: {lote_ref}'
    )
    if docs_lote.empty:
        st.caption("Nenhum documento encontrado para este lote.")
    else:
        st.dataframe(
            docs_lote[
                [
                    "arquivo",
                    "paciente",
                    "prestador",
                    "procedimento",
                    "valor_nf",
                    "score_final",
                    "classificacao_final",
                    "motivo_tecnico",
                    "motivo_comportamental",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

uploaded_files = st.file_uploader(
    copy["upload_label"],
    type=["xml"],
    accept_multiple_files=True,
    help=copy["upload_help"],
)

if "analysis_df" not in st.session_state:
    st.session_state["analysis_df"] = pd.DataFrame()
if "analysis_origin" not in st.session_state:
    st.session_state["analysis_origin"] = None

if usar_demo:
    st.session_state["analysis_df"] = processar_arquivos(carregar_demo())
    st.session_state["analysis_origin"] = copy["demo_origin"]
elif uploaded_files:
    st.session_state["analysis_df"] = processar_arquivos(uploaded_files)
    st.session_state["analysis_origin"] = copy["manual_origin"].format(qtd=len(uploaded_files))

df = st.session_state["analysis_df"]
origem = st.session_state["analysis_origin"]

if not df.empty:
    render_results(df, origem, copy)
    if st.button(
        "Registrar este lote no histórico",
        use_container_width=True,
        disabled=st.session_state.get("auth_user") is None,
        help="Disponível para usuários master autenticados.",
    ):
        try:
            salvos = salvar_lote_no_historico(
                df,
                origem,
                segment=segmento,
                uploaded_by=st.session_state["auth_user"]["username"],
            )
            st.success(f"{salvos} documento(s) foram gravados no histórico antifraude.")
            st.rerun()
        except Exception as exc:
            st.error(f"Não foi possível gravar no histórico: {exc}")
else:
    render_empty_state(copy)
