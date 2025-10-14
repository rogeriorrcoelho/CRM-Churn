-- Daily Access Users
select substr(DtCriacao,0,11) as DtDia, 
       count(distinct idCliente) as DAU
from transacoes
group by 1
order by DtDia
