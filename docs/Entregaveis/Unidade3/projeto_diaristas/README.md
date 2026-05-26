# projeto_diaristas — Pipeline SIDRA → PED-like

Pipeline de descoberta + ETL em Python que extrai dados da **PNAD Contínua** (SIDRA / IBGE) e normaliza em um modelo dimensional inspirado na **PED do IPEDF/DIEESE**, com foco em **diaristas, trabalho doméstico e informalidade**.

Faz parte do **Projeto Integrador I (PI 1)** — tema "Trabalho Autônomo ou Informal" / Gig Economy — vinculado ao repositório [Lucas-Balduino/ProjetoIntegrador](https://github.com/Lucas-Balduino/ProjetoIntegrador) e ancorado no **ODS 8** (Trabalho Decente e Crescimento Econômico).

Entregue como parte de `docs/Entregaveis/Unidade3/`.

## Correção de escopo

O link originalmente compartilhado para o trabalho era `https://sidra.ibge.gov.br/home/primpec/brasil`, que aponta para **Primeiras Estimativas da Pecuária** (bovinos, leite, ovos) — não tem relação com diaristas. As fontes corretas no SIDRA são:

- Trimestral: <https://sidra.ibge.gov.br/pesquisa/pnadct/tabelas>
- Mensal: <https://sidra.ibge.gov.br/pesquisa/pnadcm>
- API REST: <https://apisidra.ibge.gov.br/>

## Estrutura

```text
projeto_diaristas/
  pipeline/
    descoberta.py     # scraping HTML das listagens PNADC/T e PNADC/M
    catalogo.yaml     # tabelas-alvo com palavras-chave e bloco temático
    ai_mapper.py      # consome /DescritoresTabela/t/{T} e gera spec ETL
    etl.py            # orquestrador: descoberta + mapping + extração
    modelo.py         # constrói star schema (dim_*, fato_*)
    utils_sidra.py    # cliente HTTP com cache + retry
  specs/              # specs YAML por tabela (gerados pelo ai_mapper)
  data/
    raw/              # JSON SIDRA bruto cacheado
    staging/          # parquet long-format por tabela
    marts/            # star schema final (parquet + csv)
  docs/
    metodologia.md    # ENTREGÁVEL principal
    referencias.md    # fichamento das fontes de validação
```

## Como rodar

```powershell
python -m pip install -r requirements.txt

# 1) descobrir tabelas (gera/atualiza catalogo.yaml com infos do SIDRA)
python -m pipeline.descoberta

# 2) gerar specs com auxílio do mapeador heurístico (modo offline)
python -m pipeline.ai_mapper --all

# 3) rodar o ETL (extrai + normaliza + modela)
python -m pipeline.etl --target 4097 --nivel BR
python -m pipeline.etl --target 6383 --nivel BR

# 3b) rodar todas as tabelas marcadas como "prioridade: alta"
python -m pipeline.etl --all

# 4) construir o modelo dimensional (star schema PED-like)
python -m pipeline.modelo
```

## Entregáveis

1. Script: `pipeline/etl.py` (orquestra o pipeline completo).
2. `.md` principal: `docs/metodologia.md` — contexto PI 1, mapeamento PED↔PNAD-C, catálogo SIDRA, dicionário do modelo, how-to-run.
3. `.md` complementar: `docs/referencias.md` — fontes de validação (IPEA, IBGE, SEBRAE, FENATRAD, OIT, eSocial).
