# Minha Inflação

MVP em Streamlit para importar cupons NFC-e pelo link do QR Code, revisar os itens e acompanhar a inflação pessoal por produto, categoria e cesta mensal.

## Rodar localmente

```bash
streamlit run app.py
```

## Como usar

1. Abra o QR Code do cupom fiscal no celular.
2. Copie o link da NFC-e.
3. Cole o link na aba `Importar cupom`.
4. Revise os itens extraidos.
5. Salve no historico.

Os dados ficam no SQLite local `minha_inflacao.db`.
