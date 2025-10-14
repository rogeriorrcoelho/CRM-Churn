-- Para cada data de referência (dtRef), 
-- contagem de clientes (únicos) que estiveram ativos (possuiram transações) 
-- nos últimos 28 dias (inclusive)

with tb_daily as (
    select distinct
        date(substr(DtCriacao,0,11)) as DtDia, 
        idCliente
    
    from transacoes
    order by DtDia
),


tb_distinct_day as (
    SELECT
        DISTINCT DtDia as dtRef
    from tb_daily
)

select 
    t1.dtRef,
    count( DISTINCT IdCliente) AS MAU,
    count( DISTINCT t2.dtDia) as qtdDias

from 
    tb_distinct_day as t1

left join tb_daily as t2
on t2.DtDia <= t1.dtRef
and julianday(t1.dtRef) - julianday(t2.DtDia) < 28

GROUP BY t1.dtRef

order by t1.dtRef DESC
