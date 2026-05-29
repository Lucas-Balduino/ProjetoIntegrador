# projeto_diaristas — Pipeline SIDRA → Dashboard Streamlit

Pipeline de descoberta + ETL em Python que extrai dados da **PNAD Contínua** (SIDRA / IBGE) e normaliza em um modelo dimensional inspirado na **PED do IPEDF/DIEESE**, com foco em **diaristas, trabalho doméstico e informalidade**.

Inclui **dashboard Streamlit interativo** alimentado pelos marts gerados, com design baseado no protótipo [AvaliacaoIHC](https://github.com/Lucas-Balduino/AvaliacaoIHC).

Faz parte do **Projeto Integrador I (PI 1)** — tema "Trabalho Autônomo ou Informal" / Gig Economy — vinculado ao repositório [Lucas-Balduino/ProjetoIntegrador](https://github.com/Lucas-Balduino/ProjetoIntegrador) e ancorado no **ODS 8**.

## Estrutura

```text
projeto_diaristas/
  app.py                    # Dashboard Streamlit (entrada principal)
  pages/                    # Sobre, Fontes de Dados
  dashboard/                # Camada de apresentação (theme, queries, charts)
  dashboard/assets/marts/   # Snapshot versionado para Streamlit Cloud
  pipeline/                 # ETL SIDRA + formulários
  specs/                    # Specs YAML por tabela SIDRA
  scripts/
    export_snapshot.py      # Copia data/marts → dashboard/assets/marts
    run_etl_and_export.py   # Pipeline completo + export
  data/                     # raw / staging / marts (gitignored, dev local)
  docs/metodologia.md       # Entregável principal
  .streamlit/config.toml    # Tema do dashboard
```

## Como rodar o dashboard

```powershell
cd docs/Entregaveis/Unidade3/projeto_diaristas
python -m pip install -r requirements.txt
streamlit run app.py
```

O dashboard carrega dados de `data/marts/` (local) ou, se ausente, de `dashboard/assets/marts/` (snapshot commitado).

## Pipeline ETL (atualizar dados)

```powershell
python -m pip install -r requirements.txt

# Opção A — script automatizado (recomendado)
python scripts/run_etl_and_export.py

# Opção B — passo a passo
python -m pipeline.ai_mapper --tabela 8529 --tabela 5440 --tabela 6374
python -m pipeline.etl --target 4097 --target 6383 --target 8529 --target 5440 --target 6374 --nivel BR --periodos last
python -m pipeline.etl --formularios
python -m pipeline.modelo
python scripts/export_snapshot.py --force
```

Coloque os Excel da pesquisa primária em `PesquisaFormularios/` na raiz do repositório:

- `pesquisa-contratante.xlsx`
- `pesquisa-diaristas.xlsx`

Após exportar o snapshot, faça commit de `dashboard/assets/marts/` para o deploy no Streamlit Cloud refletir dados atualizados.

## Deploy Streamlit Cloud

1. Conecte o repositório [Lucas-Balduino/ProjetoIntegrador](https://github.com/Lucas-Balduino/ProjetoIntegrador)
2. **Main file path:** `docs/Entregaveis/Unidade3/projeto_diaristas/app.py`
3. Python 3.10+
4. Secrets: nenhum (dados em snapshot local; SIDRA não é chamada em runtime)

## Entregáveis

1. Pipeline ETL: `pipeline/etl.py`
2. Dashboard interativo: `app.py` + `pages/`
3. Metodologia: `docs/metodologia.md`
4. Snapshot de dados: `dashboard/assets/marts/`

## Fontes SIDRA

- Trimestral: <https://sidra.ibge.gov.br/pesquisa/pnadct/tabelas>
- API REST: <https://apisidra.ibge.gov.br/>
