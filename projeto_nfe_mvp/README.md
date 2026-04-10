# Projeto NFe MVP

MVP em Streamlit para analise antifraude de XMLs de NF-e com foco em:

- duplicidade tecnica
- reapresentacao do mesmo XML
- sinais comportamentais suspeitos
- exportacao do resultado em CSV

## Rodar localmente

1. Crie um ambiente virtual Python 3.10+
2. Instale as dependencias:

```bash
pip install -r requirements.txt
```

3. Rode o app:

```bash
streamlit run app.py
```

## Deploy recomendado

O caminho mais simples para MVP publico e o Streamlit Community Cloud:

1. subir esta pasta para um repositorio no GitHub
2. criar um app novo no Streamlit Cloud
3. apontar para o arquivo `app.py`
4. publicar e compartilhar a URL

## Estrutura

- `app.py`: interface web principal
- `detectar_duplicidade.py`: script batch para gerar CSV local
- `gerar_220_xmls_ricos.py`: gerador de XMLs de exemplo
- `xmls_ricos/`: base de XMLs de teste
