-- Monthly Access Users
SELECT DISTINCT
       substr(DtCriacao,0,8) as DtDia, 
       count(DISTINCT idCliente) as num_clientes
FROM transacoes
group by DtDia
ORDER BY DtDia