"""Página Fontes de Dados."""

import streamlit as st

from dashboard import theme, ui

st.set_page_config(page_title="Fontes | Trabalho Doméstico Informal", layout="wide")
theme.inject_theme()
ui.render_sidebar()

theme.page_header(
    "Fontes de Dados",
    "Referências secundárias e primárias utilizadas no dashboard",
)

st.markdown("### Dados secundários (macro)")

fontes_macro = [
    ("PNAD Contínua — IBGE SIDRA", "https://sidra.ibge.gov.br/pesquisa/pnadct/tabelas", "Tabelas 4097, 6383, 8529, 5440, 6374"),
    ("API SIDRA REST", "https://apisidra.ibge.gov.br/", "Pipeline ETL automatizado"),
    ("IPEA — Cuidado remunerado", "https://www.ipea.gov.br/portal/publicacao-item?id=58b6a5cf-0a0a-4171-8a4e-d8e9e54f2808", "Validação da problemática"),
    ("IBGE — PNAD Contínua", "https://www.ibge.gov.br/estatisticas/sociais/saude/17270-pnad-continua.html", "Metodologia estatística"),
    ("SEBRAE", "https://sebrae.com.br/sites/PortalSebrae/empreendedorismofeminino", "Empreendedorismo feminino / MEI"),
]

for nome, url, desc in fontes_macro:
    st.markdown(f"- **[{nome}]({url})** — {desc}")

st.markdown("### Dados primários (micro)")

st.markdown(
    """
    - **Pesquisa com contratantes** — Google Forms → Excel (`pesquisa-contratante.xlsx`, 106 respostas)
    - **Pesquisa com diaristas** — Google Forms / WhatsApp → Excel (`pesquisa-diaristas.xlsx`, 21 respostas)
    - Campo local em **Brasília, 2026**
    """
)

st.markdown("### Referências legais e setoriais")

fontes_legal = [
    ("FENATRAD", "https://fenatrad.org.br/institucional/", "Federação Nacional dos Trabalhadores Domésticos"),
    ("OIT / ILO", "https://www.ilo.org/", "Trabalhadoras domésticas remuneradas"),
    ("eSocial — Empregador Doméstico", "https://www.gov.br/esocial/pt-br/empregador-domestico", "Manual de formalização"),
    ("MPT", "https://www.mpt.mp.br/", "Direitos trabalhistas da categoria"),
]

for nome, url, desc in fontes_legal:
    st.markdown(f"- **[{nome}]({url})** — {desc}")

st.markdown("### Protótipo IHC (referência de design)")
st.markdown(
    "[AvaliacaoIHC — protótipo HTML/CSS/JS](https://github.com/Lucas-Balduino/AvaliacaoIHC) "
    "utilizado como referência visual para este dashboard Streamlit."
)

st.markdown("### Pipeline de dados")
st.code(
    """
python -m pipeline.etl --target 4097 --target 6383 --target 8529 --target 5440 --target 6374 --nivel BR --periodos last
python -m pipeline.etl --formularios
python -m pipeline.modelo
python scripts/export_snapshot.py
    """.strip(),
    language="powershell",
)

ui.footer("snapshot")
