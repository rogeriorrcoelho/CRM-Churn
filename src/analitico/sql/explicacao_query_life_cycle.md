# Contagem de usuários ativos por ciclo de vida


## 1. Definições de negócio

Classificações definidas/mapeadas:

* **Curioso** — `idade < 7` dias desde a primeira interação.
* **Fiel** — `recência < 7` e `recência anterior < 15` (versão original ambígua; na prática quer-se: último contato recente e penúltimo contato dentro de janela curta).
* **Turista** — `7 <= recência <= 14` (usuário com recência média).
* **Desencantado** — `15 <= recência <= 28`.
* **Zumbi** — `recência > 28`.
* **Reconquistado** — `recência < 7` e `14 <= recência anterior <= 28`.
* **Reborn** — `recência < 7` e `recência anterior > 28`.

---

## 2. Visão geral da consulta

CTEs (Common Table Expressions) para:

1. Normalizar transações por dia (`tb_daily`);
2. Calcular idade e recência do cliente (`tb_idade`);
3. Gerar `row_number` por dia para extrair a penúltima ativação (`tb_rn` / `tb_penultima_ativacao`);
4. Aplicar as regras de negócio em uma `CASE` final e agrupar o total por classificação.

---

## 3. CTEs

### `tb_daily`

```sql
WITH tb_daily as (
    SELECT DISTINCT
        IdCliente,
        substr(DtCriacao ,0,11) as dtDia
    FROM transacoes
),
```

* **O que faz:** pega todas as transações e reduz cada registro ao par `(IdCliente, dtDia)`, onde `dtDia` é a data (sem hora) da criação. `DISTINCT` evita contar várias transações no mesmo dia mais de uma vez.

---

### `tb_idade`

```sql
tb_idade AS (
    SELECT
        IdCliente,
        cast (max(julianday('2025-09-01') - julianday(dtDia)) as int) as qtdeDiasPrimTransacao,
        cast (min(julianday('2025-09-01') - julianday(dtDia)) as int) as qtdeDiasUltTransacao
    FROM tb_daily
    GROUP BY IdCliente
    ORDER BY 1 asc, 2 asc
),
```

* **O que faz:** para cada cliente calcula duas medidas, ambas em dias:

  * `qtdeDiasPrimTransacao` = `max(julianday(ref_date) - julianday(dtDia))` → diferença máxima entre a data de referência (`'2025-09-01'`) e as datas do cliente. Isso corresponde ao número de dias desde a **primeira** transação (idade do cliente em dias).
  * `qtdeDiasUltTransacao` = `min(julianday(ref_date) - julianday(dtDia))` → diferença mínima, ou seja, dias desde a **última** transação (recência).

---

### `tb_rn` e `tb_penultima_ativacao`

```sql
tb_rn as (
    SELECT
        *,
        row_number() OVER (PARTITION BY IdCliente ORDER BY dtDia DESC) AS rnDia
    FROM tb_daily
),

tb_penultima_ativacao as (
    SELECT *,
        cast(julianday('2025-09-01') - julianday(dtDia) AS int) as qtdePenultimaTransacao
    FROM tb_rn
    WHERE rnDia = 2
),
```

* **`tb_rn`:** cria, por cliente, uma numeração das datas (`dtDia`) em ordem decrescente. Assim `rnDia = 1` é a data do último dia com atividade e `rnDia = 2` é a penúltima.
* **`tb_penultima_ativacao`:** filtra apenas a linha `rnDia = 2` (quando existe) e calcula `qtdePenultimaTransacao`, que representa a quantidade de dias desde a penúltima transação até a data de referência (`'2025-09-01'`).
* **Observações:**

  * Clientes com apenas 1 dia de atividade não terão linha em `tb_penultima_ativacao` (ou seja, `qtdePenultimaTransacao` ficará `NULL` após o `LEFT JOIN` usado adiante). 

---

### `tb_life_cycle` e aplicação da `CASE`

```sql
tb_life_cycle AS (

    SELECT
        t1.*,
        t2.qtdePenultimaTransacao,
        CASE
            WHEN qtdeDiasPrimTransacao <= 7 THEN '01 - CURIOSO'
            WHEN qtdeDiasUltTransacao <= 7 AND qtdePenultimaTransacao - qtdeDiasUltTransacao <= 14 THEN '02 - FIEL'
            WHEN qtdeDiasUltTransacao BETWEEN 8 and 14 THEN '03 - TURISTA'
            WHEN qtdeDiasUltTransacao BETWEEN 15 and 28 THEN '04 - DESENCANTADA'
            WHEN qtdeDiasUltTransacao > 28 THEN '05 - ZUMBI'
            WHEN qtdeDiasUltTransacao <= 7 AND qtdePenultimaTransacao - qtdeDiasUltTransacao  BETWEEN 15 AND 28 THEN '02 - RECONQUISTADO'
            WHEN qtdeDiasUltTransacao <= 7 AND qtdePenultimaTransacao - qtdeDiasUltTransacao  > 28 THEN '02 - REBORN'
        END AS descLifeCycle
    FROM tb_idade AS t1
    LEFT JOIN tb_penultima_ativacao AS t2
    ON t1.IdCliente = t2.IdCliente
)
```

* **Parâmetros usados:** `qtdeDiasPrimTransacao` (idade), `qtdeDiasUltTransacao` (recência), `qtdePenultimaTransacao` (recência da penúltima).
* **Interpretação das expressões:**

  * `qtdePenultimaTransacao - qtdeDiasUltTransacao` calcula o **intervalo em dias** entre a penúltima e a última transação (ou seja, quantos dias separaram as duas últimas ativações). 

---

## 4. Pontos de atenção

1. **Clientes sem penúltima transação:**

   * `qtdePenultimaTransacao` será `NULL` quando o cliente tiver apenas uma data em `tb_daily`. As expressões do `CASE` que usam `qtdePenultimaTransacao` produzirão `NULL` na comparação e falharão a condição.

2. **`CURIOSO` vs `FIEL`:**

   * A condição `qtdeDiasPrimTransacao <= 7` marca clientes como `CURIOSO` mesmo que também atendam `FIEL` (por exemplo, um cliente que começou há 3 dias e teve duas visitas dentro de 2 dias). Defina a prioridade: se `curioso` deve significar "novo e ainda sem recorrência", então coloque a verificação de `FIEL` e `RECONQUISTADO/REBORN` antes de `CURIOSO` ou refine a lógica (ex.: `qtdeDiasPrimTransacao <= 7 AND qtdeDiasUltTransacao > 7` para só marcar curioso quem não teve recência imediata).

