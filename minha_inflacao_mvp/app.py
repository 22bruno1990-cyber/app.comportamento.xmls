import base64
import hashlib
import html
import re
import sqlite3
from dataclasses import dataclass
from datetime import date, datetime
from io import BytesIO
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pandas as pd
import requests
import streamlit as st


APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "minha_inflacao.db"
HERO_IMAGE_PATH = APP_DIR / "assets" / "minha-inflacao-hero-bg.png"
CATEGORIES = [
    "Arroz, feijão e grãos",
    "Bebidas",
    "Bebê e infantil",
    "Café e mercearia",
    "Carnes e ovos",
    "Congelados",
    "Doces e snacks",
    "Despesas pessoais",
    "Educação",
    "Farmácia",
    "Higiene",
    "Hortifruti",
    "Laticínios",
    "Limpeza",
    "Mercearia geral",
    "Padaria",
    "Pet",
    "Transportes",
    "Comunicação",
    "Vestuário",
    "Utilidades",
]
IPCA_GROUPS = [
    {
        "group": "Alimentação e bebidas",
        "plain_language": "Mercado, comida em casa, bebidas e alimentação fora.",
        "app_examples": "arroz, leite, carnes, hortifruti, café, snacks, bebidas",
    },
    {
        "group": "Habitação",
        "plain_language": "Moradia e contas da casa.",
        "app_examples": "produtos de limpeza, gás, energia, água e condomínio quando cadastrados",
    },
    {
        "group": "Artigos de residência",
        "plain_language": "Itens para casa, móveis, eletros e utensílios.",
        "app_examples": "utensílios e itens domésticos quando aparecerem nos cupons",
    },
    {
        "group": "Vestuário",
        "plain_language": "Roupas, calçados e acessórios.",
        "app_examples": "não aparece no cupom de mercado, mas pode entrar em compras futuras",
    },
    {
        "group": "Transportes",
        "plain_language": "Combustível, transporte público, apps, veículo e manutenção.",
        "app_examples": "não aparece no cupom de mercado, mas pode entrar em despesas cadastradas",
    },
    {
        "group": "Saúde e cuidados pessoais",
        "plain_language": "Farmácia, higiene, plano de saúde e cuidados pessoais.",
        "app_examples": "higiene pessoal, absorvente, shampoo, escova, itens de farmácia",
    },
    {
        "group": "Despesas pessoais",
        "plain_language": "Serviços pessoais, lazer, pet e gastos diversos.",
        "app_examples": "pet, lazer e serviços quando cadastrados",
    },
    {
        "group": "Educação",
        "plain_language": "Escola, cursos, mensalidades e material escolar.",
        "app_examples": "pode entrar em despesas cadastradas fora do cupom de mercado",
    },
    {
        "group": "Comunicação",
        "plain_language": "Internet, celular, telefone e serviços digitais.",
        "app_examples": "pode entrar em despesas cadastradas fora do cupom de mercado",
    },
]
CATEGORY_TO_IPCA_GROUP = {
    "Arroz, feijão e grãos": "Alimentação e bebidas",
    "Bebidas": "Alimentação e bebidas",
    "Bebê e infantil": "Saúde e cuidados pessoais",
    "Café e mercearia": "Alimentação e bebidas",
    "Carnes e ovos": "Alimentação e bebidas",
    "Congelados": "Alimentação e bebidas",
    "Doces e snacks": "Alimentação e bebidas",
    "Farmácia": "Saúde e cuidados pessoais",
    "Higiene": "Saúde e cuidados pessoais",
    "Hortifruti": "Alimentação e bebidas",
    "Laticínios": "Alimentação e bebidas",
    "Limpeza": "Habitação",
    "Mercearia geral": "Alimentação e bebidas",
    "Padaria": "Alimentação e bebidas",
    "Pet": "Despesas pessoais",
    "Transportes": "Transportes",
    "Comunicação": "Comunicação",
    "Vestuário": "Vestuário",
    "Despesas pessoais": "Despesas pessoais",
    "Educação": "Educação",
    "Utilidades": "Artigos de residência",
}
IPCA_GROUP_TO_DEFAULT_CATEGORY = {
    "Alimentação e bebidas": "Mercearia geral",
    "Habitação": "Limpeza",
    "Artigos de residência": "Utilidades",
    "Vestuário": "Vestuário",
    "Transportes": "Transportes",
    "Saúde e cuidados pessoais": "Farmácia",
    "Despesas pessoais": "Despesas pessoais",
    "Educação": "Educação",
    "Comunicação": "Comunicação",
}


@dataclass
class Receipt:
    access_key: str
    source_url: str
    merchant: str
    purchase_date: date
    total: float
    items: list[dict]


def init_db() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS receipts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fingerprint TEXT NOT NULL UNIQUE,
                access_key TEXT,
                source_url TEXT,
                merchant TEXT,
                purchase_date TEXT NOT NULL,
                total REAL NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                receipt_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                normalized_name TEXT NOT NULL,
                category TEXT NOT NULL,
                quantity REAL NOT NULL,
                unit TEXT,
                unit_price REAL NOT NULL,
                total_price REAL NOT NULL,
                FOREIGN KEY(receipt_id) REFERENCES receipts(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS product_rules (
                raw_key TEXT PRIMARY KEY,
                display_name TEXT NOT NULL,
                category TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        columns = {row[1] for row in conn.execute("PRAGMA table_info(items)").fetchall()}
        if "raw_key" not in columns:
            conn.execute("ALTER TABLE items ADD COLUMN raw_key TEXT")
            rows = conn.execute("SELECT id, product_name FROM items").fetchall()
            for item_id, product_name in rows:
                conn.execute("UPDATE items SET raw_key = ? WHERE id = ?", (raw_product_key(product_name), item_id))


def br_number(value: str | None) -> float:
    if not value:
        return 0.0
    cleaned = re.sub(r"[^\d,.-]", "", value).strip()
    if "," in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def money(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def clean_text(value: str) -> str:
    value = html.unescape(value or "")
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def image_data_uri(path: Path) -> str:
    if not path.exists():
        return ""
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def render_light_theme_css() -> None:
    hero_image = image_data_uri(HERO_IMAGE_PATH)
    st.markdown(
        """
        <style>
        :root {
            --mi-ink: #1f2933;
            --mi-muted: #667085;
            --mi-money: #2f8f6b;
            --mi-money-dark: #1f6f55;
            --mi-calc: #2f4f68;
            --mi-inflation: #b7791f;
            --mi-inflation-soft: #fff8e8;
            --mi-paper: #f7f8f5;
            --mi-panel: #ffffff;
            --mi-line: #e4e7ec;
        }
        .stApp {
            background: var(--mi-paper);
            color: var(--mi-ink);
        }
        [data-testid="stHeader"] {
            background: rgba(247, 248, 245, 0.94);
        }
        [data-testid="stMetric"],
        [data-testid="stVerticalBlockBorderWrapper"] {
            background: var(--mi-panel);
            border-color: var(--mi-line);
            box-shadow: 0 1px 2px rgba(31, 41, 51, 0.04);
        }
        [data-testid="stMetric"] {
            border-left: 2px solid rgba(47, 143, 107, 0.55);
        }
        [data-testid="stMetric"] [data-testid="stMetricValue"] {
            color: var(--mi-money-dark);
        }
        div[data-testid="stDataFrame"] {
            background: var(--mi-panel);
            border: 1px solid var(--mi-line);
            border-radius: 8px;
        }
        h1, h2, h3, p, label, span {
            color: var(--mi-ink);
        }
        h1 {
            color: var(--mi-ink);
            font-weight: 650;
        }
        h2, h3 {
            color: var(--mi-calc);
            font-weight: 600;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 2px;
            border-bottom: 1px solid var(--mi-line);
        }
        .stTabs [data-baseweb="tab"] {
            background: transparent;
            border: 0;
            border-bottom: 2px solid transparent;
            border-radius: 0;
            color: var(--mi-muted);
            padding: 10px 14px;
        }
        .stTabs [aria-selected="true"] {
            background: transparent;
            border-bottom-color: var(--mi-money);
            color: var(--mi-money-dark);
        }
        .stTabs [aria-selected="true"] p {
            color: var(--mi-money-dark);
        }
        .stButton > button {
            background: #ffffff;
            color: var(--mi-calc);
            border: 1px solid #cfd6dd;
            border-radius: 8px;
            box-shadow: 0 1px 2px rgba(31, 41, 51, 0.04);
            font-weight: 500;
        }
        .stButton > button:hover {
            background: #f8faf9;
            color: var(--mi-money-dark);
            border-color: rgba(47, 143, 107, 0.45);
        }
        .stButton > button[kind="primary"] {
            background: #eef7f2;
            color: var(--mi-money-dark);
            border: 1px solid rgba(47, 143, 107, 0.35);
        }
        .stButton > button[kind="primary"]:hover {
            background: #e4f1eb;
            color: var(--mi-money-dark);
            border-color: rgba(47, 143, 107, 0.55);
        }
        [data-testid="stAlert"] {
            border-color: #ead49c;
            background: var(--mi-inflation-soft);
        }
        div[data-testid="stExpander"] {
            background: var(--mi-panel);
            border: 1px solid var(--mi-line);
            border-radius: 8px;
        }
        .mi-cover {
            position: relative;
            overflow: hidden;
            display: grid;
            grid-template-columns: minmax(0, 1.05fr) minmax(320px, 0.95fr);
            gap: 24px;
            align-items: stretch;
            padding: 30px;
            margin: 10px 0 28px;
            border: 1px solid var(--mi-line);
            border-radius: 12px;
            background:
                radial-gradient(circle at 92% 12%, rgba(183, 121, 31, 0.11), transparent 32%),
                linear-gradient(135deg, #ffffff 0%, #f7fbf8 100%);
            box-shadow: 0 14px 36px rgba(31, 41, 51, 0.07);
        }
        .mi-cover > * {
            position: relative;
            z-index: 1;
        }
        .mi-cover__eyebrow {
            display: inline-flex;
            width: fit-content;
            padding: 6px 10px;
            border-radius: 999px;
            background: var(--mi-inflation-soft);
            color: #8a5b16;
            border: 1px solid #ead49c;
            font-size: 13px;
            font-weight: 700;
            margin-bottom: 16px;
        }
        .mi-cover h1 {
            margin: 0;
            max-width: 760px;
            font-size: 48px;
            line-height: 1;
            font-weight: 760;
            color: var(--mi-ink);
        }
        .mi-cover p {
            margin: 18px 0 0;
            color: var(--mi-muted);
            font-size: 18px;
            line-height: 1.55;
            max-width: 720px;
        }
        .mi-cover__side {
            display: grid;
            gap: 14px;
        }
        .mi-cover__visual {
            min-height: 300px;
            aspect-ratio: 1 / 1;
            border-radius: 12px;
            border: 1px solid var(--mi-line);
            background:
                linear-gradient(180deg, rgba(255, 255, 255, 0.03), rgba(255, 255, 255, 0.20)),
                url("{{HERO_IMAGE}}") center / cover no-repeat;
            box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.45), 0 12px 30px rgba(31, 41, 51, 0.08);
        }
        .mi-cover__panel {
            display: grid;
            align-content: center;
            gap: 12px;
            padding: 22px;
            border-radius: 10px;
            background: rgba(255, 255, 255, 0.82);
            border: 1px solid var(--mi-line);
        }
        .mi-cover__row {
            display: grid;
            grid-template-columns: 38px 1fr;
            gap: 12px;
            align-items: center;
            padding: 12px;
            border-radius: 8px;
            background: #ffffff;
            border: 1px solid #edf0f2;
        }
        .mi-cover__icon {
            width: 38px;
            height: 38px;
            display: grid;
            place-items: center;
            border-radius: 8px;
            background: #eef7f2;
            color: var(--mi-money-dark);
            font-weight: 800;
            font-size: 13px;
        }
        .mi-cover__row strong {
            display: block;
            color: var(--mi-calc);
            font-size: 15px;
        }
        .mi-cover__row span {
            display: block;
            color: var(--mi-muted);
            font-size: 13px;
            margin-top: 2px;
        }
        @media (max-width: 900px) {
            .mi-cover {
                grid-template-columns: 1fr;
                padding: 22px;
                background:
                    linear-gradient(135deg, #ffffff 0%, #f7fbf8 100%);
            }
            .mi-cover__visual {
                min-height: 220px;
            }
            .mi-cover h1 {
                font-size: 38px;
            }
        }
        </style>
        """.replace("{{HERO_IMAGE}}", hero_image),
        unsafe_allow_html=True,
    )


def normalize_product_name(name: str) -> str:
    normalized = clean_text(name).upper()
    normalized = re.sub(r"\b(LT|LTA|UNID|UN|KG|G|ML|L)\b", " ", normalized)
    normalized = re.sub(r"\b\d+([,.]\d+)?\b", " ", normalized)
    normalized = re.sub(r"[^A-Z0-9À-Ú ]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized[:80] or clean_text(name).upper()[:80]


def categorize(name: str) -> str:
    n = normalize_product_name(name)
    rules = [
        ("Arroz, feijão e grãos", ["ARROZ", "FEIJAO", "FEIJ", "LENTILHA", "GRAO", "GRAOS", "PIP YOKI"]),
        ("Laticínios", ["LEITE", "LTE", "IOGUR", "YAKULT", "QUEIJO", "QJ", "MANTEIGA", "MANT", "REQUEIJAO"]),
        ("Carnes e ovos", ["CARNE", "FRANGO", "BOV", "SUINO", "PEIXE", "OVO", "LINGUICA", "LING", "PRESUNTO"]),
        ("Hortifruti", ["BANANA", "MACA", "LARANJA", "TOMATE", "CEBOLA", "BATATA", "ALFACE", "CENOURA", "GOIA", "FRUT"]),
        ("Café e mercearia", ["CAFE", "ACUCAR", "OLEO", "FARINHA", "MACARRAO", "MOLHO", "HELLM", "MAIONESE", "PRINGLES", "BISCO", "B PRINGLES", "POLP", "SUCR", "BAT PALHA", "MILHO", "SAL ", "PAO", "PANC"]),
        ("Limpeza", ["DETERG", "DET ", "SABAO", "AMACIANTE", "AM COMFORT", "COMFORT", "DESINF", "AGUA SANIT", "OMO", "ROUPA", "LIMPOL", "COPERALC"]),
        ("Higiene", ["PAPEL HIG", "P H ", "SHAMPOO", "SH350", "PANT", "SABONETE", "CREME DENT", "DESOD", "ABS ", "TOALHA", "ESC ORAL", "ALC GEL"]),
        ("Bebidas", ["REFRI", "SUCO", "AGUA", "CERVEJA", "VINHO", "AZ ANDOR"]),
        ("Bebê e infantil", ["NINH 380G", "INFANT", "FRALDA"]),
        ("Padaria", ["PAO ", "BOLO", "BISNAG", "PANCO"]),
    ]
    for category, keys in rules:
        if any(key in n for key in keys):
            return category
    return "Mercearia geral"


def raw_product_key(name: str) -> str:
    return normalize_product_name(name)


def category_to_ipca_group(category: str) -> str:
    return CATEGORY_TO_IPCA_GROUP.get(str(category), "Alimentação e bebidas")


def extract_access_key(url: str, page_text: str = "") -> str:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    if query.get("p"):
        digits = re.sub(r"\D", "", query["p"][0])
        if len(digits) >= 44:
            return digits[:44]
    for source in [url, page_text]:
        match = re.search(r"\b(\d{44})\b", source)
        if match:
            return match.group(1)
    return hashlib.sha1((url + page_text[:500]).encode("utf-8")).hexdigest()[:20]


def extract_date(text: str) -> date:
    patterns = [
        r"Emiss[aã]o\s*[:\-]?\s*(\d{2}/\d{2}/\d{4})",
        r"Data\s+de\s+Emiss[aã]o\s*[:\-]?\s*(\d{2}/\d{2}/\d{4})",
        r"(\d{2}/\d{2}/\d{4})\s+\d{2}:\d{2}",
        r"\b(\d{2}/\d{2}/\d{4})\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.I)
        if match:
            return datetime.strptime(match.group(1), "%d/%m/%Y").date()
    return date.today()


def extract_merchant(raw_html: str, text: str | None = None) -> str:
    text = text or clean_text(raw_html)
    html_patterns = [
        r"class=[\"'][^\"']*txtTopo[^\"']*[\"'][^>]*>([\s\S]*?)</(?:div|span|p)>",
        r"id=[\"']u20[\"'][^>]*>([\s\S]*?)</(?:div|span|p)>",
    ]
    for pattern in html_patterns:
        match = re.search(pattern, raw_html, flags=re.I)
        if match:
            merchant = clean_text(match.group(1))
            if merchant:
                return merchant[:120]

    patterns = [
        r"Nome/Raz[aã]o Social\s*[:\-]?\s*([^|]+?)(?:CNPJ|Inscri|Endere|$)",
        r"Emitente\s*[:\-]?\s*([^|]+?)(?:CNPJ|$)",
        r"([A-Z0-9 .,&-]{6,})\s+CNPJ",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.I)
        if match:
            return clean_text(match.group(1))[:120]
    blocked = ("consulta resumida", "secretaria da fazenda", "document", "$(", "function")
    lines = [
        line.strip()
        for line in text.splitlines()
        if len(line.strip()) > 5 and not any(term in line.lower() for term in blocked)
    ]
    return lines[0][:120] if lines else "Mercado nao identificado"


def extract_total(text: str, items: list[dict]) -> float:
    patterns = [
        r"Valor\s+total\s+da\s+nota\s*[:\-]?\s*R?\$?\s*([\d.,]+)",
        r"Valor\s+a\s+pagar\s*[:\-]?\s*R?\$?\s*([\d.,]+)",
        r"Valor\s+total\s*[:\-]?\s*R?\$?\s*([\d.,]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.I)
        if match:
            return br_number(match.group(1))
    return round(sum(item["total_price"] for item in items), 2)


def parse_item_blocks(raw_html: str) -> list[dict]:
    blocks = re.findall(
        r"(<tr[^>]*(?:id=[\"']?Item|class=[\"'][^\"']*Item)[\s\S]*?</tr>)",
        raw_html,
        flags=re.I,
    )
    if not blocks:
        blocks = re.findall(r"(<tr[\s\S]*?</tr>)", raw_html, flags=re.I)

    items = []
    for block in blocks:
        if not re.search(r"txtTit|Qtde|Qtd|Vl\.?\s*Unit|valor", block, flags=re.I):
            continue

        title_match = re.search(
            r"class=[\"'][^\"']*txtTit[^\"']*[\"'][^>]*>([\s\S]*?)</span>",
            block,
            flags=re.I,
        )
        if not title_match:
            cells = re.findall(r"<t[dh][^>]*>([\s\S]*?)</t[dh]>", block, flags=re.I)
            title = clean_text(cells[0]) if cells else ""
        else:
            title = clean_text(title_match.group(1))

        if not title or len(title) < 2:
            continue

        text = clean_text(block)
        quantity = br_number(first_match(text, [r"Qtde\.?\s*:?\s*([\d.,]+)", r"Qtd\.?\s*:?\s*([\d.,]+)"])) or 1
        unit = first_match(text, [r"\bUN\.?\s*:?\s*([A-Z0-9]+)", r"Unidade\s*:?\s*([A-Z0-9]+)"]) or "UN"
        unit_price = br_number(first_match(text, [r"Vl\.?\s*Unit\.?\s*:?\s*R?\$?\s*([\d.,]+)", r"Unit[aá]rio\s*:?\s*R?\$?\s*([\d.,]+)"]))

        value_matches = re.findall(
            r"class=[\"'][^\"']*valor[^\"']*[\"'][^>]*>([\s\S]*?)</span>",
            block,
            flags=re.I,
        )
        total_price = br_number(clean_text(value_matches[-1])) if value_matches else 0.0
        if total_price == 0:
            total_price = br_number(first_match(text, [r"Valor\s*total\s*:?\s*R?\$?\s*([\d.,]+)"]))
        if unit_price == 0 and quantity:
            unit_price = round(total_price / quantity, 4)
        if total_price == 0 and unit_price:
            total_price = round(quantity * unit_price, 2)

        items.append(
            {
                "product_name": title,
                "normalized_name": normalize_product_name(title),
                "category": categorize(title),
                "quantity": quantity,
                "unit": unit,
                "unit_price": unit_price,
                "total_price": total_price,
            }
        )
    return items


def first_match(text: str, patterns: list[str]) -> str:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.I)
        if match:
            return match.group(1)
    return ""


def parse_nfce_html(raw_html: str, source_url: str) -> Receipt:
    text = clean_text(raw_html)
    items = parse_item_blocks(raw_html)
    return Receipt(
        access_key=extract_access_key(source_url, text),
        source_url=source_url,
        merchant=extract_merchant(raw_html, text),
        purchase_date=extract_date(text),
        total=extract_total(text, items),
        items=items,
    )


def fetch_nfce(url: str) -> Receipt:
    headers = {
        "User-Agent": "Mozilla/5.0 MinhaInflacao/0.1",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return parse_nfce_html(response.text, url)


def decode_qr_image(uploaded_file) -> str:
    try:
        import cv2
        import numpy as np
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError(
            "Leitura de imagem do QR Code precisa do pacote opencv-python-headless. "
            "Por enquanto, abra o QR Code no celular e cole o link aqui."
        ) from exc

    image = Image.open(BytesIO(uploaded_file.getvalue())).convert("RGB")
    array = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    detector = cv2.QRCodeDetector()
    decoded, _, _ = detector.detectAndDecode(array)
    if not decoded:
        raise ValueError("Nao encontrei um QR Code legivel nessa imagem.")
    return decoded


def receipt_fingerprint(receipt: Receipt) -> str:
    base = f"{receipt.access_key}|{receipt.purchase_date.isoformat()}|{receipt.total:.2f}"
    return hashlib.sha1(base.encode("utf-8")).hexdigest()


def save_receipt(receipt: Receipt, items_df: pd.DataFrame) -> tuple[bool, str]:
    if items_df.empty:
        return False, "Nenhum item para salvar."

    fingerprint = receipt_fingerprint(receipt)
    with sqlite3.connect(DB_PATH) as conn:
        rules = load_product_rules(conn)
        try:
            cursor = conn.execute(
                """
                INSERT INTO receipts
                    (fingerprint, access_key, source_url, merchant, purchase_date, total, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    fingerprint,
                    receipt.access_key,
                    receipt.source_url,
                    receipt.merchant,
                    receipt.purchase_date.isoformat(),
                    float(items_df["total_price"].sum()),
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )
        except sqlite3.IntegrityError:
            return False, "Esse cupom ja foi salvo antes."

        receipt_id = cursor.lastrowid
        for row in items_df.to_dict("records"):
            product_name = clean_text(str(row["product_name"]))
            key = raw_product_key(product_name)
            rule = rules.get(key)
            display_name = rule["display_name"] if rule else normalize_product_name(str(row.get("normalized_name") or product_name))
            category = rule["category"] if rule else str(row.get("category") or categorize(product_name))
            conn.execute(
                """
                INSERT INTO items
                    (receipt_id, product_name, raw_key, normalized_name, category, quantity, unit, unit_price, total_price)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    receipt_id,
                    product_name,
                    key,
                    display_name,
                    category,
                    float(row.get("quantity") or 1),
                    str(row.get("unit") or "UN"),
                    float(row.get("unit_price") or 0),
                    float(row.get("total_price") or 0),
                ),
            )
    return True, "Cupom salvo no historico."


def save_manual_expense(expense: dict) -> tuple[bool, str]:
    description = clean_text(str(expense["description"]))
    if not description:
        return False, "Informe uma descrição para a despesa."
    total = float(expense["total_price"])
    if total <= 0:
        return False, "Informe um valor maior que zero."

    quantity = float(expense.get("quantity") or 1)
    unit_price = total / quantity if quantity else total
    purchase_date = pd.to_datetime(expense["purchase_date"]).date()
    source = clean_text(str(expense.get("source") or "Lançamento manual"))
    ipca_group = str(expense["ipca_group"])
    category = str(expense.get("category") or IPCA_GROUP_TO_DEFAULT_CATEGORY.get(ipca_group, "Despesas pessoais"))
    normalized_name = clean_text(str(expense.get("normalized_name") or description)).upper()
    raw_key = raw_product_key(normalized_name)
    fingerprint = hashlib.sha1(
        f"manual|{purchase_date.isoformat()}|{source}|{description}|{total:.2f}".encode("utf-8")
    ).hexdigest()
    attachment_ref = "manual"
    attachment = expense.get("attachment")
    if attachment is not None:
        attachments_dir = APP_DIR / "attachments"
        attachments_dir.mkdir(exist_ok=True)
        safe_name = re.sub(r"[^A-Za-z0-9_.-]", "_", attachment.name)
        attachment_path = attachments_dir / f"{fingerprint[:12]}_{safe_name}"
        attachment_path.write_bytes(attachment.getvalue())
        attachment_ref = str(attachment_path.relative_to(APP_DIR))

    with sqlite3.connect(DB_PATH) as conn:
        try:
            cursor = conn.execute(
                """
                INSERT INTO receipts
                    (fingerprint, access_key, source_url, merchant, purchase_date, total, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    fingerprint,
                    f"MANUAL-{fingerprint[:12]}",
                    attachment_ref,
                    source,
                    purchase_date.isoformat(),
                    total,
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )
        except sqlite3.IntegrityError:
            return False, "Essa despesa manual parece ja ter sido salva."

        receipt_id = cursor.lastrowid
        conn.execute(
            """
            INSERT INTO items
                (receipt_id, product_name, raw_key, normalized_name, category, quantity, unit, unit_price, total_price)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                receipt_id,
                description,
                raw_key,
                normalized_name,
                category,
                quantity,
                str(expense.get("unit") or "UN"),
                unit_price,
                total,
            ),
        )
        upsert_product_rule(conn, raw_key, normalized_name, category)

    return True, "Despesa manual salva no historico."


def load_product_rules(conn: sqlite3.Connection | None = None) -> dict[str, dict]:
    should_close = conn is None
    conn = conn or sqlite3.connect(DB_PATH)
    try:
        rows = conn.execute("SELECT raw_key, display_name, category FROM product_rules").fetchall()
        return {
            raw_key: {"display_name": display_name, "category": category}
            for raw_key, display_name, category in rows
        }
    finally:
        if should_close:
            conn.close()


def upsert_product_rule(conn: sqlite3.Connection, raw_key: str, display_name: str, category: str) -> None:
    conn.execute(
        """
        INSERT INTO product_rules (raw_key, display_name, category, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(raw_key) DO UPDATE SET
            display_name = excluded.display_name,
            category = excluded.category,
            updated_at = excluded.updated_at
        """,
        (raw_key, clean_text(display_name).upper(), category, datetime.now().isoformat(timespec="seconds")),
    )


def update_receipts(receipts_df: pd.DataFrame) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        for row in receipts_df.to_dict("records"):
            conn.execute(
                "UPDATE receipts SET merchant = ?, purchase_date = ? WHERE id = ?",
                (
                    clean_text(str(row["merchant"])),
                    pd.to_datetime(row["purchase_date"]).date().isoformat(),
                    int(row["id"]),
                ),
            )


def update_items(items_df: pd.DataFrame) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        for row in items_df.to_dict("records"):
            raw_key = str(row.get("raw_key") or raw_product_key(str(row["product_name"])))
            normalized_name = clean_text(str(row["normalized_name"])).upper()
            category = str(row["category"])
            conn.execute(
                """
                UPDATE items
                SET normalized_name = ?, category = ?
                WHERE id = ?
                """,
                (normalized_name, category, int(row["id"])),
            )
            upsert_product_rule(conn, raw_key, normalized_name, category)


def update_item_groups(groups_df: pd.DataFrame) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        for row in groups_df.to_dict("records"):
            raw_key = str(row["raw_key"])
            display_name = clean_text(str(row["display_name"])).upper()
            category = str(row["category"])
            upsert_product_rule(conn, raw_key, display_name, category)
            conn.execute(
                """
                UPDATE items
                SET normalized_name = ?, category = ?
                WHERE raw_key = ?
                """,
                (display_name, category, raw_key),
            )


def apply_category_suggestions() -> int:
    receipts, items = load_history()
    changed = 0
    with sqlite3.connect(DB_PATH) as conn:
        for row in items.to_dict("records"):
            suggested = categorize(str(row["product_name"]))
            current = str(row.get("saved_category") or row.get("category") or "")
            if current == "Outros" and suggested != "Outros":
                conn.execute("UPDATE items SET category = ? WHERE id = ?", (suggested, int(row["id"])))
                changed += 1
    return changed


def refresh_receipt_merchants() -> tuple[int, list[str]]:
    receipts, _ = load_history()
    updated = 0
    errors = []
    with sqlite3.connect(DB_PATH) as conn:
        for row in receipts.to_dict("records"):
            source_url = str(row.get("source_url") or "")
            if not source_url.startswith("http"):
                continue
            try:
                receipt = fetch_nfce(source_url)
            except Exception as exc:
                errors.append(f"Cupom {row['id']}: {exc}")
                continue
            if receipt.merchant and receipt.merchant != row.get("merchant"):
                conn.execute("UPDATE receipts SET merchant = ? WHERE id = ?", (receipt.merchant, int(row["id"])))
                updated += 1
    return updated, errors


def load_history() -> tuple[pd.DataFrame, pd.DataFrame]:
    with sqlite3.connect(DB_PATH) as conn:
        receipts = pd.read_sql_query("SELECT * FROM receipts ORDER BY purchase_date DESC", conn)
        items = pd.read_sql_query(
            """
            SELECT i.*, r.purchase_date, r.merchant, r.access_key
            FROM items i
            JOIN receipts r ON r.id = i.receipt_id
            ORDER BY r.purchase_date DESC, i.product_name
            """,
            conn,
        )
    if not receipts.empty:
        receipts["purchase_date"] = pd.to_datetime(receipts["purchase_date"])
    if not items.empty:
        items["purchase_date"] = pd.to_datetime(items["purchase_date"])
        items["month"] = items["purchase_date"].dt.to_period("M").astype(str)
        items["raw_key"] = items.apply(
            lambda row: row["raw_key"] if isinstance(row.get("raw_key"), str) and row["raw_key"] else raw_product_key(str(row["product_name"])),
            axis=1,
        )
        items["saved_category"] = items["category"]
        items["suggested_category"] = items["product_name"].map(categorize)
        items["ipca_group"] = items["category"].map(category_to_ipca_group)
    return receipts, items


def render_metrics(receipts: pd.DataFrame, items: pd.DataFrame, all_items: pd.DataFrame) -> None:
    total_spend = items["total_price"].sum() if not items.empty else 0
    receipt_count = items["receipt_id"].nunique() if not items.empty else 0
    tracked_products = items["normalized_name"].nunique() if not items.empty else 0
    average_ticket = total_spend / receipt_count if receipt_count else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Cupons salvos", receipt_count)
    col2.metric("Gasto registrado", money(total_spend))
    col3.metric("Ticket médio filtrado", money(average_ticket))

    monthly = monthly_basket(all_items)
    if len(monthly) >= 2:
        variation = monthly["basket_total"].pct_change().iloc[-1] * 100
        col4.metric("Inflação mensal registrada", f"{variation:.1f}%")
    else:
        col4.metric("Produtos acompanhados", tracked_products)


def monthly_basket(items: pd.DataFrame) -> pd.DataFrame:
    if items.empty:
        return pd.DataFrame(columns=["month", "basket_total"])
    monthly = items.groupby("month", as_index=False)["total_price"].sum()
    return monthly.rename(columns={"total_price": "basket_total"})


def filter_items(receipts: pd.DataFrame, items: pd.DataFrame) -> pd.DataFrame:
    if items.empty:
        return items

    with st.container(border=True):
        st.markdown("**Filtros do painel**")
        col1, col2, col3, col4 = st.columns([0.9, 1.1, 1.1, 1.1])
        min_date = items["purchase_date"].min().date()
        max_date = items["purchase_date"].max().date()
        selected_dates = col1.date_input("Período", value=(min_date, max_date), min_value=min_date, max_value=max_date)
        categories = col2.multiselect("Categorias", sorted(items["category"].dropna().unique()))
        merchants = col3.multiselect("Mercados", sorted(receipts["merchant"].dropna().unique()))
        query = col4.text_input("Buscar produto", placeholder="leite, arroz, OMO...")

    filtered = items.copy()
    if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
        start, end = selected_dates
        filtered = filtered[(filtered["purchase_date"].dt.date >= start) & (filtered["purchase_date"].dt.date <= end)]
    if categories:
        filtered = filtered[filtered["category"].isin(categories)]
    if merchants:
        filtered = filtered[filtered["merchant"].isin(merchants)]
    if query:
        mask = filtered["product_name"].str.contains(query, case=False, na=False)
        mask |= filtered["normalized_name"].str.contains(query, case=False, na=False)
        filtered = filtered[mask]
    return filtered


def render_single_period_insights(items: pd.DataFrame) -> None:
    if items.empty:
        return

    st.info("Ainda existe apenas um período salvo. O painel já mostra o peso de cada item na sua compra; a curva de inflação aparece automaticamente quando você importar cupons de novos dias ou meses.")
    spend = items["total_price"].sum()
    category = items.groupby("category", as_index=False)["total_price"].sum().sort_values("total_price", ascending=False)
    top_category = category.iloc[0] if not category.empty else None
    top_item = items.sort_values("total_price", ascending=False).iloc[0]

    col1, col2, col3 = st.columns(3)
    if top_category is not None:
        col1.metric("Categoria mais pesada", top_category["category"], money(float(top_category["total_price"])))
    col2.metric("Item de maior impacto", top_item["normalized_name"][:26], money(float(top_item["total_price"])))
    col3.metric("Concentração top 10", f"{items.nlargest(10, 'total_price')['total_price'].sum() / spend * 100:.1f}%")


def estimate_personal_inflation_rate(items: pd.DataFrame) -> tuple[float, str]:
    comparison = build_personal_vs_market(items)
    if not comparison.empty:
        weights = comparison["latest_unit_price"].clip(lower=0.01)
        rate = (comparison["my_rate_pct"] * weights).sum() / weights.sum()
        return float(max(rate, 0.0)), "Inflação observada nos seus itens repetidos"

    market = build_market_reference(items)
    if not market.empty and market["current_total"].sum() > 0:
        rate = (market["market_rate_pct"] * market["current_total"]).sum() / market["current_total"].sum()
        return float(max(rate, 0.0)), "Média de mercado estimada para sua cesta atual"

    return 4.5, "Teto da meta de inflação como referência inicial"


def render_annual_plan(receipts: pd.DataFrame, items: pd.DataFrame) -> None:
    st.subheader("Plano anual de poder de compra")
    st.write(
        "Esta aba transforma seus cupons em uma resposta prática: quanto eu preciso acrescentar no próximo ano para manter o mesmo padrão de compra?"
    )

    if items.empty:
        st.info("Importe ao menos um cupom para montar seu plano anual.")
        return

    base_purchase = float(items["total_price"].sum() / max(items["receipt_id"].nunique(), 1))
    suggested_rate, source = estimate_personal_inflation_rate(items)

    with st.container(border=True):
        col1, col2, col3 = st.columns(3)
        purchases_per_month = col1.number_input("Compras parecidas por mês", min_value=1, max_value=12, value=1, step=1, key="annual_plan_purchases")
        chosen_rate = col2.slider(
            "Inflação usada no plano",
            min_value=0.0,
            max_value=12.0,
            value=round(min(max(suggested_rate, 0.0), 12.0) * 2) / 2,
            step=0.5,
            key="annual_plan_rate",
        )
        months = col3.slider("Meses do próximo ano", min_value=1, max_value=12, value=12, step=1, key="annual_plan_months")

        monthly_now = base_purchase * purchases_per_month
        monthly_needed = monthly_now * (1 + chosen_rate / 100)
        monthly_increase = monthly_needed - monthly_now
        annual_now = monthly_now * months
        annual_needed = monthly_needed * months
        annual_increase = annual_needed - annual_now

        st.caption(f"Referência inicial sugerida: {source} ({suggested_rate:.1f}% a.a.). Você pode ajustar a régua acima.")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Gasto mensal atual", money(monthly_now))
        m2.metric("Mensal necessário", money(monthly_needed), delta=money(monthly_increase))
        m3.metric("Aumento anual necessário", money(annual_increase))
        m4.metric("Orçamento anual protegido", money(annual_needed))

    st.subheader("Leitura do plano")
    st.markdown(
        f"""
        Com base nos cupons analisados, sua referência mensal atual é **{money(monthly_now)}**.

        Se a inflação usada no plano for de **{chosen_rate:.1f}% ao ano**, você precisaria acrescentar cerca de **{money(monthly_increase)} por mês**.

        Para **{months} meses**, isso representa um **aumento anual necessário de {money(annual_increase)}** para preservar o poder de compra da sua cesta atual.
        """
    )

    category = (
        items.groupby("category", as_index=False)["total_price"]
        .sum()
        .sort_values("total_price", ascending=False)
    )
    category["monthly_now"] = category["total_price"] / max(items["receipt_id"].nunique(), 1) * purchases_per_month
    category["monthly_increase"] = category["monthly_now"] * (chosen_rate / 100)
    category["annual_increase"] = category["monthly_increase"] * months

    st.subheader("Aumento anual por categoria")
    left, right = st.columns([1.05, 0.95])
    with left:
        st.bar_chart(category.set_index("category")["annual_increase"])
    with right:
        st.dataframe(
            category.assign(
                monthly_now=category["monthly_now"].map(money),
                monthly_increase=category["monthly_increase"].map(money),
                annual_increase=category["annual_increase"].map(money),
            )[["category", "monthly_now", "monthly_increase", "annual_increase"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "category": "Categoria",
                "monthly_now": "Base mensal",
                "monthly_increase": "Acréscimo mensal",
                "annual_increase": "Aumento anual",
            },
        )


def render_product_explorer(items: pd.DataFrame) -> None:
    if items.empty:
        return

    st.subheader("Explorador de produtos")
    top_n = st.slider("Quantidade de itens no ranking", min_value=5, max_value=min(50, len(items)), value=min(15, len(items)), step=5)
    ranking = (
        items.groupby(["normalized_name", "category"], as_index=False)
        .agg(
            total_price=("total_price", "sum"),
            quantity=("quantity", "sum"),
            avg_unit_price=("unit_price", "mean"),
            purchases=("id", "count"),
        )
        .sort_values("total_price", ascending=False)
    )
    ranking["share"] = ranking["total_price"] / ranking["total_price"].sum() * 100
    top = ranking.head(top_n)

    left, right = st.columns([1.1, 0.9])
    with left:
        st.bar_chart(top.set_index("normalized_name")["total_price"])
    with right:
        st.dataframe(
            top.assign(
                total_price=top["total_price"].map(money),
                avg_unit_price=top["avg_unit_price"].map(money),
                share=top["share"].map(lambda value: f"{value:.1f}%"),
            )[["normalized_name", "category", "total_price", "avg_unit_price", "share"]],
            use_container_width=True,
            hide_index=True,
        )

    default_products = top["normalized_name"].head(3).tolist()
    selected_products = st.multiselect("Comparar preço unitário", ranking["normalized_name"].tolist(), default=default_products)
    if selected_products:
        comparison = items[items["normalized_name"].isin(selected_products)].copy()
        comparison["date_label"] = comparison["purchase_date"].dt.strftime("%d/%m/%Y")
        pivot = comparison.pivot_table(
            index="date_label",
            columns="normalized_name",
            values="unit_price",
            aggfunc="mean",
        )
        st.line_chart(pivot)


def estimate_stock_savings(receipts: pd.DataFrame, items: pd.DataFrame) -> pd.DataFrame:
    if receipts.empty or items.empty or receipts["id"].nunique() < 2:
        return pd.DataFrame()

    ordered_receipts = receipts.sort_values(["purchase_date", "id"])[["id", "purchase_date", "merchant"]]
    receipt_order = ordered_receipts["id"].tolist()
    grouped_items = (
        items.groupby(["receipt_id", "raw_key"], as_index=False)
        .agg(
            normalized_name=("normalized_name", "first"),
            category=("category", "first"),
            quantity=("quantity", "sum"),
            total_price=("total_price", "sum"),
            unit_price=("unit_price", "mean"),
            purchase_date=("purchase_date", "first"),
            merchant=("merchant", "first"),
        )
    )

    last_purchase: dict[str, dict] = {}
    savings_rows = []

    for receipt_id in receipt_order:
        receipt_meta = ordered_receipts[ordered_receipts["id"] == receipt_id].iloc[0]
        current_items = grouped_items[grouped_items["receipt_id"] == receipt_id]
        current_keys = set(current_items["raw_key"])

        for raw_key, previous in last_purchase.items():
            if raw_key in current_keys:
                continue
            days_since = (receipt_meta["purchase_date"] - previous["purchase_date"]).days
            savings_rows.append(
                {
                    "period_receipt_id": receipt_id,
                    "period_date": receipt_meta["purchase_date"],
                    "period_merchant": receipt_meta["merchant"],
                    "raw_key": raw_key,
                    "normalized_name": previous["normalized_name"],
                    "category": previous["category"],
                    "last_purchase_date": previous["purchase_date"],
                    "last_merchant": previous["merchant"],
                    "last_quantity": previous["quantity"],
                    "last_unit_price": previous["unit_price"],
                    "avoided_total": previous["total_price"],
                    "days_since_purchase": days_since,
                    "reason": "Ainda usando compra anterior",
                }
            )

        for row in current_items.to_dict("records"):
            last_purchase[row["raw_key"]] = row

    return pd.DataFrame(savings_rows)


def render_stock_savings(receipts: pd.DataFrame, items: pd.DataFrame) -> None:
    st.subheader("Economia por estoque em uso")
    if receipts["id"].nunique() < 2:
        st.info("Quando você subir o próximo cupom, esta seção vai calcular item a item o que você deixou de recomprar porque ainda estava usando a compra anterior.")
        return

    savings = estimate_stock_savings(receipts, items)
    if savings.empty:
        st.success("No comparativo atual, todos os itens recorrentes foram recomprados ou ainda não há ausência suficiente para estimar economia.")
        return

    category_filter = st.multiselect(
        "Filtrar economia por categoria",
        sorted(savings["category"].dropna().unique()),
        key="stock_savings_categories",
    )
    filtered = savings[savings["category"].isin(category_filter)] if category_filter else savings

    latest_date = filtered["period_date"].max()
    latest = filtered[filtered["period_date"] == latest_date]
    total_avoided = float(filtered["avoided_total"].sum())
    latest_avoided = float(latest["avoided_total"].sum())

    col1, col2, col3 = st.columns(3)
    col1.metric("Economia estimada acumulada", money(total_avoided))
    col2.metric("Economia no último cupom", money(latest_avoided))
    col3.metric("Itens não recomprados", filtered["raw_key"].nunique())

    by_product = (
        filtered.groupby(["normalized_name", "category"], as_index=False)
        .agg(
            avoided_total=("avoided_total", "sum"),
            periods=("period_receipt_id", "count"),
            last_unit_price=("last_unit_price", "last"),
            last_quantity=("last_quantity", "last"),
        )
        .sort_values("avoided_total", ascending=False)
    )
    top = by_product.head(20)

    left, right = st.columns([1.05, 0.95])
    with left:
        st.bar_chart(top.set_index("normalized_name")["avoided_total"])
    with right:
        st.dataframe(
            top.assign(
                avoided_total=top["avoided_total"].map(money),
                last_unit_price=top["last_unit_price"].map(money),
            )[["normalized_name", "category", "periods", "last_quantity", "last_unit_price", "avoided_total"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "normalized_name": "Produto",
                "category": "Categoria",
                "periods": "Cupons sem recompra",
                "last_quantity": "Qtd. anterior",
                "last_unit_price": "Preço unit. anterior",
                "avoided_total": "Economia estimada",
            },
        )

    with st.expander("Ver cálculo item a item"):
        detail = filtered.sort_values(["period_date", "avoided_total"], ascending=[False, False]).copy()
        detail["period_date"] = detail["period_date"].dt.strftime("%d/%m/%Y")
        detail["last_purchase_date"] = detail["last_purchase_date"].dt.strftime("%d/%m/%Y")
        st.dataframe(
            detail.assign(
                last_unit_price=detail["last_unit_price"].map(money),
                avoided_total=detail["avoided_total"].map(money),
            )[
                [
                    "period_date",
                    "period_merchant",
                    "normalized_name",
                    "category",
                    "last_purchase_date",
                    "last_quantity",
                    "last_unit_price",
                    "avoided_total",
                    "days_since_purchase",
                    "reason",
                ]
            ],
            use_container_width=True,
            hide_index=True,
            column_config={
                "period_date": "Cupom atual",
                "period_merchant": "Mercado atual",
                "normalized_name": "Produto não recomprado",
                "category": "Categoria",
                "last_purchase_date": "Compra anterior",
                "last_quantity": "Qtd. anterior",
                "last_unit_price": "Preço unit. anterior",
                "avoided_total": "Economia estimada",
                "days_since_purchase": "Dias desde a compra",
                "reason": "Motivo assumido",
            },
        )


def render_data_editor(receipts: pd.DataFrame, items: pd.DataFrame) -> None:
    if receipts.empty or items.empty:
        st.info("Nenhum dado salvo para ajustar ainda.")
        return

    st.subheader("Ajustar mercado e categorias")
    st.write("Edite o nome do mercado, o produto acompanhado e a categoria. Ao salvar, o dashboard passa a usar esses valores.")

    with st.container(border=True):
        st.markdown("**Mercados dos cupons**")
        receipt_editor = receipts[["id", "purchase_date", "merchant", "total"]].copy()
        receipt_editor["purchase_date"] = receipt_editor["purchase_date"].dt.date
        edited_receipts = st.data_editor(
            receipt_editor,
            use_container_width=True,
            hide_index=True,
            disabled=["id", "total"],
            column_config={
                "id": "ID",
                "purchase_date": st.column_config.DateColumn("Data"),
                "merchant": st.column_config.TextColumn("Mercado"),
                "total": st.column_config.NumberColumn("Total", format="R$ %.2f"),
            },
            key="receipt_editor",
        )
        col1, col2 = st.columns(2)
        if col1.button("Salvar mercados", type="primary", use_container_width=True):
            update_receipts(edited_receipts)
            st.success("Mercados atualizados.")
            st.rerun()
        if col2.button("Rebuscar mercado pelo QR Code", use_container_width=True):
            updated, errors = refresh_receipt_merchants()
            if updated:
                st.success(f"{updated} cupom(ns) atualizado(s).")
                st.rerun()
            elif errors:
                st.warning("Nao consegui atualizar automaticamente: " + " | ".join(errors[:3]))
            else:
                st.info("Nenhum mercado novo encontrado.")

    with st.container(border=True):
        st.markdown("**Agrupar nomes lidos da SEFAZ**")
        st.caption("Edite uma linha aqui para mudar todos os itens com o mesmo nome-base do cupom e ensinar o app para os próximos cupons.")
        groups = (
            items.groupby("raw_key", as_index=False)
            .agg(
                display_name=("normalized_name", lambda values: values.mode().iat[0] if not values.mode().empty else values.iloc[0]),
                category=("category", lambda values: values.mode().iat[0] if not values.mode().empty else values.iloc[0]),
                suggestion=("suggested_category", lambda values: values.mode().iat[0] if not values.mode().empty else values.iloc[0]),
                examples=("product_name", lambda values: " | ".join(values.drop_duplicates().head(3))),
                items=("id", "count"),
                total_price=("total_price", "sum"),
                avg_unit_price=("unit_price", "mean"),
            )
            .sort_values("total_price", ascending=False)
        )
        only_other_groups = st.toggle("Mostrar apenas grupos em Outros", value=False)
        group_editor = groups[groups["category"] == "Outros"].copy() if only_other_groups else groups.copy()

        edited_groups = st.data_editor(
            group_editor,
            use_container_width=True,
            hide_index=True,
            disabled=["raw_key", "suggestion", "examples", "items", "total_price", "avg_unit_price"],
            column_config={
                "raw_key": "Nome-base SEFAZ",
                "display_name": st.column_config.TextColumn("Produto acompanhado"),
                "category": st.column_config.SelectboxColumn("Categoria final", options=CATEGORIES, required=True),
                "suggestion": "Sugestão",
                "examples": "Exemplos no cupom",
                "items": "Itens",
                "total_price": st.column_config.NumberColumn("Total", format="R$ %.2f"),
                "avg_unit_price": st.column_config.NumberColumn("Preço médio", format="R$ %.2f"),
            },
            key="group_editor",
        )
        if st.button("Salvar regras de agrupamento", type="primary", use_container_width=True):
            update_item_groups(edited_groups)
            st.success("Agrupamentos salvos. O dashboard e os próximos cupons passam a usar essas regras.")
            st.rerun()

    with st.container(border=True):
        st.markdown("**Ajuste fino por item**")
        only_other = st.toggle("Mostrar apenas itens ainda salvos em Outros", value=False)
        item_editor = items.copy()
        if only_other:
            item_editor = item_editor[item_editor["saved_category"] == "Outros"]
        item_editor = item_editor[
            [
                "id",
                "raw_key",
                "purchase_date",
                "product_name",
                "normalized_name",
                "saved_category",
                "suggested_category",
                "category",
                "quantity",
                "unit",
                "unit_price",
                "total_price",
            ]
        ].sort_values("total_price", ascending=False)
        item_editor["purchase_date"] = item_editor["purchase_date"].dt.date

        if item_editor.empty:
            st.success("Nenhum item em Outros com o filtro atual.")
        else:
            edited_items = st.data_editor(
                item_editor,
                use_container_width=True,
                hide_index=True,
                disabled=[
                    "id",
                    "raw_key",
                    "purchase_date",
                    "product_name",
                    "saved_category",
                    "suggested_category",
                    "quantity",
                    "unit",
                    "unit_price",
                    "total_price",
                ],
                column_config={
                    "id": "ID",
                    "raw_key": "Nome-base SEFAZ",
                    "purchase_date": "Data",
                    "product_name": "Produto no cupom",
                    "normalized_name": st.column_config.TextColumn("Produto acompanhado"),
                    "saved_category": "Categoria salva",
                    "suggested_category": "Sugestão",
                    "category": st.column_config.SelectboxColumn("Categoria", options=CATEGORIES, required=True),
                    "quantity": "Qtd.",
                    "unit": "Un.",
                    "unit_price": st.column_config.NumberColumn("Preço unit.", format="R$ %.2f"),
                    "total_price": st.column_config.NumberColumn("Total", format="R$ %.2f"),
                },
                key="item_editor",
            )
            col1, col2 = st.columns(2)
            if col1.button("Salvar produtos e categorias", type="primary", use_container_width=True):
                update_items(edited_items)
                st.success("Itens atualizados.")
                st.rerun()
            if col2.button("Aplicar sugestões automáticas", use_container_width=True):
                changed = apply_category_suggestions()
                st.success(f"{changed} item(ns) categorizado(s) automaticamente.")
                st.rerun()


def render_dashboard(receipts: pd.DataFrame, items: pd.DataFrame) -> None:
    if receipts.empty or items.empty:
        st.info("Salve o primeiro cupom para liberar os graficos da sua inflação pessoal.")
        return

    filtered = filter_items(receipts, items)
    if filtered.empty:
        st.warning("Nenhum item encontrado com os filtros atuais.")
        return

    render_metrics(receipts, filtered, items)

    st.divider()
    if items["month"].nunique() < 2:
        render_single_period_insights(filtered)

    left, right = st.columns([1.15, 0.85])

    with left:
        if filtered["month"].nunique() >= 2:
            st.subheader("Cesta registrada por mês")
            monthly = monthly_basket(filtered)
            chart_data = monthly.set_index("month")["basket_total"]
            st.line_chart(chart_data)
        else:
            st.subheader("Peso por categoria")
            category_chart = filtered.groupby("category")["total_price"].sum().sort_values(ascending=False)
            st.bar_chart(category_chart)

    with right:
        st.subheader("Resumo por categoria")
        category = filtered.groupby("category", as_index=False)["total_price"].sum().sort_values("total_price", ascending=False)
        category["share"] = category["total_price"] / category["total_price"].sum() * 100
        st.dataframe(
            category.assign(
                total_price=category["total_price"].map(money),
                share=category["share"].map(lambda value: f"{value:.1f}%"),
            ),
            use_container_width=True,
            hide_index=True,
        )

    render_product_explorer(filtered)

    ranking = (
        filtered.groupby(["normalized_name", "month"], as_index=False)["unit_price"]
        .mean()
        .sort_values(["normalized_name", "month"])
    )
    ranking["prev_price"] = ranking.groupby("normalized_name")["unit_price"].shift(1)
    ranking["change_pct"] = ((ranking["unit_price"] / ranking["prev_price"]) - 1) * 100
    latest_month = ranking["month"].max()
    movers = ranking[(ranking["month"] == latest_month) & ranking["change_pct"].notna()]
    movers = movers.sort_values("change_pct", ascending=False).head(10)
    if not movers.empty:
        st.subheader("Itens que mais subiram no ultimo mês importado")
        st.dataframe(
            movers[["normalized_name", "unit_price", "prev_price", "change_pct"]].assign(
                unit_price=movers["unit_price"].map(money),
                prev_price=movers["prev_price"].map(money),
                change_pct=movers["change_pct"].map(lambda value: f"{value:.1f}%"),
            ),
            use_container_width=True,
            hide_index=True,
        )

def compound_rate(*rates: float) -> float:
    factor = 1.0
    for rate in rates:
        factor *= 1 + (rate / 100)
    return (factor - 1) * 100


def market_reference_for_item(row: pd.Series) -> tuple[float, str]:
    name = f"{row.get('normalized_name', '')} {row.get('product_name', '')}".upper()
    category = str(row.get("category") or "")
    jan_apr_food = 3.44
    may_food_preview = 1.38
    food_reference = compound_rate(jan_apr_food, may_food_preview)

    item_rules = [
        ("BATATA", compound_rate(jan_apr_food, 26.29), "IPCA alimento + IPCA-15 maio: batata-inglesa"),
        ("TOMATE", compound_rate(jan_apr_food, 12.97), "IPCA alimento + IPCA-15 maio: tomate"),
        ("LEITE", compound_rate(jan_apr_food, 6.07), "IPCA alimento + IPCA-15 maio: leite longa vida"),
        ("LTE", compound_rate(jan_apr_food, 6.07), "IPCA alimento + IPCA-15 maio: leite longa vida"),
        ("CARNE", compound_rate(jan_apr_food, 1.98), "IPCA alimento + IPCA-15 maio: carnes"),
        ("BOV", compound_rate(jan_apr_food, 1.98), "IPCA alimento + IPCA-15 maio: carnes"),
        ("FRANGO", compound_rate(jan_apr_food, 1.98), "IPCA alimento + IPCA-15 maio: carnes"),
        ("CAFE", compound_rate(jan_apr_food, -2.09), "IPCA alimento + IPCA-15 maio: café moído"),
        ("MACA", compound_rate(jan_apr_food, -2.32), "IPCA alimento + IPCA-15 maio: maçã"),
    ]
    for token, rate, source in item_rules:
        if token in name:
            return rate, source

    if category in {"Arroz, feijão e grãos", "Bebidas", "Café e mercearia", "Carnes e ovos", "Hortifruti", "Laticínios", "Mercearia geral", "Padaria"}:
        return food_reference, "IPCA Alimentação e Bebidas jan-abr + IPCA-15 maio"
    if category == "Higiene":
        return 1.60, "IPCA-15 maio: higiene pessoal"
    if category == "Limpeza":
        return 3.02, "IPCA-15 acumulado do ano como proxy geral"
    return 3.02, "IPCA-15 acumulado do ano como proxy geral"


def scale_market_rate_to_period(rate_pct: float, start_date: pd.Timestamp, end_date: pd.Timestamp) -> float:
    reference_start = pd.Timestamp("2026-01-01")
    reference_end = pd.Timestamp("2026-06-01")
    reference_days = max((reference_end - reference_start).days, 1)
    period_days = max((pd.Timestamp(end_date) - pd.Timestamp(start_date)).days, 0)
    if period_days == 0:
        return 0.0
    return ((1 + rate_pct / 100) ** (period_days / reference_days) - 1) * 100


def build_market_reference(items: pd.DataFrame) -> pd.DataFrame:
    if items.empty:
        return pd.DataFrame()

    base = (
        items.groupby(["raw_key", "normalized_name", "category"], as_index=False)
        .agg(
            current_unit_price=("unit_price", "mean"),
            current_total=("total_price", "sum"),
            quantity=("quantity", "sum"),
            purchases=("id", "count"),
        )
        .sort_values("current_total", ascending=False)
    )
    references = base.apply(market_reference_for_item, axis=1)
    base["market_rate_pct"] = [item[0] for item in references]
    base["reference_source"] = [item[1] for item in references]
    base["estimated_january_unit_price"] = base["current_unit_price"] / (1 + base["market_rate_pct"] / 100)
    base["estimated_increase_per_unit"] = base["current_unit_price"] - base["estimated_january_unit_price"]
    base["estimated_increase_total"] = base["estimated_increase_per_unit"] * base["quantity"]
    return base


def build_personal_vs_market(items: pd.DataFrame) -> pd.DataFrame:
    if items.empty:
        return pd.DataFrame()

    rows = []
    grouped = (
        items.groupby(["raw_key", "purchase_date"], as_index=False)
        .agg(
            normalized_name=("normalized_name", "first"),
            category=("category", "first"),
            unit_price=("unit_price", "mean"),
            quantity=("quantity", "sum"),
            total_price=("total_price", "sum"),
            receipt_id=("receipt_id", "first"),
        )
        .sort_values(["raw_key", "purchase_date", "receipt_id"])
    )

    for raw_key, history in grouped.groupby("raw_key"):
        history = history.sort_values(["purchase_date", "receipt_id"])
        if history["purchase_date"].nunique() < 2:
            continue
        first = history.iloc[0]
        latest = history.iloc[-1]
        if not first["unit_price"]:
            continue
        my_rate = ((latest["unit_price"] / first["unit_price"]) - 1) * 100
        market_full_rate, source = market_reference_for_item(latest)
        market_period_rate = scale_market_rate_to_period(
            market_full_rate,
            pd.Timestamp(first["purchase_date"]),
            pd.Timestamp(latest["purchase_date"]),
        )
        difference = my_rate - market_period_rate
        rows.append(
            {
                "raw_key": raw_key,
                "normalized_name": latest["normalized_name"],
                "category": latest["category"],
                "first_date": first["purchase_date"],
                "latest_date": latest["purchase_date"],
                "first_unit_price": first["unit_price"],
                "latest_unit_price": latest["unit_price"],
                "my_rate_pct": my_rate,
                "market_rate_pct": market_period_rate,
                "difference_pct": difference,
                "status": "Acima da média" if difference > 1 else "Abaixo da média" if difference < -1 else "Em linha",
                "reference_source": source,
            }
        )
    return pd.DataFrame(rows)


def render_personal_vs_market(items: pd.DataFrame) -> None:
    st.subheader("Minha compra vs média do período")
    comparison = build_personal_vs_market(items)
    if comparison.empty:
        st.info(
            "Ainda não há itens repetidos em cupons de datas diferentes. "
            "Assim que você subir outro cupom com produtos já comprados antes, esta área mostra se você pagou acima, igual ou abaixo da média de mercado no mesmo período."
        )
        return

    latest_weight = comparison["latest_unit_price"].clip(lower=0.01)
    my_avg = (comparison["my_rate_pct"] * latest_weight).sum() / latest_weight.sum()
    market_avg = (comparison["market_rate_pct"] * latest_weight).sum() / latest_weight.sum()
    gap = my_avg - market_avg

    col1, col2, col3 = st.columns(3)
    col1.metric("Minha inflação média", f"{my_avg:.1f}%")
    col2.metric("Média de mercado no período", f"{market_avg:.1f}%")
    col3.metric("Diferença", f"{gap:+.1f} p.p.")

    st.dataframe(
        comparison.sort_values("difference_pct", ascending=False).assign(
            first_date=comparison["first_date"].dt.strftime("%d/%m/%Y"),
            latest_date=comparison["latest_date"].dt.strftime("%d/%m/%Y"),
            first_unit_price=comparison["first_unit_price"].map(money),
            latest_unit_price=comparison["latest_unit_price"].map(money),
            my_rate_pct=comparison["my_rate_pct"].map(lambda value: f"{value:.1f}%"),
            market_rate_pct=comparison["market_rate_pct"].map(lambda value: f"{value:.1f}%"),
            difference_pct=comparison["difference_pct"].map(lambda value: f"{value:+.1f} p.p."),
        )[
            [
                "normalized_name",
                "category",
                "first_date",
                "latest_date",
                "first_unit_price",
                "latest_unit_price",
                "my_rate_pct",
                "market_rate_pct",
                "difference_pct",
                "status",
                "reference_source",
            ]
        ],
        use_container_width=True,
        hide_index=True,
        column_config={
            "normalized_name": "Produto",
            "category": "Categoria",
            "first_date": "Compra anterior",
            "latest_date": "Compra atual",
            "first_unit_price": "Preço anterior",
            "latest_unit_price": "Preço atual",
            "my_rate_pct": "Minha variação",
            "market_rate_pct": "Média mercado",
            "difference_pct": "Minha diferença",
            "status": "Leitura",
            "reference_source": "Fonte/regra",
        },
    )


def render_market_reference(receipts: pd.DataFrame, items: pd.DataFrame) -> None:
    st.subheader("Média de mercado")
    st.write("Uma comparação estimada para quem ainda não tem histórico próprio suficiente. Ela não substitui seus cupons: serve como norte externo para janeiro até agora.")

    if items.empty:
        st.info("Importe um cupom para comparar seus itens com a média de mercado.")
        return

    st.info(
        "Referência usada: Alimentação e Bebidas acumulou 3,44% de janeiro a abril de 2026, e o IPCA-15 de maio mostrou alta de 1,38% em Alimentação e Bebidas. "
        "Para alguns itens, o app usa destaques do IPCA-15 de maio, como leite longa vida, tomate, batata, carnes, café e maçã."
    )

    render_personal_vs_market(items)
    st.divider()

    comparison = build_market_reference(items)
    category_filter = st.multiselect(
        "Categorias",
        sorted(comparison["category"].dropna().unique()),
        key="market_reference_categories",
    )
    filtered = comparison[comparison["category"].isin(category_filter)] if category_filter else comparison

    if filtered.empty:
        st.warning("Nenhum item encontrado para as categorias selecionadas.")
        return

    weighted_rate = (filtered["market_rate_pct"] * filtered["current_total"]).sum() / filtered["current_total"].sum()
    estimated_jan_total = (filtered["current_total"] / (1 + filtered["market_rate_pct"] / 100)).sum()
    estimated_now_total = filtered["current_total"].sum()
    estimated_gap = estimated_now_total - estimated_jan_total

    col1, col2, col3 = st.columns(3)
    col1.metric("Inflação média estimada", f"{weighted_rate:.1f}%")
    col2.metric("Cesta estimada em janeiro", money(float(estimated_jan_total)))
    col3.metric("Diferença estimada", money(float(estimated_gap)))

    left, right = st.columns([1.05, 0.95])
    top = filtered.sort_values("estimated_increase_total", ascending=False).head(20)
    with left:
        st.subheader("Itens com maior pressão estimada")
        st.bar_chart(top.set_index("normalized_name")["estimated_increase_total"])
    with right:
        st.subheader("Resumo por categoria")
        category = (
            filtered.groupby("category", as_index=False)
            .agg(
                current_total=("current_total", "sum"),
                estimated_increase_total=("estimated_increase_total", "sum"),
                market_rate_pct=("market_rate_pct", "mean"),
            )
            .sort_values("estimated_increase_total", ascending=False)
        )
        st.dataframe(
            category.assign(
                current_total=category["current_total"].map(money),
                estimated_increase_total=category["estimated_increase_total"].map(money),
                market_rate_pct=category["market_rate_pct"].map(lambda value: f"{value:.1f}%"),
            ),
            use_container_width=True,
            hide_index=True,
            column_config={
                "category": "Categoria",
                "current_total": "Total atual",
                "estimated_increase_total": "Pressão estimada",
                "market_rate_pct": "Média ref.",
            },
        )

    st.subheader("Comparativo item a item")
    display = filtered.sort_values("estimated_increase_total", ascending=False).copy()
    st.dataframe(
        display.assign(
            current_unit_price=display["current_unit_price"].map(money),
            estimated_january_unit_price=display["estimated_january_unit_price"].map(money),
            estimated_increase_per_unit=display["estimated_increase_per_unit"].map(money),
            estimated_increase_total=display["estimated_increase_total"].map(money),
            market_rate_pct=display["market_rate_pct"].map(lambda value: f"{value:.1f}%"),
        )[
            [
                "normalized_name",
                "category",
                "current_unit_price",
                "estimated_january_unit_price",
                "market_rate_pct",
                "estimated_increase_per_unit",
                "estimated_increase_total",
                "reference_source",
            ]
        ],
        use_container_width=True,
        hide_index=True,
        column_config={
            "normalized_name": "Produto",
            "category": "Categoria",
            "current_unit_price": "Preço atual cupom",
            "estimated_january_unit_price": "Preço jan estimado",
            "market_rate_pct": "Inflação média ref.",
            "estimated_increase_per_unit": "Dif. unitária",
            "estimated_increase_total": "Dif. na cesta",
            "reference_source": "Fonte/regra",
        },
    )

    with st.expander("Fontes e limites da comparação"):
        st.write(
            "Esta aba usa índices públicos agregados e destaques por item quando disponíveis. "
            "Ela não consulta histórico de preço online do Assaí/SENDAS item a item, porque preços de e-commerce mudam, podem variar por CEP e raramente expõem histórico de janeiro. "
            "Por isso, a aba é classificada como média de mercado e deve aparecer separada da sua inflação real."
        )
        st.markdown(
            """
            Fontes usadas como referência:
            - IBGE/IPCA: Alimentação e Bebidas acumulado de janeiro a abril de 2026: 3,44%.
            - IBGE/IPCA-15 maio de 2026: Alimentação e Bebidas 1,38%; alimentação no domicílio 1,73%.
            - Destaques IPCA-15 maio: batata-inglesa 26,29%, tomate 12,97%, leite longa vida 6,07%, carnes 1,98%, higiene pessoal 1,60%, maçã -2,32% e café moído -2,09%.
            """
        )


def render_ipca_groups_guide(receipts: pd.DataFrame, items: pd.DataFrame) -> None:
    st.subheader("Grupos IPCA")
    st.write(
        "O IPCA oficial mede a inflação em 9 grupos de consumo. "
        "O Minha Inflação usa essa estrutura como linguagem didática, mas calcula a inflação da pessoa ou do grupo com base nos itens realmente importados."
    )

    col1, col2 = st.columns([0.58, 0.42])

    official = pd.DataFrame(IPCA_GROUPS)
    with col1:
        st.markdown("**Visão oficial, traduzida para o uso do app**")
        st.dataframe(
            official,
            use_container_width=True,
            hide_index=True,
            column_config={
                "group": "Grupo IPCA",
                "plain_language": "O que significa",
                "app_examples": "Como pode aparecer no Minha Inflação",
            },
        )

    with col2:
        st.markdown("**Como ler o cálculo no app**")
        st.info(
            "Individual: o app calcula a inflação da sua cesta. "
            "Grupo: o mesmo cálculo pode ser agregado e anonimizado para famílias, condomínios, empresas ou comunidades."
        )
        st.markdown(
            """
            O IPCA completo inclui despesas que não aparecem em cupom de mercado, como aluguel, energia, transporte, educação e internet.

            Por isso, quando você sobe apenas cupons de supermercado, a cobertura tende a ficar concentrada em:
            - Alimentação e bebidas
            - Habitação, quando houver limpeza doméstica
            - Saúde e cuidados pessoais, quando houver higiene/farmácia
            """
        )

    st.divider()
    st.subheader("Cobertura atual da sua base")
    if items.empty:
        st.info("Importe um cupom para ver quais grupos do IPCA já aparecem na sua inflação individual.")
        return

    coverage = (
        items.groupby("ipca_group", as_index=False)
        .agg(
            total_price=("total_price", "sum"),
            items=("id", "count"),
            products=("normalized_name", "nunique"),
        )
        .sort_values("total_price", ascending=False)
    )
    all_groups = pd.DataFrame({"ipca_group": [item["group"] for item in IPCA_GROUPS]})
    coverage = all_groups.merge(coverage, on="ipca_group", how="left").fillna(
        {"total_price": 0, "items": 0, "products": 0}
    )
    total = float(coverage["total_price"].sum())
    coverage["share"] = coverage["total_price"].apply(lambda value: (value / total * 100) if total else 0)
    coverage["status"] = coverage["total_price"].apply(lambda value: "Com dados dos cupons" if value > 0 else "Sem dados ainda")

    m1, m2, m3 = st.columns(3)
    m1.metric("Grupos com dados", int((coverage["total_price"] > 0).sum()))
    m2.metric("Grupos oficiais", len(IPCA_GROUPS))
    m3.metric("Base analisada", money(total))

    left, right = st.columns([1.05, 0.95])
    with left:
        chart = coverage[coverage["total_price"] > 0].set_index("ipca_group")["total_price"]
        if chart.empty:
            st.info("Nenhum grupo com gasto identificado ainda.")
        else:
            st.bar_chart(chart)
    with right:
        display = coverage.copy()
        st.dataframe(
            display.assign(
                total_price=display["total_price"].map(money),
                share=display["share"].map(lambda value: f"{value:.1f}%"),
                items=display["items"].astype(int),
                products=display["products"].astype(int),
            ),
            use_container_width=True,
            hide_index=True,
            column_config={
                "ipca_group": "Grupo IPCA",
                "total_price": "Valor na base",
                "items": "Itens",
                "products": "Produtos",
                "share": "Peso",
                "status": "Status",
            },
        )

    with st.expander("Por que isso importa?"):
        st.write(
            "Quando o usuário vê os grupos IPCA, ele entende que o app não está tentando copiar o IPCA oficial. "
            "Ele está criando um índice individual ou coletivo em cima da cesta real daquela pessoa ou daquele grupo. "
            "Quanto mais tipos de despesas forem cadastrados, mais ampla fica a leitura da inflação pessoal."
        )


def render_cover() -> None:
    st.markdown(
        """
        <section class="mi-cover">
          <div>
            <div class="mi-cover__eyebrow">Nasceu de uma compra de mercado que assustou</div>
            <h1>Minha Inflação</h1>
            <p>Eu criei este painel para entender onde a minha compra ficou mais cara. A ideia é simples: subir os cupons, acompanhar item por item e enxergar se a inflação chegou de verdade na minha cesta.</p>
          </div>
          <div class="mi-cover__side">
            <div class="mi-cover__visual" aria-label="Gráfico de inflação e cupom fiscal"></div>
            <div class="mi-cover__panel">
              <div class="mi-cover__row">
                <div class="mi-cover__icon">QR</div>
                <div><strong>Começo pelo cupom</strong><span>Leio o QR Code da NFC-e para organizar a compra sem digitar item por item.</span></div>
              </div>
              <div class="mi-cover__row">
                <div class="mi-cover__icon">%</div>
                <div><strong>Olho produto por produto</strong><span>Vejo preço, categoria e variação para entender o que realmente pesou.</span></div>
              </div>
              <div class="mi-cover__row">
                <div class="mi-cover__icon">R$</div>
                <div><strong>Uso como um guia pessoal</strong><span>Comparo minha cesta com referências de mercado e planejo a próxima compra com mais clareza.</span></div>
              </div>
            </div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_home(receipts: pd.DataFrame, items: pd.DataFrame) -> None:
    render_cover()

    if receipts.empty or items.empty:
        st.info("Comece importando seu primeiro cupom. Depois disso, o app libera o dashboard, as comparações e o plano anual.")
        return

    latest_date = receipts["purchase_date"].max()
    latest_label = latest_date.strftime("%d/%m/%Y") if pd.notna(latest_date) else "-"

    col1, col2, col3 = st.columns(3)
    col1.metric("Cupons salvos", int(receipts["id"].nunique()))
    col2.metric("Itens acompanhados", int(items["normalized_name"].nunique()))
    col3.metric("Última compra", latest_label)

    st.caption("Use o Dashboard para enxergar o que pesou, o Plano anual para proteger seu poder de compra e Análises para comparar com mercado, estoque e grupos IPCA.")


def render_importer() -> None:
    st.subheader("Importar cupom pelo QR Code")
    st.caption("Cole aqui o link aberto pelo QR Code da NFC-e. Quando a SEFAZ entregar os itens na pagina, o app importa tudo em formato revisavel.")

    url = st.text_input("Link do QR Code / NFC-e", placeholder="https://.../NFCeConsultaPublica?p=...")
    qr_upload = st.file_uploader("Ou envie uma imagem do QR Code", type=["png", "jpg", "jpeg"])
    html_upload = st.file_uploader("Ou envie um HTML salvo da pagina da NFC-e", type=["html", "htm", "txt"])

    col1, col2 = st.columns([0.35, 0.65])
    import_clicked = col1.button("Ler cupom", type="primary", use_container_width=True)
    clear_clicked = col2.button("Limpar importação atual", use_container_width=True)

    if clear_clicked:
        st.session_state.pop("receipt", None)
        st.session_state.pop("items_editor", None)
        st.rerun()

    if import_clicked:
        try:
            resolved_url = url.strip()
            if not resolved_url and qr_upload is not None:
                resolved_url = decode_qr_image(qr_upload).strip()

            if resolved_url:
                receipt = fetch_nfce(resolved_url)
            elif html_upload is not None:
                raw = html_upload.getvalue().decode("utf-8", errors="ignore")
                receipt = parse_nfce_html(raw, html_upload.name)
            else:
                st.warning("Cole o link do QR Code, envie a imagem do QR Code ou envie o HTML da pagina.")
                return
            if not receipt.items:
                st.error("Consegui abrir o cupom, mas nao encontrei a lista de produtos. Use a opção de HTML salvo ou me mande um exemplo do link para ajustarmos o parser do seu estado.")
                return
            st.session_state["receipt"] = receipt
            st.session_state["items_editor"] = pd.DataFrame(receipt.items)
        except Exception as exc:
            st.error(f"Nao consegui importar esse cupom: {exc}")

    receipt: Receipt | None = st.session_state.get("receipt")
    if not receipt:
        return

    st.success(f"Cupom lido: {receipt.merchant} | {receipt.purchase_date.strftime('%d/%m/%Y')} | {money(receipt.total)}")
    st.caption(f"Chave/fingerprint: {receipt.access_key}")

    edited = st.data_editor(
        st.session_state["items_editor"],
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "product_name": st.column_config.TextColumn("Produto"),
            "normalized_name": st.column_config.TextColumn("Nome acompanhado"),
            "category": st.column_config.TextColumn("Categoria"),
            "quantity": st.column_config.NumberColumn("Qtd.", min_value=0.0, step=0.01),
            "unit": st.column_config.TextColumn("Un."),
            "unit_price": st.column_config.NumberColumn("Preço unit.", format="R$ %.2f", min_value=0.0),
            "total_price": st.column_config.NumberColumn("Total", format="R$ %.2f", min_value=0.0),
        },
        hide_index=True,
    )

    save_col, total_col = st.columns([0.35, 0.65])
    total_col.metric("Total revisado", money(float(edited["total_price"].sum())))
    if save_col.button("Salvar no histórico", type="primary", use_container_width=True):
        ok, message = save_receipt(receipt, edited)
        if ok:
            st.success(message)
            st.session_state.pop("receipt", None)
            st.session_state.pop("items_editor", None)
            st.rerun()
        else:
            st.warning(message)


def render_manual_expense() -> None:
    st.subheader("Adicionar despesa manual")
    st.write(
        "Use esta aba para despesas que não chegam por QR Code de mercado, como aluguel, condomínio, internet, transporte, educação, plano de saúde ou assinaturas."
    )

    ipca_group_names = [item["group"] for item in IPCA_GROUPS]
    with st.container(border=True):
        col1, col2, col3 = st.columns([1.1, 0.9, 1.0])
        ipca_group = col1.selectbox("Grupo IPCA", ipca_group_names)
        default_category = IPCA_GROUP_TO_DEFAULT_CATEGORY.get(ipca_group, "Despesas pessoais")
        category = col2.selectbox(
            "Categoria interna",
            CATEGORIES,
            index=CATEGORIES.index(default_category) if default_category in CATEGORIES else 0,
        )
        purchase_date = col3.date_input("Data da despesa", value=date.today())

        description = st.text_input("Descrição", placeholder="Ex.: Condomínio, internet, gasolina, escola, plano de saúde")

        col4, col5, col6 = st.columns([0.8, 0.7, 1.1])
        total_price = col4.number_input("Valor total", min_value=0.0, step=1.0, format="%.2f")
        quantity = col5.number_input("Quantidade", min_value=0.01, value=1.0, step=1.0, format="%.2f")
        source = col6.text_input("Origem/fornecedor", placeholder="Ex.: Enel, Vivo, Uber, escola, condomínio")
        attachment = st.file_uploader(
            "Comprovante opcional",
            type=["pdf", "png", "jpg", "jpeg", "txt"],
            help="Anexe uma fatura, recibo ou foto quando quiser guardar a origem da despesa.",
        )

        normalized_name = st.text_input(
            "Nome acompanhado",
            value=description.upper() if description else "",
            placeholder="Como esse gasto deve aparecer nos gráficos",
        )

        st.caption(
            "Dica: para despesas recorrentes, use sempre o mesmo nome acompanhado. Assim o app compara a evolução mês a mês."
        )

        if st.button("Salvar despesa manual", type="primary", use_container_width=True):
            ok, message = save_manual_expense(
                {
                    "description": description,
                    "normalized_name": normalized_name or description,
                    "ipca_group": ipca_group,
                    "category": category,
                    "purchase_date": purchase_date,
                    "total_price": total_price,
                    "quantity": quantity,
                    "unit": "UN",
                    "source": source or "Lançamento manual",
                    "attachment": attachment,
                }
            )
            if ok:
                st.success(message)
                st.rerun()
            else:
                st.warning(message)

    with st.expander("Quando usar manual em vez de QR Code?"):
        st.markdown(
            """
            Use QR Code para mercado, farmácia, combustível e lojas com NFC-e.

            Use manual para despesas dos outros grupos do IPCA:
            - Habitação: aluguel, condomínio, luz, água, gás.
            - Transportes: Uber, ônibus, estacionamento, manutenção.
            - Educação: escola, curso, material.
            - Comunicação: internet, celular, streaming.
            - Saúde: plano, consulta, exame.
            """
        )


def render_analysis_hub(receipts: pd.DataFrame, items: pd.DataFrame) -> None:
    st.subheader("Análises")
    st.write("Compare sua cesta com referências de mercado, veja economias por estoque em uso e entenda a leitura pelos grupos IPCA.")

    view = st.radio(
        "Escolha a análise",
        ["Média de mercado", "Economia", "Grupos IPCA"],
        horizontal=True,
        label_visibility="collapsed",
        key="analysis_view",
    )

    if view == "Média de mercado":
        render_market_reference(receipts, items)
    elif view == "Economia":
        render_stock_savings(receipts, items)
    else:
        render_ipca_groups_guide(receipts, items)


def render_history(receipts: pd.DataFrame, items: pd.DataFrame) -> None:
    if receipts.empty:
        st.info("Nenhum cupom salvo ainda.")
        return

    st.subheader("Cupons")
    display = receipts.copy()
    display["purchase_date"] = display["purchase_date"].dt.strftime("%d/%m/%Y")
    display["total"] = display["total"].map(money)
    st.dataframe(
        display[["purchase_date", "merchant", "total", "access_key"]],
        use_container_width=True,
        hide_index=True,
    )
    st.subheader("Itens")
    item_display = items.copy()
    item_display["purchase_date"] = item_display["purchase_date"].dt.strftime("%d/%m/%Y")
    item_display["unit_price"] = item_display["unit_price"].map(money)
    item_display["total_price"] = item_display["total_price"].map(money)
    st.dataframe(
        item_display[
            [
                "purchase_date",
                "merchant",
                "product_name",
                "normalized_name",
                "category",
                "quantity",
                "unit",
                "unit_price",
                "total_price",
            ]
        ],
        use_container_width=True,
        hide_index=True,
        column_config={
            "purchase_date": "Data",
            "merchant": "Mercado",
            "product_name": "Produto no cupom",
            "normalized_name": "Produto acompanhado",
            "category": "Categoria",
            "quantity": "Qtd.",
            "unit": "Un.",
            "unit_price": "Preço unit.",
            "total_price": "Total",
        },
    )


def render_data_hub(receipts: pd.DataFrame, items: pd.DataFrame) -> None:
    st.subheader("Dados")
    st.write("Cadastre despesas fora do QR Code, revise categorias e consulte o histórico que alimenta seus cálculos.")

    view = st.radio(
        "Escolha a área de dados",
        ["Despesa manual", "Ajustar dados", "Histórico"],
        horizontal=True,
        label_visibility="collapsed",
        key="data_view",
    )

    if view == "Despesa manual":
        render_manual_expense()
    elif view == "Ajustar dados":
        render_data_editor(receipts, items)
    else:
        render_history(receipts, items)


def main() -> None:
    st.set_page_config(page_title="Minha Inflação", page_icon="MI", layout="wide")
    render_light_theme_css()
    init_db()

    tab_home, tab_import, tab_dashboard, tab_plan, tab_analysis, tab_data = st.tabs(
        ["Início", "Importar", "Dashboard", "Plano anual", "Análises", "Dados"]
    )
    receipts, items = load_history()

    with tab_home:
        render_home(receipts, items)

    with tab_import:
        render_importer()

    with tab_dashboard:
        render_dashboard(receipts, items)

    with tab_plan:
        render_annual_plan(receipts, items)

    with tab_analysis:
        render_analysis_hub(receipts, items)

    with tab_data:
        render_data_hub(receipts, items)


if __name__ == "__main__":
    main()
