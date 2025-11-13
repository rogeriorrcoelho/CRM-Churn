# %%

import pandas as pd
import sqlalchemy


def import_query(path):
    with open(path) as open_file:
        query = open_file.read()
    return(query)

query = import_query("../sql/life_cycle.sql")

# %%
# engine tansacional - (aplicação)
engine_app = sqlalchemy.create_engine("sqlite:///../../../data/crm-transacional/database.db")

# %%
# criar um banco analítico para guardar os dados
# engine analítico
engine_analytical = sqlalchemy.create_engine("sqlite:///../../../data/analitico/database.db")


# %%

# definindo as datas para as safras
dates = [
    '2024-05-01',
    '2024-06-01',
    '2024-07-01',
    '2024-08-01',
    '2024-09-01',
    '2024-10-01',
    '2024-11-01',
    '2024-12-01',
    '2025-01-01',
    '2025-02-01',
    '2025-03-01',
    '2025-04-01',
    '2025-05-01',
    '2025-06-01',
    '2025-07-01',
    '2025-08-01',
    '2025-09-01',
]


# %%

for i in dates:
    # monta a query com o valor da data
    delete_sql = f"delete from life_cycle where dtRef = date('{i}', '-1 day')"
    
    with engine_analytical.connect() as con:
        try:
            con.execute(sqlalchemy.text(delete_sql))
            con.commit()
        except Exception as err:
            print(err)
    
    # mostra a query no console
    print(delete_sql)

    query_format = query.format(date=i)
    df = pd.read_sql(query_format, engine_app)

    # guarda os dados no banco analítico
    df.to_sql("life_cycle", engine_analytical, index=False, if_exists="append")

# %%

with engine_analytical.connect() as con:
    result = con.execute(sqlalchemy.text("select " \
                                            "dtRef, " \
                                            "descLifeCycle, " \
                                            "count(*) " \
                                         "from life_cycle " \
                                         "group by 1, 2 " \
                                         "order by 1,2"
                                         )
                        )

for row in result:
    print(row)


# %%
