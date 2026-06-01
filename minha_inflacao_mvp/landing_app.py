import base64
import re
from pathlib import Path

import streamlit as st


APP_DIR = Path(__file__).resolve().parent
LANDING_PATH = APP_DIR / "minha_inflacao_landing.html"
IMAGE_PATH = APP_DIR / "assets" / "minha-inflacao-app.png"


def load_landing_html() -> str:
    html = LANDING_PATH.read_text(encoding="utf-8")
    if IMAGE_PATH.exists():
        encoded = base64.b64encode(IMAGE_PATH.read_bytes()).decode("ascii")
        html = html.replace(
            'src="assets/minha-inflacao-app.png"',
            f'src="data:image/png;base64,{encoded}"',
        )
    html = html.replace(
        'href="mailto:contato@minhainflacao.app?subject=Quero%20testar%20o%20Minha%20Infla%C3%A7%C3%A3o"',
        'href="mailto:piloto@minhainflacao.app?subject=Quero%20testar%20o%20Minha%20Infla%C3%A7%C3%A3o"',
    )
    return html


def load_landing_fragment() -> str:
    html = load_landing_html()
    style_match = re.search(r"<style>(.*?)</style>", html, flags=re.S)
    body_match = re.search(r"<body>(.*?)</body>", html, flags=re.S)
    style = style_match.group(1) if style_match else ""
    body = body_match.group(1) if body_match else html
    return f"<style>{style}</style>{body}"


def main() -> None:
    st.set_page_config(
        page_title="Minha Inflação",
        page_icon="MI",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    st.markdown(
        """
        <style>
        #MainMenu, header, footer { visibility: hidden; }
        .block-container {
            padding: 0;
            max-width: 100%;
        }
        iframe {
            display: block;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.html(load_landing_fragment())


if __name__ == "__main__":
    main()
