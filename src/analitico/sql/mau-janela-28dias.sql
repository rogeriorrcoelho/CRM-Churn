-- clientes ativos janela dos últimos 28 dias
-- clientes que estiveram ativo nos últimos 28 dias por data de referência
-- Para cada data de referência (dtRef), quais usuários 
-- estiveram ativos (tiveram transações) nos últimos 28 dias (inclusive)

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
    t1.*,
    t2.*

from 
    tb_distinct_day as t1

left join tb_daily as t2
on t2.DtDia <= t1.dtRef
and julianday(t1.dtRef) - julianday(t2.DtDia) < 28
order by t1.dtRef DESC
