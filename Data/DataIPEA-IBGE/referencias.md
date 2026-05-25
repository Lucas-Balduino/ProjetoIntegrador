# Referências — Fontes de Validação da Problemática (PI 1)

Documento complementar à [metodologia.md](metodologia.md). Reúne as fontes utilizadas para validar a problemática de **diaristas / trabalho doméstico / informalidade** no contexto do PI 1 (Design Thinking, ODS 8), com um fichamento curto explicando **o que cada fonte prova** e **qual seção do dashboard ela sustenta**.

## Estrutura do fichamento

Para cada fonte:
- **O que prova**: a hipótese ou indicador que a fonte sustenta.
- **Onde aplicar**: a seção do dashboard / pesquisa onde a fonte entra como evidência.
- **Trecho/indicador-chave**: o dado ou citação que ancora o argumento.

---

## A. Fontes secundárias — Mercado (quantitativo)

### A1. IBGE — PNAD Contínua (página oficial)
- **URL**: <https://www.ibge.gov.br/estatisticas/sociais/saude/17270-pnad-continua.html>
- **O que prova**: metodologia, abrangência e periodicidade da pesquisa que alimenta as tabelas SIDRA usadas neste pipeline. É a "constituição metodológica" do nosso dado quantitativo.
- **Onde aplicar**: nota de rodapé do dashboard explicando que todos os dados macro vêm de uma pesquisa domiciliar amostral contínua, com painel rotacional.
- **Indicador-chave**: amostra de ~211 mil domicílios por trimestre; investiga ocupação, posição na ocupação, carteira assinada e rendimento.

### A2. IBGE — SIDRA (tabelas) e API
- **URLs**: <https://sidra.ibge.gov.br/pesquisa/pnadct/tabelas>, <https://apisidra.ibge.gov.br/>
- **O que prova**: existência de séries históricas consultáveis programaticamente desde 1T 2012.
- **Onde aplicar**: fonte primária dos dados que alimentam o ETL deste repositório (ver [metodologia.md §6](metodologia.md)).
- **Indicador-chave**: 21 tabelas curadas no [`pipeline/catalogo.yaml`](../pipeline/catalogo.yaml), todas com cobertura nacional (BR, UF e em vários casos municípios).

### A3. IPEA — *Cuidado remunerado e trabalho doméstico*
- **URL**: <https://www.ipea.gov.br/portal/publicacao-item?id=58b6a5cf-0a0a-4171-8a4e-d8e9e54f2808>
- **O que prova**: perfil predominantemente de **mulheres negras** nas ocupações de cuidado e trabalho doméstico; disparidades raciais em condições de trabalho, renda, escolaridade e tempo de deslocamento; **uso ainda limitado, porém com interesse potencial, em plataformas digitais**.
- **Onde aplicar**: validação do recorte de gênero/raça do dashboard (cruzando com nossas tabelas 4093, 6402); e principalmente — **valida a hipótese central do PI**: existe demanda latente das trabalhadoras por uma plataforma digital adequada.
- **Indicador-chave**: maioria absoluta de mulheres negras com baixa escolaridade no setor; interesse declarado por apps mesmo em meio à baixa adoção atual.

### A4. IPEA — busca Gig Economy
- **URL**: <https://www.ipea.gov.br/portal/busca-geral?q=economia+gig>
- **O que prova**: existência de corpus de estudos brasileiros sobre Gig Economy / plataformização do trabalho. Permite contextualizar o caso das diaristas dentro do fenômeno macro.
- **Onde aplicar**: introdução/contexto do dashboard.
- **Indicador-chave**: múltiplos textos para discussão TD (Texto para Discussão) tratando trabalho de plataforma, vínculo, proteção social.

### A5. SEBRAE — Empreendedorismo Feminino
- **URL**: <https://sebrae.com.br/sites/PortalSebrae/empreendedorismofeminino>
- **O que prova**: existência de caminhos formais (MEI, cursos, microcrédito) para autonomização de trabalhadoras autônomas.
- **Onde aplicar**: seção do dashboard sobre **alternativas de formalização** (ODS 8). Contrabalança o quadro de informalidade observado nas tabelas 8517/8529.
- **Indicador-chave**: políticas públicas de incentivo + dados próprios SEBRAE sobre mulheres como dona-de-negócio (MEI feminino crescente).

---

## B. Fontes secundárias — Legal e institucional (qualitativo)

### B1. FENATRAD — Federação Nacional das Trabalhadoras Domésticas
- **URL**: <https://fenatrad.org.br/institucional/>
- **O que prova**: organização e representação coletiva da categoria; posicionamento institucional sobre direitos, riscos e demandas.
- **Onde aplicar**: seção "Perspectiva da trabalhadora" do dashboard — voz organizada da categoria, complementa o que vem nas entrevistas primárias.
- **Indicador-chave**: pautas defendidas (PEC das Domésticas / LC 150/2015, combate ao assédio, formalização).

### B2. OIT / ILO — *Trabalhadoras domésticas remuneradas* (2025)
- **URL**: <https://www.ilo.org/sites/default/files/2025-05/trabalhadoras_domesticas_remuneradas.pdf>
- **O que prova**: panorama internacional do trabalho doméstico remunerado; recomendações para alcance de **trabalho decente** (ODS 8) na categoria.
- **Onde aplicar**: âncora teórica para a leitura ODS 8 do dashboard. Conecta o problema local ao framework global.
- **Indicador-chave**: padrões de informalidade global, ausência de proteção social, recomendações da OIT sobre regulação de plataformas.

### B3. eSocial Doméstico — Manual do Empregador Doméstico
- **URL**: <https://www.gov.br/esocial/pt-br/empregador-domestico/manual-do-empregador-domestico>
- **O que prova**: existe um caminho concreto de **formalização para a categoria mensalista** (eSocial doméstico). Em contrapartida, a diarista (que trabalha em múltiplos domicílios) não se enquadra nesse fluxo.
- **Onde aplicar**: seção "Gap regulatório" do dashboard — argumento central para justificar a plataforma proposta no PI 2 (formalização da diarista, possivelmente via MEI + recibo padronizado).
- **Indicador-chave**: o eSocial doméstico assume vínculo mensal; ausência de processo análogo para o regime de diária reforça a oportunidade da plataforma.

---

## C. Como cada fonte conversa com o pipeline deste repositório

| Fonte | Tipo | Papel no dashboard | Tabelas SIDRA conectadas |
| --- | --- | --- | --- |
| IBGE / SIDRA | quantitativo | **valor numérico** nos marts (taxa de informalidade, rendimento, horas, nº de diaristas) | 4097, 6383, 5440, 6374, 8517, 8529 |
| IPEA Cuidado Remunerado | quanti+quali | **narrativa de equidade** (gênero/raça) | 6402, 6405, 6406 (cruzamento) |
| IPEA Gig Economy | qualitativo | contexto macro do PI | (citação) |
| SEBRAE Empreendedorismo Feminino | qualitativo | narrativa de **formalização (MEI)** | (citação) |
| FENATRAD | qualitativo | voz da categoria | (citação) |
| OIT 2025 | qualitativo | âncora **ODS 8** | (citação) |
| eSocial doméstico | regulatório | argumento de **gap regulatório** que motiva a solução do PI 2 | (citação) |

