# Roadmap do Projeto: Monitorização de Polinizadores (Data2Eco)

Este documento rastreia o progresso do pipeline de dados para a análise de biodiversidade na cafeicultura.

**Objetivo Final:** Entregar um dashboard/relatório que mostre a variação da riqueza de espécies de abelhas (*Apidae*) no Brasil entre as décadas de 2000-2010 e 2011-2023.

---

## 📅 Fase 1: Configuração e Planeamento (Dias 1-2)
*Foco: Infraestrutura e Definições*

- [ ] **Configuração do Repositório**
    - [x] Criar repositório no GitHub e definir proteção da branch `main`.
    - [ ] Criar ficheiro `.gitignore` (Python, dbt, OS).
    - [ ] Criar estrutura de pastas (`scripts/`, `dbt_project/`).
- [ ] **Definição de Escopo de Dados**
    - [ ] Validar filtros da API GBIF: `familyKey` (Apidae), `country` (BR), `year` (2000-2023).
- [ ] **Configuração dbt**
    - [ ] `dbt init` do projeto.
    - [ ] Configurar `profiles.yml` para conexão ao Data Warehouse (Postgres/BigQuery).

---

## 🚜 Fase 2: Ingestão de Dados (Responsável: Pessoa A)
*Foco: Extração (Extract) e Carregamento (Load)*

- [ ] **Script de Extração (Python)**
    - [ ] Implementar paginação na API de Busca do GBIF (`offset`/`limit`).
    - [ ] Adicionar tratamento de erros e *retries* para falhas de conexão.
    - [ ] Salvar dados brutos em formato intermédio (Parquet/CSV) localmente.
- [ ] **Carregamento no Warehouse**
    - [ ] Criar tabela `raw_gbif_occurrences` no banco de dados.
    - [ ] Carregar dados do ficheiro local para a tabela `raw`.

---

## 🏗️ Fase 3: Camadas Bronze e Silver (Colaborativo)
*Foco: Transformação e Limpeza*

- [ ] **Camada Bronze (dbt)**
    - [ ] Criar `models/staging/sources.yml` (Definição da source).
    - [ ] Criar `stg_gbif_occurrences.sql` (Tipagem de dados, renomeação de colunas).
- [ ] **Camada Silver (dbt)** - *Responsável: Pessoa B*
    - [ ] Filtrar registos sem coordenadas (`lat`/`long` nulos).
    - [ ] Filtrar registos de baixa precisão ou categorias indesejadas (ex: Fósseis).
    - [ ] Deduplicar ocorrências.
    - [ ] Adicionar testes de qualidade (`not_null`, `unique`) no `schema.yml`.

---

## 📊 Fase 4: Camada Gold e Métricas (Responsável: Pessoa B)
*Foco: Lógica de Negócio e Agregação*

- [ ] **Lógica de Períodos**
    - [ ] Criar coluna calculada para blocos de tempo ("2000-2010", "2011-2023").
- [ ] **Agregação**
    - [ ] Criar `gold_biodiversity_trends.sql`.
    - [ ] Calcular contagem distinta de `scientific_name` por Estado e Período.
    - [ ] Calcular % de variação entre os períodos (Window Functions).
- [ ] **Documentação**
    - [ ] Preencher descrições das colunas no `schema.yml` para a camada Gold.

---

## 🚀 Fase 5: Entrega e Visualização
*Foco: Valor para o Cliente*

- [ ] **Validação Final**
    - [ ] Executar `dbt test` em todo o pipeline.
    - [ ] Revisão cruzada do código (Pull Request final).
- [ ] **Visualização (Opcional/Bónus)**
    - [ ] Conectar ferramenta de BI (Metabase/Preset) à tabela Gold.
    - [ ] Gerar gráfico de linhas: *Riqueza de Espécies x Década* por Estado.