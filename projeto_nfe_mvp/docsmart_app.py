import io
import calendar
import re
from datetime import datetime

import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="DocSmart | Diagnóstico rápido",
    page_icon="assets/docsignal-mark.svg",
    layout="wide",
)


MODULES = {
    "Planilhas": {
        "price": "R$ 600",
        "copy": "Organiza uma base em painel, alertas e resumo executivo.",
        "needs_secondary": False,
        "secondary_label": "",
    },
    "Agenda": {
        "price": "R$ 600",
        "copy": "Transforma vencimentos em agenda de ações e alertas.",
        "needs_secondary": False,
        "secondary_label": "",
    },
    "Pagamentos": {
        "price": "R$ 700",
        "copy": "Cruza NFs/contas a pagar com extrato ou base de pagamentos.",
        "needs_secondary": True,
        "secondary_label": "Extrato ou pagamentos exportados",
    },
    "Cobrança": {
        "price": "R$ 700",
        "copy": "Cruza contas a receber com recebimentos para apontar pendências.",
        "needs_secondary": True,
        "secondary_label": "Recebimentos exportados",
    },
    "Fiscal Assist": {
        "price": "R$ 900",
        "copy": "Organiza entradas e saídas em pacote técnico para validação do contador.",
        "needs_secondary": False,
        "secondary_label": "",
    },
}


STATUS_ORDER = [
    "Não iniciado",
    "Contato feito",
    "Interessado",
    "Amostra solicitada",
    "Proposta enviada",
    "Fechado",
]


def css():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800;900&display=swap');
        html, body, [class*="css"] { font-family: 'Manrope', sans-serif; }
        .stApp {
            background:
                radial-gradient(circle at 82% 8%, rgba(92, 200, 255, 0.18), transparent 28%),
                radial-gradient(circle at 10% 90%, rgba(216, 155, 55, 0.12), transparent 26%),
                linear-gradient(180deg, #f6f9fd 0%, #eef4fb 100%);
        }
        .block-container { padding-top: 1.5rem; padding-bottom: 3rem; max-width: 1500px; }
        .stApp,
        .stApp p,
        .stApp li,
        .stApp label,
        .stApp span,
        .stApp div[data-testid="stMarkdownContainer"] {
            color: #102844;
        }
        .stApp h1,
        .stApp h2,
        .stApp h3,
        .stApp h4,
        .stApp h5,
        .stApp h6,
        .stApp [data-testid="stHeader"],
        .stApp [data-testid="stSubheader"] {
            color: #102844 !important;
        }
        .stApp label,
        .stApp [data-testid="stWidgetLabel"],
        .stApp [data-testid="stCaptionContainer"] {
            color: #334962 !important;
            font-weight: 800;
        }
        section[data-testid="stSidebar"],
        section[data-testid="stSidebar"] > div {
            background: #07111f !important;
        }
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] li,
        section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] {
            color: rgba(248, 251, 255, .78) !important;
        }
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] strong {
            color: #f8fbff !important;
        }
        section[data-testid="stSidebar"] .stButton button {
            color: #f8fbff !important;
            background: rgba(248, 251, 255, .08) !important;
            border: 1px solid rgba(248, 251, 255, .28) !important;
            border-radius: 10px;
        }
        section[data-testid="stSidebar"] .stButton button:hover {
            background: rgba(92, 200, 255, .16) !important;
            border-color: rgba(92, 200, 255, .42) !important;
        }
        .hero {
            background:
                linear-gradient(135deg, rgba(7, 17, 31, 0.98), rgba(16, 40, 68, 0.95)),
                radial-gradient(circle at 82% 20%, rgba(92, 200, 255, 0.24), transparent 30%);
            color: #f8fbff;
            border-radius: 18px;
            padding: 30px 32px;
            box-shadow: 0 22px 70px rgba(7, 17, 31, 0.16);
            margin-bottom: 20px;
        }
        .hero small {
            color: #5cc8ff;
            font-weight: 900;
            letter-spacing: .08em;
            text-transform: uppercase;
        }
        .hero-title {
            color: #f8fbff !important;
            margin: 10px 0 8px;
            font-size: clamp(2.4rem, 5vw, 4.8rem);
            font-weight: 950;
            line-height: .95;
            letter-spacing: 0;
            text-shadow: 0 2px 18px rgba(0, 0, 0, .26);
        }
        .hero-title * { color: #f8fbff !important; }
        .hero p { color: rgba(248, 251, 255, .80) !important; max-width: 900px; font-size: 1.08rem; }
        .hero small { color: #5cc8ff !important; }
        .home-hero {
            min-height: 520px;
            display: grid;
            grid-template-columns: minmax(0, 1.05fr) minmax(360px, .95fr);
            gap: 34px;
            align-items: center;
            background:
                linear-gradient(135deg, rgba(7, 17, 31, 0.98), rgba(16, 40, 68, 0.95)),
                radial-gradient(circle at 82% 18%, rgba(92, 200, 255, 0.24), transparent 32%),
                radial-gradient(circle at 80% 90%, rgba(216, 155, 55, 0.16), transparent 30%);
            border-radius: 18px;
            padding: 38px;
            box-shadow: 0 22px 70px rgba(7, 17, 31, 0.16);
            margin-bottom: 22px;
        }
        .home-hero small {
            color: #5cc8ff !important;
            font-weight: 900;
            letter-spacing: .08em;
            text-transform: uppercase;
        }
        .home-title {
            color: #f8fbff !important;
            text-shadow: 0 2px 18px rgba(0, 0, 0, .28);
            font-size: clamp(3rem, 6vw, 6.2rem);
            font-weight: 950;
            line-height: .92;
            margin: 14px 0 18px;
            letter-spacing: 0;
        }
        .home-hero p {
            color: rgba(248, 251, 255, .82) !important;
            font-size: 1.12rem;
            max-width: 760px;
        }
        .home-panel {
            background: rgba(248, 251, 255, 0.10);
            border: 1px solid rgba(248, 251, 255, 0.16);
            border-radius: 14px;
            padding: 22px;
        }
        .home-row {
            display: grid;
            grid-template-columns: 1fr auto;
            gap: 12px;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid rgba(248, 251, 255, 0.12);
        }
        .home-row:last-child { border-bottom: 0; }
        .home-row strong { color: #f8fbff; }
        .home-row span { color: rgba(248, 251, 255, .70) !important; font-weight: 800; }
        .home-hero div[data-testid="stMarkdownContainer"],
        .home-hero div[data-testid="stMarkdownContainer"] *,
        .home-title,
        .home-title *,
        .home-hero p,
        .home-hero strong {
            color: #f8fbff !important;
        }
        .home-hero small {
            color: #5cc8ff !important;
        }
        .home-steps {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 12px;
            margin: 16px 0 24px;
        }
        .home-step {
            background: #fff;
            border: 1px solid rgba(16, 40, 68, 0.12);
            border-radius: 12px;
            padding: 18px;
            min-height: 128px;
            box-shadow: 0 12px 34px rgba(7, 17, 31, 0.06);
        }
        .home-step strong { display:block; color:#102844; margin-bottom:8px; }
        .home-step span { color:#64758c; }
        .metric {
            border-radius: 14px;
            padding: 18px;
            background: #fff;
            border: 1px solid rgba(16, 40, 68, 0.12);
            box-shadow: 0 12px 36px rgba(7, 17, 31, 0.07);
            min-height: 118px;
        }
        .metric span { color: #64758c; font-size: .86rem; font-weight: 800; text-transform: uppercase; }
        .metric strong { display:block; color:#102844; font-size:2rem; margin-top:8px; }
        .insight-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 12px;
            margin: 16px 0 20px;
        }
        .insight-card {
            background: #fff;
            border: 1px solid rgba(16, 40, 68, 0.12);
            border-top: 5px solid #2f73c6;
            border-radius: 12px;
            padding: 16px;
            min-height: 132px;
            box-shadow: 0 12px 34px rgba(7, 17, 31, 0.06);
        }
        .insight-card.warning { border-top-color: #d89b37; }
        .insight-card.danger { border-top-color: #d9534f; }
        .insight-card strong { display:block; color:#102844; margin-bottom: 8px; }
        .insight-card span { color:#64758c; font-size:.92rem; line-height:1.35; }
        div[data-testid="stTabs"] {
            background: #ffffff;
            border: 1px solid rgba(16, 40, 68, 0.14);
            border-radius: 14px;
            padding: 10px 12px 14px;
            box-shadow: 0 12px 34px rgba(7, 17, 31, 0.06);
            margin-top: 14px;
        }
        div[data-testid="stTabs"] div[role="tablist"] {
            gap: 8px;
            background: #e9f2fb;
            border: 1px solid rgba(16, 40, 68, 0.10);
            border-radius: 12px;
            padding: 7px;
            margin-bottom: 12px;
        }
        div[data-testid="stTabs"] button[role="tab"] {
            min-height: 42px;
            border-radius: 9px;
            padding: 8px 14px;
            color: #102844;
            font-weight: 900;
            background: transparent;
            border: 1px solid transparent;
        }
        div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
            background: #102844;
            color: #f8fbff;
            border-color: #102844;
            box-shadow: 0 8px 22px rgba(16, 40, 68, 0.22);
        }
        div[data-testid="stTabs"] button[role="tab"][aria-selected="false"]:hover {
            background: rgba(47, 115, 198, 0.10);
            border-color: rgba(47, 115, 198, 0.18);
        }
        div[data-testid="stTabs"] div[data-testid="stMarkdownContainer"] h3 {
            color: #102844;
        }
        .note {
            border-left: 5px solid #d89b37;
            background: #fff8e8;
            color: #503a10;
            padding: 14px 16px;
            border-radius: 8px;
            margin: 12px 0;
        }
        .module-card {
            background: #fff;
            border: 1px solid rgba(16, 40, 68, 0.14);
            border-radius: 12px;
            padding: 14px;
            min-height: 150px;
        }
        .module-card strong { color:#102844; font-size: 1.05rem; }
        .module-card p { color:#64758c; margin: 8px 0 0; }
        .module-card em { color:#2f73c6; font-style: normal; font-weight: 900; }
        .monthly-module-card {
            background: #102844;
            border: 1px solid rgba(92, 200, 255, 0.24);
            border-radius: 12px;
            padding: 18px 20px;
            margin: 14px 0 4px;
            display: grid;
            grid-template-columns: 1fr auto;
            gap: 16px;
            align-items: center;
            box-shadow: 0 14px 42px rgba(7, 17, 31, 0.10);
        }
        .monthly-module-card strong { color:#f8fbff; display:block; font-size:1.08rem; }
        .monthly-module-card p { color:rgba(248, 251, 255, .76) !important; margin: 6px 0 0; }
        .monthly-module-card em { color:#5cc8ff; font-style: normal; font-weight: 950; white-space: nowrap; }
        .calendar-wrap {
            background: #fff;
            border: 1px solid rgba(16, 40, 68, 0.14);
            border-radius: 14px;
            padding: 18px;
            box-shadow: 0 12px 36px rgba(7, 17, 31, 0.07);
            margin: 12px 0 18px;
            overflow-x: auto;
        }
        .calendar-title {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
            margin-bottom: 12px;
        }
        .calendar-title strong { color: #102844; font-size: 1.25rem; }
        .calendar-title span { color: #64758c; font-weight: 800; font-size: .9rem; }
        .calendar-grid {
            display: grid;
            grid-template-columns: repeat(7, 142px);
            gap: 10px;
            width: max-content;
            min-width: 100%;
        }
        .calendar-head {
            color: #64758c;
            font-size: .76rem;
            font-weight: 900;
            text-transform: uppercase;
            letter-spacing: .06em;
            padding: 4px 6px;
        }
        .day-cell {
            width: 142px;
            height: 142px;
            border: 1px solid rgba(16, 40, 68, 0.12);
            border-radius: 10px;
            background: #f8fbff;
            padding: 9px;
            overflow: hidden;
        }
        .day-cell.empty { background: transparent; border-color: transparent; }
        .day-number {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 26px;
            height: 26px;
            border-radius: 50%;
            background: #e9f2fb;
            color: #102844;
            font-weight: 950;
            font-size: .85rem;
            margin-bottom: 6px;
        }
        .event {
            border-radius: 7px;
            padding: 5px 7px;
            margin-top: 5px;
            color: #102844;
            font-size: .71rem;
            line-height: 1.2;
            border: 1px solid rgba(16, 40, 68, 0.08);
        }
        .event strong {
            display: block;
            font-size: .70rem;
            margin-bottom: 2px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .event-title {
            display: block;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .event.receive { background: #e9f8f1; border-left: 4px solid #4fa37b; }
        .event.pay { background: #fff4e2; border-left: 4px solid #d89b37; }
        .event.overdue { background: #ffecec; border-left-color: #d9534f; }
        .event.today { box-shadow: inset 0 0 0 2px rgba(47, 115, 198, .32); }
        .event small {
            display: block;
            color: #64758c;
            margin-top: 2px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        @media (max-width: 900px) {
            .insight-grid { grid-template-columns: 1fr; }
            .home-hero { grid-template-columns: 1fr; padding: 26px; }
            .home-steps { grid-template-columns: 1fr; }
            .monthly-module-card { grid-template-columns: 1fr; }
            .calendar-grid { grid-template-columns: repeat(7, 132px); }
            .day-cell { width: 132px; height: 132px; }
            .calendar-head { display: none; }
            .day-cell.empty { display: none; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def normalize_name(value):
    text = str(value or "").strip().lower()
    text = re.sub(r"[áàãâä]", "a", text)
    text = re.sub(r"[éèêë]", "e", text)
    text = re.sub(r"[íìîï]", "i", text)
    text = re.sub(r"[óòõôö]", "o", text)
    text = re.sub(r"[úùûü]", "u", text)
    text = re.sub(r"ç", "c", text)
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_")


def read_upload(uploaded):
    if uploaded is None:
        return pd.DataFrame()
    name = uploaded.name.lower()
    if name.endswith(".csv"):
        raw = uploaded.getvalue()
        for sep in [",", ";", "\t"]:
            try:
                df = pd.read_csv(io.BytesIO(raw), sep=sep)
                if df.shape[1] > 1:
                    return df
            except Exception:
                pass
        return pd.read_csv(io.BytesIO(raw))
    return pd.read_excel(uploaded)


def clean_df(df):
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    df = df.dropna(how="all")
    return df


def find_col(df, keywords):
    normalized = {col: normalize_name(col) for col in df.columns}
    for col, norm in normalized.items():
        if any(k in norm for k in keywords):
            return col
    return None


def infer_columns(df):
    return {
        "documento": find_col(df, ["doc", "nf", "nota", "numero", "titulo", "fatura"]),
        "fornecedor": find_col(df, ["fornecedor", "cliente", "prestador", "razao", "nome", "favorecido"]),
        "valor": find_col(df, ["valor", "total", "preco", "montante", "vlr"]),
        "data": find_col(df, ["data", "emissao", "venc", "pagamento", "recebimento", "competencia"]),
        "status": find_col(df, ["status", "situacao", "baixado", "pago", "recebido"]),
        "descricao": find_col(df, ["descricao", "historico", "item", "produto", "servico", "observacao"]),
        "tipo": find_col(df, ["tipo", "entrada", "saida", "movimento", "natureza"]),
        "categoria": find_col(df, ["categoria", "grupo", "classificacao", "centro", "conta"]),
        "cnpj": find_col(df, ["cnpj", "cpf", "documento_fiscal"]),
        "competencia": find_col(df, ["competencia", "mes", "periodo", "referencia"]),
    }


def to_number(series):
    if series is None:
        return pd.Series(dtype="float64")
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce")
    cleaned = (
        series.astype(str)
        .str.replace(r"R\$", "", regex=True)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.replace(r"[^0-9\-.]", "", regex=True)
    )
    return pd.to_numeric(cleaned, errors="coerce")


def to_date(series):
    if series is None:
        return pd.Series(dtype="datetime64[ns]")
    return pd.to_datetime(series, errors="coerce", dayfirst=True)


def currency(value):
    try:
        return f"R$ {float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def metric_grid(metrics):
    cols = st.columns(len(metrics))
    for col, (label, value) in zip(cols, metrics):
        col.markdown(
            f'<div class="metric"><span>{label}</span><strong>{value}</strong></div>',
            unsafe_allow_html=True,
        )


def insight_grid(insights):
    html = ['<div class="insight-grid">']
    for title, copy, tone in insights:
        html.append(f'<div class="insight-card {tone}"><strong>{title}</strong><span>{copy}</span></div>')
    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)


def build_excel(sheets):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for name, df in sheets.items():
            safe_name = name[:31]
            df.to_excel(writer, index=False, sheet_name=safe_name)
            ws = writer.book[safe_name]
            for cell in ws[1]:
                cell.font = cell.font.copy(bold=True, color="FFFFFF")
                cell.fill = cell.fill.copy(fill_type="solid", fgColor="102844")
            for column_cells in ws.columns:
                max_len = max(len(str(cell.value or "")) for cell in column_cells)
                ws.column_dimensions[column_cells[0].column_letter].width = min(max(max_len + 2, 12), 42)
    output.seek(0)
    return output.getvalue()


def summarize_planilhas(df, cols):
    valor = to_number(df[cols["valor"]]) if cols["valor"] else pd.Series([0] * len(df))
    fornecedor = df[cols["fornecedor"]].astype(str) if cols["fornecedor"] else pd.Series(["Sem fornecedor"] * len(df))
    documento = df[cols["documento"]].astype(str) if cols["documento"] else pd.Series([""] * len(df))
    datas = to_date(df[cols["data"]]) if cols["data"] else pd.Series([pd.NaT] * len(df))
    descricao = df[cols["descricao"]].astype(str) if cols["descricao"] else pd.Series([""] * len(df))

    result = df.copy()
    result["_valor_detectado"] = valor
    result["_chave_documento"] = documento.str.strip().str.lower()
    result["_fornecedor_detectado"] = fornecedor
    result["_data_detectada"] = datas
    result["_dia_mes"] = datas.dt.day
    result["_semana_mes"] = ((datas.dt.day.sub(1) // 7) + 1).where(datas.notna(), pd.NA)
    result["_faixa_mes"] = "Sem data"
    result.loc[result["_dia_mes"].between(1, 10, inclusive="both"), "_faixa_mes"] = "Início do mês"
    result.loc[result["_dia_mes"].between(11, 20, inclusive="both"), "_faixa_mes"] = "Meio do mês"
    result.loc[result["_dia_mes"].between(21, 31, inclusive="both"), "_faixa_mes"] = "Fim do mês"
    result["_score_atencao"] = 20
    result["_alerta"] = "Revisar"
    result["_motivos"] = ""

    duplicate_mask = result["_chave_documento"].duplicated(keep=False) & result["_chave_documento"].ne("")
    result.loc[duplicate_mask, "_score_atencao"] += 45
    result.loc[duplicate_mask, "_motivos"] += "Documento repetido; "

    if valor.notna().any():
        threshold = valor.quantile(0.9)
        high_mask = valor >= threshold
        result.loc[high_mask, "_score_atencao"] += 25
        result.loc[high_mask, "_motivos"] += "Valor no topo da base; "

    recurring = fornecedor.map(fornecedor.value_counts()) >= 2
    result.loc[recurring, "_score_atencao"] += 10
    result.loc[recurring, "_motivos"] += "Fornecedor/cliente recorrente; "

    if cols["descricao"]:
        desc_key = descricao.str.strip().str.lower()
        repeated_desc = desc_key.duplicated(keep=False) & desc_key.ne("")
        result.loc[repeated_desc, "_score_atencao"] += 10
        result.loc[repeated_desc, "_motivos"] += "Descrição recorrente; "

    result["_score_atencao"] = result["_score_atencao"].clip(upper=100)
    result["_motivos"] = result["_motivos"].str.strip().str.rstrip(";").replace("", "Sem alerta crítico")
    result["_alerta"] = "Baixo"
    result.loc[result["_score_atencao"] >= 45, "_alerta"] = "Médio"
    result.loc[result["_score_atencao"] >= 70, "_alerta"] = "Alto"

    top = (
        pd.DataFrame({"Nome": fornecedor, "Valor": valor})
        .groupby("Nome", dropna=False)["Valor"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
    )
    alerts = result[result["_alerta"].isin(["Alto", "Médio"])].sort_values(["_score_atencao", "_valor_detectado"], ascending=[False, False]).copy()
    monthly = (
        pd.DataFrame({"Mês": datas.dt.to_period("M").astype(str), "Valor": valor})
        .dropna(subset=["Valor"])
        .groupby("Mês", dropna=False)["Valor"]
        .sum()
        .reset_index()
        .sort_values("Mês")
    )
    seasonality = (
        result[result["_data_detectada"].notna()]
        .groupby(["_faixa_mes"], dropna=False)
        .agg(Quantidade=("_faixa_mes", "size"), Valor=("_valor_detectado", "sum"))
        .reset_index()
        .rename(columns={"_faixa_mes": "Faixa do mês"})
    )
    order = {"Início do mês": 1, "Meio do mês": 2, "Fim do mês": 3, "Sem data": 4}
    seasonality["_ordem"] = seasonality["Faixa do mês"].map(order).fillna(9)
    seasonality = seasonality.sort_values("_ordem").drop(columns=["_ordem"])
    weekly = (
        result[result["_data_detectada"].notna()]
        .assign(
            Mês=result["_data_detectada"].dt.to_period("M").astype(str),
            Semana=result["_semana_mes"].astype("Int64").astype(str).radd("Semana "),
        )
        .groupby(["Mês", "Semana"], dropna=False)
        .agg(Quantidade=("_semana_mes", "size"), Valor=("_valor_detectado", "sum"))
        .reset_index()
        .sort_values(["Mês", "Semana"])
    )
    peak_week = weekly.sort_values("Valor", ascending=False).head(1)
    alert_summary = (
        result.groupby("_alerta", dropna=False)
        .agg(Quantidade=("_alerta", "size"), Valor=("_valor_detectado", "sum"))
        .reset_index()
        .sort_values("Quantidade", ascending=False)
    )
    metrics = [
        ("Linhas analisadas", f"{len(df):,}".replace(",", ".")),
        ("Valor total", currency(valor.sum())),
        ("Score médio", f"{result['_score_atencao'].mean():.0f}"),
        ("Pico semanal", currency(peak_week.iloc[0]["Valor"]) if not peak_week.empty else "R$ 0,00"),
    ]
    insights = [
        ("Prioridade de revisão", f"{len(alerts)} linha(s) com score médio/alto. Comece por valores altos e documentos repetidos.", "danger" if len(alerts) else ""),
        ("Concentração", f"Maior concentração em {top.iloc[0]['Nome']} com {currency(top.iloc[0]['Valor'])}." if not top.empty else "Sem concentração detectada.", "warning"),
        ("Sazonalidade", f"Maior pico em {peak_week.iloc[0]['Mês']} · {peak_week.iloc[0]['Semana']} com {currency(peak_week.iloc[0]['Valor'])}." if not peak_week.empty else "Sem datas suficientes para sazonalidade.", "warning"),
    ]
    return metrics, result, alerts, top, monthly, alert_summary, seasonality, weekly, insights


def match_by_doc_or_value(base, secondary, base_cols, secondary_cols, paid_label):
    result = base.copy()
    base_doc = result[base_cols["documento"]].astype(str).str.strip().str.lower() if base_cols["documento"] else pd.Series([""] * len(result))
    base_val = to_number(result[base_cols["valor"]]) if base_cols["valor"] else pd.Series([None] * len(result))
    base_date = to_date(result[base_cols["data"]]) if base_cols["data"] else pd.Series([pd.NaT] * len(result))
    base_name = result[base_cols["fornecedor"]].astype(str) if base_cols["fornecedor"] else pd.Series(["Sem nome"] * len(result))

    sec_doc = secondary[secondary_cols["documento"]].astype(str).str.strip().str.lower() if secondary_cols["documento"] else pd.Series([""] * len(secondary))
    sec_val = to_number(secondary[secondary_cols["valor"]]) if secondary_cols["valor"] else pd.Series([None] * len(secondary))
    sec_values_by_doc = {}
    if secondary_cols["documento"]:
        sec_tmp = pd.DataFrame({"doc": sec_doc, "valor": sec_val}).dropna(subset=["valor"])
        sec_values_by_doc = sec_tmp.groupby("doc")["valor"].sum().to_dict()

    sec_docs = set(sec_doc[sec_doc.ne("")])
    rounded_values = set(sec_val.dropna().round(2))

    status = []
    divergences = []
    for doc, val in zip(base_doc, base_val):
        paid_value = sec_values_by_doc.get(doc, None)
        if doc and paid_value is not None and pd.notna(val) and abs(float(paid_value) - float(val)) > 0.01:
            status.append("Divergência de valor")
            divergences.append(float(val) - float(paid_value))
        elif doc and doc in sec_docs:
            status.append(paid_label)
            divergences.append(0)
        elif pd.notna(val) and round(float(val), 2) in rounded_values:
            status.append(f"{paid_label} por valor")
            divergences.append(0)
        else:
            status.append("Pendente")
            divergences.append(float(val) if pd.notna(val) else 0)
    result["_status_docsmart"] = status
    result["_valor_detectado"] = base_val
    result["_data_detectada"] = base_date
    result["_nome_detectado"] = base_name
    result["_diferenca_detectada"] = divergences
    result["_score_atencao"] = 20
    result.loc[result["_status_docsmart"].eq("Pendente"), "_score_atencao"] += 45
    result.loc[result["_status_docsmart"].eq("Divergência de valor"), "_score_atencao"] += 35
    result.loc[base_doc.duplicated(keep=False) & base_doc.ne(""), "_score_atencao"] += 20
    if base_val.notna().any():
        result.loc[base_val >= base_val.quantile(0.85), "_score_atencao"] += 15
    result["_score_atencao"] = result["_score_atencao"].clip(upper=100)
    result["_prioridade"] = "Baixa"
    result.loc[result["_score_atencao"] >= 45, "_prioridade"] = "Média"
    result.loc[result["_score_atencao"] >= 70, "_prioridade"] = "Alta"
    result["_motivo"] = result["_status_docsmart"]
    result.loc[base_doc.duplicated(keep=False) & base_doc.ne(""), "_motivo"] += "; documento repetido"
    pending = result[result["_status_docsmart"].isin(["Pendente", "Divergência de valor"])].sort_values(["_score_atencao", "_valor_detectado"], ascending=[False, False]).copy()
    top = (
        pd.DataFrame({"Nome": base_name, "Valor": base_val})
        .groupby("Nome", dropna=False)["Valor"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
    )
    status_summary = (
        result.groupby("_status_docsmart", dropna=False)
        .agg(Quantidade=("_status_docsmart", "size"), Valor=("_valor_detectado", "sum"))
        .reset_index()
        .sort_values("Valor", ascending=False)
    )
    month = base_date.dt.to_period("M").astype(str)
    monthly = (
        pd.DataFrame({"Mês": month, "Status": result["_status_docsmart"], "Valor": base_val})
        .dropna(subset=["Valor"])
        .groupby(["Mês", "Status"], dropna=False)["Valor"]
        .sum()
        .reset_index()
        .sort_values(["Mês", "Status"])
    )
    week = ((base_date.dt.day.sub(1) // 7) + 1).where(base_date.notna(), pd.NA)
    weekly = (
        pd.DataFrame({"Mês": month, "Semana": week.astype("Int64").astype(str).radd("Semana "), "Valor": base_val})
        .dropna(subset=["Valor"])
        .groupby(["Mês", "Semana"], dropna=False)["Valor"]
        .sum()
        .reset_index()
        .sort_values(["Mês", "Semana"])
    )
    pending_value = pending["_valor_detectado"].sum()
    paid_count = result["_status_docsmart"].str.contains(paid_label, regex=False).sum()
    peak_name = top.iloc[0]["Nome"] if not top.empty else "sem concentração"
    peak_value = currency(top.iloc[0]["Valor"]) if not top.empty else "R$ 0,00"
    metrics = [
        ("Linhas base", f"{len(base):,}".replace(",", ".")),
        ("Localizados", str(paid_count)),
        ("Valor pendente", currency(pending["_valor_detectado"].sum())),
        ("Score médio", f"{result['_score_atencao'].mean():.0f}"),
    ]
    insights = [
        ("Prioridade financeira", f"{len(pending)} item(ns) exigem ação, somando {currency(pending_value)}.", "danger" if len(pending) else ""),
        ("Concentração", f"Maior concentração em {peak_name}, com {peak_value}.", "warning"),
        ("Próximo passo", "Validar pendências de maior score, confirmar divergências e decidir se o acompanhamento deve virar mensal.", ""),
    ]
    return metrics, result, pending, top, status_summary, monthly, weekly, insights


def summarize_agenda(df, cols):
    result = df.copy()
    date_col = cols["data"]
    value_col = cols["valor"]
    dates = to_date(result[date_col]) if date_col else pd.Series([pd.NaT] * len(result))
    values = to_number(result[value_col]) if value_col else pd.Series([0] * len(result))
    today = pd.Timestamp(datetime.today().date())
    days = (dates - today).dt.days

    result["_data_detectada"] = dates
    result["_valor_detectado"] = values
    result["_dias_para_vencer"] = days
    result["_faixa"] = "Sem data"
    result.loc[days < 0, "_faixa"] = "Vencido"
    result.loc[days == 0, "_faixa"] = "Vence hoje"
    result.loc[(days > 0) & (days <= 7), "_faixa"] = "Próximos 7 dias"
    result.loc[days > 7, "_faixa"] = "Futuro"
    result["_prioridade"] = result["_faixa"].map({
        "Vencido": "Alta",
        "Vence hoje": "Alta",
        "Próximos 7 dias": "Média",
        "Futuro": "Baixa",
        "Sem data": "Revisar",
    })

    agenda = result[result["_prioridade"].isin(["Alta", "Média"])].sort_values("_dias_para_vencer")
    by_day = (
        pd.DataFrame({"Data": dates, "Valor": values, "Faixa": result["_faixa"]})
        .dropna(subset=["Data"])
        .groupby(["Data", "Faixa"], dropna=False)["Valor"]
        .sum()
        .reset_index()
        .sort_values("Data")
    )
    metrics = [
        ("Linhas analisadas", f"{len(df):,}".replace(",", ".")),
        ("Vencidos", str((result["_faixa"] == "Vencido").sum())),
        ("Vence hoje", str((result["_faixa"] == "Vence hoje").sum())),
        ("Próximos 7 dias", str((result["_faixa"] == "Próximos 7 dias").sum())),
    ]
    return metrics, result, agenda, by_day


def summarize_fiscal_assist(df, cols, accountant):
    result = df.copy()
    value_col = cols["valor"]
    date_col = cols["data"] or cols["competencia"]
    type_col = cols["tipo"]
    category_col = cols["categoria"] or cols["descricao"]
    name_col = cols["fornecedor"]
    doc_col = cols["documento"]
    cnpj_col = cols["cnpj"]

    values = to_number(result[value_col]) if value_col else pd.Series([0] * len(result))
    dates = to_date(result[date_col]) if date_col else pd.Series([pd.NaT] * len(result))
    movement = result[type_col].astype(str) if type_col else pd.Series(["Não informado"] * len(result))
    category = result[category_col].astype(str) if category_col else pd.Series(["Sem classificação"] * len(result))
    names = result[name_col].astype(str) if name_col else pd.Series(["Sem nome"] * len(result))
    docs = result[doc_col].astype(str) if doc_col else pd.Series([""] * len(result))
    cnpjs = result[cnpj_col].astype(str) if cnpj_col else pd.Series([""] * len(result))

    normalized_movement = movement.str.lower()
    result["_tipo_docsmart"] = "Revisar"
    result.loc[normalized_movement.str.contains("entrada|compra|despesa|pagar|fornecedor", regex=True, na=False), "_tipo_docsmart"] = "Entrada/Despesa"
    result.loc[normalized_movement.str.contains("saida|saída|venda|receita|receber|cliente", regex=True, na=False), "_tipo_docsmart"] = "Saída/Receita"
    result["_valor_detectado"] = values
    result["_data_detectada"] = dates
    result["_competencia"] = dates.dt.to_period("M").astype(str).replace("NaT", "Sem competência")
    result["_categoria_sugerida"] = category.where(category.str.strip().ne(""), "Sem classificação")
    result["_nome_detectado"] = names
    result["_documento_detectado"] = docs
    result["_cnpj_detectado"] = cnpjs
    result["_ponto_validacao"] = "Conferir classificação com contador"
    result.loc[result["_categoria_sugerida"].eq("Sem classificação"), "_ponto_validacao"] = "Sem classificação sugerida"
    result.loc[result["_data_detectada"].isna(), "_ponto_validacao"] = "Sem data/competência detectada"
    result.loc[result["_valor_detectado"].isna(), "_ponto_validacao"] = "Sem valor detectado"
    result.loc[result["_cnpj_detectado"].str.strip().isin(["", "nan", "None"]), "_ponto_validacao"] = "Sem CNPJ/CPF detectado"
    result.loc[result["_tipo_docsmart"].eq("Revisar"), "_ponto_validacao"] = "Tipo de movimento não identificado"

    summary = (
        result.groupby(["_competencia", "_tipo_docsmart"], dropna=False)
        .agg(Quantidade=("_tipo_docsmart", "size"), Valor=("_valor_detectado", "sum"))
        .reset_index()
        .rename(columns={"_competencia": "Competência", "_tipo_docsmart": "Tipo"})
        .sort_values(["Competência", "Tipo"])
    )
    by_category = (
        result.groupby(["_categoria_sugerida", "_tipo_docsmart"], dropna=False)
        .agg(Quantidade=("_categoria_sugerida", "size"), Valor=("_valor_detectado", "sum"))
        .reset_index()
        .rename(columns={"_categoria_sugerida": "Categoria sugerida", "_tipo_docsmart": "Tipo"})
        .sort_values("Valor", ascending=False)
    )
    validation = result[
        result["_ponto_validacao"].ne("Conferir classificação com contador")
    ].sort_values(["_ponto_validacao", "_valor_detectado"], ascending=[True, False])
    protocol = pd.DataFrame(
        [
            ["Empresa analisada", accountant.get("empresa") or "Não informado"],
            ["Período de competência", accountant.get("periodo") or "Não informado"],
            ["Contador/escritório informado", accountant.get("contador") or "Não informado"],
            ["CRC informado", accountant.get("crc") or "Não informado"],
            ["E-mail contábil", accountant.get("email") or "Não informado"],
            ["Data de geração", datetime.now().strftime("%d/%m/%Y %H:%M")],
            ["Finalidade", "Organização documental e relatório técnico para validação contábil profissional"],
            ["Limite de uso", "Não calcula tributo, não apura imposto e não substitui contador habilitado"],
        ],
        columns=["Campo", "Informação"],
    )

    missing = len(validation)
    entradas = result[result["_tipo_docsmart"].eq("Entrada/Despesa")]["_valor_detectado"].sum()
    saidas = result[result["_tipo_docsmart"].eq("Saída/Receita")]["_valor_detectado"].sum()
    metrics = [
        ("Linhas analisadas", f"{len(df):,}".replace(",", ".")),
        ("Entradas/despesas", currency(entradas)),
        ("Saídas/receitas", currency(saidas)),
        ("Itens para validar", str(missing)),
    ]
    insights = [
        ("Pacote para contador", "Exportação condicionada ao responsável contábil informado com CRC e e-mail.", ""),
        ("Pontos de validação", f"{missing} item(ns) precisam de revisão antes de qualquer uso contábil.", "warning" if missing else ""),
        ("Limite técnico", "O relatório organiza dados. Apuração fiscal e decisão tributária seguem com o contador.", "danger"),
    ]
    return metrics, result, summary, by_category, validation, protocol, insights


def render_modules():
    cols = st.columns(len(MODULES))
    for col, (name, cfg) in zip(cols, MODULES.items()):
        col.markdown(
            f"""
            <div class="module-card">
              <strong>{name}</strong><br>
              <em>{cfg["price"]}</em>
              <p>{cfg["copy"]}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown(
        """
        <div class="monthly-module-card">
          <div>
            <strong>DocSmart Mensal</strong>
            <p>Acompanhamento mensal de um ou mais módulos, por volume de linhas e rotina de devolutiva.</p>
          </div>
          <em>a partir de R$ 900/mês</em>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_agenda_calendar(treated):
    if treated.empty or "_data_detectada" not in treated.columns:
        st.info("Não encontrei datas suficientes para montar o calendário.")
        return

    dated = treated.dropna(subset=["_data_detectada"]).copy()
    if dated.empty:
        st.info("Não encontrei datas válidas para montar o calendário.")
        return

    dated["_data_detectada"] = pd.to_datetime(dated["_data_detectada"], errors="coerce")
    dated = dated.dropna(subset=["_data_detectada"])
    ref_date = dated["_data_detectada"].min()
    year = int(ref_date.year)
    month = int(ref_date.month)
    month_name = ref_date.strftime("%B/%Y").capitalize()
    weeks = calendar.Calendar(firstweekday=0).monthdayscalendar(year, month)

    inferred = infer_columns(dated)
    type_col = "Tipo" if "Tipo" in dated.columns else None
    name_col = "Nome" if "Nome" in dated.columns else inferred.get("fornecedor")
    doc_col = inferred.get("documento")
    today = pd.Timestamp(datetime.today().date())

    html = [
        '<div class="calendar-wrap">',
        '<div class="calendar-title">',
        f"<strong>Agenda financeira · {month_name}</strong>",
        "<span>Receber, pagar e vencimentos em uma visão de mês</span>",
        "</div>",
        '<div class="calendar-grid">',
    ]
    for label in ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]:
        html.append(f'<div class="calendar-head">{label}</div>')

    for week in weeks:
        for day in week:
            if day == 0:
                html.append('<div class="day-cell empty"></div>')
                continue
            day_date = pd.Timestamp(year=year, month=month, day=day)
            events = dated[dated["_data_detectada"].dt.date == day_date.date()]
            html.append('<div class="day-cell">')
            html.append(f'<div class="day-number">{day}</div>')
            for _, event in events.head(4).iterrows():
                event_type = str(event.get(type_col, "Evento")) if type_col else "Evento"
                event_class = "receive" if "receber" in event_type.lower() else "pay" if "pagar" in event_type.lower() else "receive"
                if event.get("_faixa") == "Vencido":
                    event_class += " overdue"
                if day_date.date() == today.date():
                    event_class += " today"
                title = str(event.get(name_col, event_type))[:34] if name_col else event_type
                doc = str(event.get(doc_col, ""))[:22] if doc_col else ""
                value = currency(event.get("_valor_detectado", 0))
                faixa = str(event.get("_faixa", ""))
                html.append(f'<div class="event {event_class}">')
                html.append(f"<strong>{event_type} · {value}</strong>")
                html.append(f'<span class="event-title">{title}</span>')
                detail = " · ".join(part for part in [doc, faixa] if part)
                if detail:
                    html.append(f"<small>{detail}</small>")
                html.append("</div>")
            if len(events) > 4:
                html.append(f'<div class="event"><strong>+{len(events) - 4} itens</strong>Ver tabela de ações</div>')
            html.append("</div>")
    html.append("</div></div>")
    st.markdown("".join(html), unsafe_allow_html=True)


def demo_data(module):
    base = pd.DataFrame()
    secondary = pd.DataFrame()
    if module == "Planilhas":
        base = pd.DataFrame(
            [
                ["NF-1001", "Fornecedor Atlas", "01/03/2026", "Peças manutenção", "1.250,00", "Manutenção"],
                ["NF-1002", "Beta Serviços", "03/03/2026", "Serviço técnico", "3.800,00", "Serviços"],
                ["NF-1003", "Cromo Materiais", "08/03/2026", "Materiais operação", "890,00", "Compras"],
                ["NF-1004", "Delta Logística", "11/03/2026", "Frete mensal", "7.450,00", "Logística"],
                ["NF-1005", "Fornecedor Atlas", "15/03/2026", "Peças manutenção", "1.120,00", "Manutenção"],
                ["NF-1006", "Omega Facilities", "18/03/2026", "Limpeza", "2.250,00", "Facilities"],
                ["NF-1007", "Norte Tecnologia", "21/03/2026", "Licença mensal", "980,00", "Tecnologia"],
                ["NF-1008", "Delta Logística", "02/04/2026", "Frete mensal", "7.980,00", "Logística"],
                ["NF-1009", "Beta Serviços", "05/04/2026", "Serviço técnico", "3.950,00", "Serviços"],
                ["NF-1010", "Fornecedor Atlas", "08/04/2026", "Peças manutenção", "1.460,00", "Manutenção"],
                ["NF-1011", "Cromo Materiais", "12/04/2026", "Materiais operação", "1.040,00", "Compras"],
                ["NF-1012", "Omega Facilities", "15/04/2026", "Limpeza", "2.320,00", "Facilities"],
                ["NF-1013", "Norte Tecnologia", "20/04/2026", "Licença mensal", "980,00", "Tecnologia"],
                ["NF-1014", "Delta Logística", "25/04/2026", "Frete extra", "12.600,00", "Logística"],
                ["NF-1015", "Beta Serviços", "03/05/2026", "Serviço técnico", "4.100,00", "Serviços"],
                ["NF-1015", "Beta Serviços", "03/05/2026", "Serviço técnico", "4.100,00", "Serviços"],
                ["NF-1016", "Fornecedor Atlas", "06/05/2026", "Peças manutenção", "1.390,00", "Manutenção"],
                ["NF-1017", "Delta Logística", "10/05/2026", "Frete mensal", "8.240,00", "Logística"],
                ["NF-1018", "Norte Tecnologia", "14/05/2026", "Licença mensal", "980,00", "Tecnologia"],
                ["NF-1019", "Omega Facilities", "18/05/2026", "Limpeza", "2.410,00", "Facilities"],
                ["NF-1020", "Cromo Materiais", "22/05/2026", "Materiais operação", "1.180,00", "Compras"],
            ],
            columns=["Documento", "Fornecedor", "Data", "Descrição", "Valor", "Categoria"],
        )
    elif module == "Pagamentos":
        base = pd.DataFrame(
            [
                ["NF-9001", "Fornecedor Alpha", "03/03/2026", "1.250,00"],
                ["NF-9002", "Beta Peças", "11/03/2026", "3.480,00"],
                ["NF-9003", "Gama Consultoria", "14/03/2026", "7.200,00"],
                ["NF-9004", "Delta Materiais", "22/03/2026", "890,00"],
                ["NF-9005", "Omega Facilities", "28/03/2026", "2.440,00"],
                ["NF-9006", "Fornecedor Alpha", "04/04/2026", "1.380,00"],
                ["NF-9007", "Beta Peças", "10/04/2026", "4.120,00"],
                ["NF-9008", "Norte Logística", "18/04/2026", "6.100,00"],
                ["NF-9009", "Gama Consultoria", "24/04/2026", "7.200,00"],
                ["NF-9010", "Omega Facilities", "29/04/2026", "2.600,00"],
                ["NF-9011", "Fornecedor Alpha", "02/05/2026", "1.420,00"],
                ["NF-9012", "Beta Peças", "09/05/2026", "4.550,00"],
                ["NF-9013", "Norte Logística", "15/05/2026", "6.100,00"],
                ["NF-9013", "Norte Logística", "15/05/2026", "6.100,00"],
                ["NF-9014", "Delta Materiais", "22/05/2026", "1.040,00"],
            ],
            columns=["Documento", "Fornecedor", "Vencimento", "Valor"],
        )
        secondary = pd.DataFrame(
            [
                ["NF-9001", "Fornecedor Alpha", "04/03/2026", "1.250,00"],
                ["NF-9002", "Beta Peças", "11/03/2026", "3.480,00"],
                ["NF-9003", "Gama Consultoria", "14/03/2026", "7.200,00"],
                ["PIX-DELTA-9004", "Delta Materiais", "22/03/2026", "890,00"],
                ["NF-9006", "Fornecedor Alpha", "04/04/2026", "1.380,00"],
                ["NF-9007", "Beta Peças", "10/04/2026", "3.900,00"],
                ["NF-9009", "Gama Consultoria", "24/04/2026", "7.200,00"],
                ["NF-9011", "Fornecedor Alpha", "02/05/2026", "1.420,00"],
                ["NF-9014", "Delta Materiais", "22/05/2026", "1.040,00"],
            ],
            columns=["Documento", "Favorecido", "Data pagamento", "Valor"],
        )
    elif module == "Cobrança":
        base = pd.DataFrame(
            [
                ["NF-R1020", "Cliente Atlas", "02/03/2026", "1.800,00"],
                ["NF-R1021", "Cliente Beta", "08/03/2026", "2.450,00"],
                ["NF-R1022", "Cliente Cromo", "14/03/2026", "3.900,00"],
                ["NF-R1023", "Cliente Delta", "17/03/2026", "1.250,00"],
                ["NF-R1024", "Cliente Essencial", "28/03/2026", "7.800,00"],
                ["NF-R1025", "Cliente Atlas", "04/04/2026", "1.950,00"],
                ["NF-R1026", "Cliente Beta", "09/04/2026", "2.700,00"],
                ["NF-R1027", "Cliente Forte", "16/04/2026", "6.400,00"],
                ["NF-R1028", "Cliente Cromo", "21/04/2026", "3.900,00"],
                ["NF-R1029", "Cliente Essencial", "29/04/2026", "7.800,00"],
                ["NF-R1030", "Cliente Atlas", "03/05/2026", "2.100,00"],
                ["NF-R1031", "Cliente Beta", "07/05/2026", "2.920,00"],
                ["NF-R1032", "Cliente Forte", "15/05/2026", "6.400,00"],
                ["NF-R1033", "Cliente Delta", "18/05/2026", "1.390,00"],
                ["NF-R1034", "Cliente Essencial", "27/05/2026", "8.100,00"],
            ],
            columns=["Documento", "Cliente", "Vencimento", "Valor"],
        )
        secondary = pd.DataFrame(
            [
                ["NF-R1020", "Cliente Atlas", "04/03/2026", "1.800,00"],
                ["NF-R1021", "Cliente Beta", "08/03/2026", "2.450,00"],
                ["NF-R1023", "Cliente Delta", "17/03/2026", "1.250,00"],
                ["NF-R1025", "Cliente Atlas", "04/04/2026", "1.950,00"],
                ["NF-R1026", "Cliente Beta", "09/04/2026", "2.200,00"],
                ["NF-R1028", "Cliente Cromo", "21/04/2026", "3.900,00"],
                ["NF-R1030", "Cliente Atlas", "03/05/2026", "2.100,00"],
                ["NF-R1033", "Cliente Delta", "18/05/2026", "1.390,00"],
            ],
            columns=["Documento", "Cliente", "Data recebimento", "Valor"],
        )
    elif module == "Agenda":
        base = pd.DataFrame(
            [
                ["Receber", "Cliente Atlas", "NF-R1020", "02/05/2026", "1.800,00"],
                ["Receber", "Cliente Beta", "NF-R1021", "08/05/2026", "2.450,00"],
                ["Receber", "Cliente Cromo", "NF-R1022", "14/05/2026", "3.900,00"],
                ["Pagar", "Fornecedor Alpha", "NF-9001", "03/05/2026", "1.250,00"],
                ["Pagar", "Beta Peças", "NF-9002", "13/05/2026", "3.480,00"],
                ["Pagar", "Delta Materiais", "NF-9004", "16/05/2026", "890,00"],
                ["Pagar", "Omega Facilities", "NF-9005", "21/05/2026", "2.440,00"],
            ],
            columns=["Tipo", "Nome", "Documento", "Vencimento", "Valor"],
        )
    else:
        base = pd.DataFrame(
            [
                ["Entrada", "NF-3301", "Fornecedor Atlas", "12.345.678/0001-90", "03/05/2026", "Peças manutenção", "Manutenção", "1.250,00"],
                ["Saída", "NF-8801", "Cliente Beta", "22.333.444/0001-55", "04/05/2026", "Serviço prestado", "Receita de serviços", "4.800,00"],
                ["Entrada", "NF-3302", "Delta Logística", "18.222.111/0001-20", "07/05/2026", "Frete mensal", "Logística", "2.950,00"],
                ["Saída", "NF-8802", "Cliente Cromo", "11.222.333/0001-44", "10/05/2026", "Venda mensal", "Receita comercial", "7.600,00"],
                ["Entrada", "NF-3303", "Omega Facilities", "31.444.555/0001-66", "12/05/2026", "Limpeza", "", "1.850,00"],
                ["Entrada", "NF-3304", "Norte Tecnologia", "45.111.222/0001-77", "", "Licença mensal", "Tecnologia", "980,00"],
                ["Revisar", "NF-3305", "Fornecedor sem tipo", "55.666.777/0001-88", "18/05/2026", "Compra operacional", "Compras", "1.420,00"],
                ["Saída", "NF-8803", "Cliente Atlas", "12.111.222/0001-33", "22/05/2026", "Serviço recorrente", "Receita de serviços", "3.100,00"],
                ["Entrada", "NF-3306", "Beta Peças", "22.987.222/0001-00", "24/05/2026", "Material de reposição", "Compras", "2.340,00"],
                ["Saída", "NF-8804", "Cliente Delta", "40.400.400/0001-40", "25/05/2026", "Contrato mensal", "Receita de serviços", "5.200,00"],
                ["Entrada", "NF-3307", "Lumen Energia", "11.777.111/0001-00", "26/05/2026", "Energia elétrica", "Utilities", "3.760,00"],
                ["Entrada", "NF-3308", "Sigma Segurança", "21.888.222/0001-00", "27/05/2026", "Monitoramento", "Segurança", "2.790,00"],
                ["Saída", "NF-8805", "Cliente Essencial", "50.500.500/0001-50", "28/05/2026", "Venda recorrente", "Receita comercial", "8.100,00"],
                ["Entrada", "NF-3309", "Fornecedor sem CNPJ", "", "29/05/2026", "Despesa operacional", "Revisar cadastro", "1.110,00"],
                ["Entrada", "NF-3310", "Rota Express", "31.999.333/0001-00", "30/05/2026", "Entrega expressa", "Logística", ""],
                ["Saída", "NF-8806", "Cliente Giga", "70.700.700/0001-70", "31/05/2026", "Serviço adicional", "", "6.400,00"],
            ],
            columns=["Tipo", "Documento", "Nome", "CNPJ", "Competência", "Descrição", "Categoria", "Valor"],
        )
    return base, secondary


def load_demo(module):
    base, secondary = demo_data(module)
    st.session_state["demo_module"] = module
    st.session_state["demo_base"] = base
    st.session_state["demo_secondary"] = secondary
    st.session_state["demo_loaded"] = True


def render_sidebar():
    st.sidebar.image("assets/docsignal-mark.svg", width=54)
    st.sidebar.title("DocSmart")
    st.sidebar.caption("Demos rápidas para apresentação")

    for module in MODULES:
        if st.sidebar.button(f"Carregar demo {module}", use_container_width=True):
            load_demo(module)

    if st.sidebar.button("Limpar demo", use_container_width=True):
        for key in ["demo_module", "demo_base", "demo_secondary", "demo_loaded"]:
            st.session_state.pop(key, None)

    st.sidebar.divider()
    st.sidebar.markdown("**Como apresentar**")
    st.sidebar.markdown(
        """
        1. Escolha uma demo.
        2. Mostre métricas e alertas.
        3. Baixe o Excel.
        4. Explique que o cliente envia a base real depois.
        """
    )
    st.sidebar.divider()
    st.sidebar.markdown("**Demos em arquivo**")
    st.sidebar.caption("Também existem exemplos XLSX na pasta comercial/docsmart.")


def render_diagnosis(module, primary, secondary, using_demo, accountant=None):
    if primary is None and not using_demo:
        st.warning("Envie a base principal para começar.")
        return

    try:
        df = clean_df(st.session_state["demo_base"] if using_demo else read_upload(primary))
        if df.empty:
            st.warning("A base principal está vazia.")
            return
        cols = infer_columns(df)

        st.caption(
            "Colunas detectadas: "
            + ", ".join(f"{k}: {v or 'não encontrada'}" for k, v in cols.items())
        )

        sheets = {}
        if module == "Planilhas":
            metrics, treated, alerts, top, monthly, alert_summary, seasonality, weekly, insights = summarize_planilhas(df, cols)
            metric_grid(metrics)
            insight_grid(insights)
            tab_alerts, tab_rank, tab_trend, tab_season = st.tabs(["Alertas priorizados", "Ranking", "Tendência", "Sazonalidade"])
            with tab_alerts:
                st.markdown("### Alertas priorizados por score")
                show_cols = [
                    col for col in [
                        cols.get("documento"),
                        cols.get("fornecedor"),
                        cols.get("data"),
                        cols.get("valor"),
                        "_score_atencao",
                        "_alerta",
                        "_motivos",
                    ] if col and col in alerts.columns
                ]
                st.dataframe(alerts[show_cols].head(30), use_container_width=True)
            with tab_rank:
                st.markdown("### Maiores valores por fornecedor/cliente")
                st.dataframe(top, use_container_width=True)
                st.markdown("### Distribuição dos alertas")
                st.dataframe(alert_summary, use_container_width=True)
            with tab_trend:
                st.markdown("### Evolução mensal detectada")
                st.bar_chart(monthly.set_index("Mês")["Valor"] if not monthly.empty else pd.Series(dtype="float64"))
                st.dataframe(monthly, use_container_width=True)
            with tab_season:
                st.markdown("### Concentração dentro do mês")
                st.bar_chart(seasonality.set_index("Faixa do mês")["Valor"] if not seasonality.empty else pd.Series(dtype="float64"))
                st.dataframe(seasonality, use_container_width=True)
                st.markdown("### Semanas do mês")
                if not weekly.empty:
                    week_pivot = weekly.pivot_table(index="Mês", columns="Semana", values="Valor", aggfunc="sum", fill_value=0)
                    st.dataframe(week_pivot, use_container_width=True)
                    st.bar_chart(week_pivot.T)
                else:
                    st.info("Sem datas suficientes para agrupar por semana.")
            sheets = {
                "Resumo executivo": pd.DataFrame(insights, columns=["Tema", "Leitura", "Tom"]),
                "Base tratada": treated,
                "Alertas": alerts,
                "Ranking": top,
                "Tendência mensal": monthly,
                "Sazonalidade": seasonality,
                "Semanas do mês": weekly,
                "Resumo alertas": alert_summary,
            }

        elif module in ["Pagamentos", "Cobrança"]:
            if secondary is None and not using_demo:
                st.warning("Este módulo precisa da segunda base para cruzamento.")
                return
            sec_df = clean_df(st.session_state["demo_secondary"] if using_demo else read_upload(secondary))
            sec_cols = infer_columns(sec_df)
            paid_label = "Pagamento localizado" if module == "Pagamentos" else "Recebimento localizado"
            metrics, treated, pending, top, status_summary, monthly, weekly, insights = match_by_doc_or_value(df, sec_df, cols, sec_cols, paid_label)
            metric_grid(metrics)
            insight_grid(insights)
            st.caption(
                "Colunas da segunda base: "
                + ", ".join(f"{k}: {v or 'não encontrada'}" for k, v in sec_cols.items())
            )
            tab_pending, tab_status, tab_concentration, tab_time = st.tabs(["Pendências priorizadas", "Status", "Concentração", "Sazonalidade"])
            with tab_pending:
                st.markdown("### Pendências e divergências por score")
                show_cols = [
                    col for col in [
                        cols.get("documento"),
                        cols.get("fornecedor"),
                        cols.get("data"),
                        cols.get("valor"),
                        "_status_docsmart",
                        "_score_atencao",
                        "_prioridade",
                        "_motivo",
                    ] if col and col in pending.columns
                ]
                st.dataframe(pending[show_cols].head(50), use_container_width=True)
            with tab_status:
                st.markdown("### Distribuição por status")
                st.dataframe(status_summary, use_container_width=True)
                st.bar_chart(status_summary.set_index("_status_docsmart")["Valor"] if not status_summary.empty else pd.Series(dtype="float64"))
            with tab_concentration:
                st.markdown("### Concentração por fornecedor/cliente")
                st.dataframe(top, use_container_width=True)
                st.bar_chart(top.set_index("Nome")["Valor"] if not top.empty else pd.Series(dtype="float64"))
            with tab_time:
                st.markdown("### Evolução mensal por status")
                if not monthly.empty:
                    monthly_pivot = monthly.pivot_table(index="Mês", columns="Status", values="Valor", aggfunc="sum", fill_value=0)
                    st.dataframe(monthly_pivot, use_container_width=True)
                    st.bar_chart(monthly_pivot)
                st.markdown("### Semanas do mês")
                if not weekly.empty:
                    weekly_pivot = weekly.pivot_table(index="Mês", columns="Semana", values="Valor", aggfunc="sum", fill_value=0)
                    st.dataframe(weekly_pivot, use_container_width=True)
                    st.bar_chart(weekly_pivot.T)
            sheets = {
                "Resumo executivo": pd.DataFrame(insights, columns=["Tema", "Leitura", "Tom"]),
                "Base cruzada": treated,
                "Pendências": pending,
                "Status": status_summary,
                "Concentração": top,
                "Evolução mensal": monthly,
                "Semanas": weekly,
                "Base secundária": sec_df,
            }

        elif module == "Agenda":
            metrics, treated, agenda, by_day = summarize_agenda(df, cols)
            metric_grid(metrics)
            st.markdown("### Calendário do mês")
            render_agenda_calendar(treated)
            st.markdown("### Agenda de ações")
            st.dataframe(agenda.head(50), use_container_width=True)
            sheets = {"Base tratada": treated, "Agenda de ações": agenda, "Visão por data": by_day}
        else:
            accountant = accountant or {}
            required = ["contador", "crc", "email", "periodo"]
            if not all(str(accountant.get(key, "")).strip() for key in required):
                st.warning("Para gerar o Fiscal Assist, informe contador/escritório, CRC, e-mail contábil e período de competência.")
                return
            if not accountant.get("confirmado"):
                st.warning("Confirme que o pacote será submetido à validação de contador habilitado.")
                return
            metrics, treated, summary, by_category, validation, protocol, insights = summarize_fiscal_assist(df, cols, accountant)
            metric_grid(metrics)
            insight_grid(insights)
            st.markdown(
                """
                <div class="note">
                Fiscal Assist organiza entradas e saídas em relatório técnico para validação contábil. Não calcula tributo, não apura imposto e não substitui profissional habilitado.
                </div>
                """,
                unsafe_allow_html=True,
            )
            tab_summary, tab_category, tab_validation, tab_protocol = st.tabs(["Resumo contábil", "Categorias", "Validações", "Protocolo"])
            with tab_summary:
                st.markdown("### Entradas e saídas por competência")
                st.dataframe(summary, use_container_width=True)
                if not summary.empty:
                    pivot = summary.pivot_table(index="Competência", columns="Tipo", values="Valor", aggfunc="sum", fill_value=0)
                    st.bar_chart(pivot)
            with tab_category:
                st.markdown("### Classificação sugerida para conferência")
                st.dataframe(by_category, use_container_width=True)
            with tab_validation:
                st.markdown("### Itens que exigem validação antes do envio contábil")
                if validation.empty:
                    st.success("Nenhum bloqueio técnico detectado na amostra. A validação contábil ainda é obrigatória.")
                else:
                    st.dataframe(validation.head(50), use_container_width=True)
            with tab_protocol:
                st.markdown("### Protocolo de envio para validação contábil")
                st.dataframe(protocol, use_container_width=True)
            sheets = {
                "Resumo executivo": pd.DataFrame(insights, columns=["Tema", "Leitura", "Tom"]),
                "Protocolo contábil": protocol,
                "Base organizada": treated,
                "Resumo por competência": summary,
                "Categorias sugeridas": by_category,
                "Itens para validar": validation,
            }

        resumo = pd.DataFrame(
            {
                "Item": [m[0] for m in metrics] + ["Módulo", "Arquivo analisado"],
                "Valor": [m[1] for m in metrics] + [module, "Demo interna" if using_demo else primary.name],
            }
        )
        sheets = {"Resumo": resumo, **sheets}
        excel = build_excel(sheets)
        st.download_button(
            "Baixar diagnóstico Excel",
            data=excel,
            file_name=f"diagnostico_docsmart_{normalize_name(module)}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    except Exception as exc:
        st.error(f"Não consegui processar essa base: {exc}")


def render_home():
    st.markdown(
        """
        <div class="home-hero">
          <div>
            <small>DocSmart Web</small>
            <div class="home-title">Diagnóstico rápido para planilhas financeiras.</div>
            <p>
              Transforme CSV, Excel e bases exportadas em painel, alertas, sazonalidade,
              pendências e leitura executiva em poucos minutos.
            </p>
          </div>
          <div class="home-panel">
            <div class="home-row"><strong>Planilhas</strong><span>R$ 600</span></div>
            <div class="home-row"><strong>Agenda</strong><span>R$ 600</span></div>
            <div class="home-row"><strong>Pagamentos</strong><span>R$ 700</span></div>
            <div class="home-row"><strong>Cobrança</strong><span>R$ 700</span></div>
            <div class="home-row"><strong>Fiscal Assist</strong><span>R$ 900</span></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("### Como a demonstração funciona")
    st.markdown(
        """
        <div class="home-steps">
          <div class="home-step"><strong>1. Escolha o desafio operacional</strong><span>Planilha, pagamento, cobrança, agenda ou pacote para contador.</span></div>
          <div class="home-step"><strong>2. Carregue a demo</strong><span>A lateral traz exemplos prontos para apresentar sem procurar arquivos.</span></div>
          <div class="home-step"><strong>3. Gere a entrega</strong><span>O app mostra métricas, alertas, score e baixa um Excel de diagnóstico.</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns([0.22, 0.78])
    if col1.button("Entrar na demo", type="primary", use_container_width=True):
        st.session_state["entered_demo"] = True
        st.rerun()
    col2.info("Use esta tela para abrir a apresentação. Depois, entre na demo e carregue um módulo pela lateral esquerda.")


def main():
    css()
    if not st.session_state.get("entered_demo"):
        render_home()
        return

    render_sidebar()
    st.markdown(
        """
        <div class="hero">
          <small>DocSmart Web</small>
          <div class="hero-title">Diagnóstico rápido por planilha.</div>
          <p>Escolha o módulo, suba CSV/XLSX e gere uma primeira leitura com métricas, alertas e arquivo de entrega.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_modules()

    st.divider()
    left, right = st.columns([0.28, 0.72], gap="large")

    with left:
        st.subheader("Configurar diagnóstico")
        module_names = list(MODULES.keys())
        default_module = st.session_state.get("demo_module", module_names[0])
        module = st.selectbox("Módulo", module_names, index=module_names.index(default_module))
        primary = st.file_uploader("Base principal (CSV/XLSX)", type=["csv", "xlsx", "xls"])
        secondary = None
        if MODULES[module]["needs_secondary"]:
            secondary = st.file_uploader(MODULES[module]["secondary_label"], type=["csv", "xlsx", "xls"])
        accountant = {}
        if module == "Fiscal Assist":
            st.markdown("#### Responsável contábil")
            accountant = {
                "empresa": st.text_input("Empresa analisada", value="Empresa demonstração" if st.session_state.get("demo_module") == module else ""),
                "periodo": st.text_input("Período de competência", value="05/2026" if st.session_state.get("demo_module") == module else ""),
                "contador": st.text_input("Contador ou escritório contábil", value="Escritório Contábil Exemplo" if st.session_state.get("demo_module") == module else ""),
                "crc": st.text_input("CRC informado", value="CRC-SP 000000/O-0" if st.session_state.get("demo_module") == module else ""),
                "email": st.text_input("E-mail contábil", value="contador@exemplo.com.br" if st.session_state.get("demo_module") == module else ""),
            }
            accountant["confirmado"] = st.checkbox(
                "Confirmo que o pacote será submetido à validação de contador habilitado.",
                value=st.session_state.get("demo_module") == module,
                key="fiscal_confirm",
            )
        using_demo = bool(st.session_state.get("demo_loaded")) and st.session_state.get("demo_module") == module
        if using_demo:
            st.success(f"Demo {module} carregada pela lateral.")
        st.markdown(
            """
            <div class="note">
            Use uma amostra sem dados sensíveis na primeira validação. O app tenta detectar colunas de valor, data, documento e fornecedor/cliente automaticamente.
            </div>
            """,
            unsafe_allow_html=True,
        )
        run = st.button("Gerar diagnóstico", type="primary", use_container_width=True) or using_demo

    with right:
        st.subheader("Resultado")
        if not run:
            st.info("Suba uma base ou carregue uma demo pela lateral esquerda.")
            return
        if module == "Agenda":
            st.info("A demo Agenda aparece abaixo em largura total para preservar o layout de calendário.")
        else:
            render_diagnosis(module, primary, secondary, using_demo, accountant)

    if run and module == "Agenda":
        st.divider()
        render_diagnosis(module, primary, secondary, using_demo, accountant)


if __name__ == "__main__":
    main()
