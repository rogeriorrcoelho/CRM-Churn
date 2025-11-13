# %%

import pandas as pd
import sqlalchemy
import matplotlib.pyplot as plt
import seaborn as sb
from sklearn import cluster
from sklearn import preprocessing
from pathlib import Path

def import_query(path):
    with open(path) as open_file:
        query = open_file.read()
    return(query)

# Caminho da pasta 
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

print (BASE_DIR)

# %%
# Caminho e engine
print(f"sqlite:{BASE_DIR}/data/analitico/database.db")
engine = sqlalchemy.create_engine(f"sqlite:////{BASE_DIR}/data/crm-transacional/database.db")

query = import_query(f"{BASE_DIR}/src/analitico/sql/frequencia_valor.sql")
print(query)

# %%

df = pd.read_sql(query,engine)

print(df)

# removendo ponto em 7000 = erro/bug no bot do site
df = df[df['qtdePontosPos']<4000]



# %%
plt.plot(df['qtdeFrequencia'],df['qtdePontosPos'],'o')
plt.grid(True)
plt.show()



# %%
kmean = cluster.KMeans(n_clusters=5,random_state=42,max_iter=1000)

kmean.fit(df[['qtdeFrequencia','qtdePontosPos']])

df['cluster_kmean'] = kmean.labels_

df.groupby(by='cluster_kmean')['IdCliente'].count()



# %%
sb.scatterplot(data=df,
               x="qtdeFrequencia",
               y="qtdePontosPos",
               hue="cluster_kmean",
               palette="deep")
plt.grid()



# %%
# padronizando as escalas dos dois eixos

minmax = preprocessing.MinMaxScaler()

X = minmax.fit_transform(df[['qtdeFrequencia','qtdePontosPos']])

kmean = cluster.KMeans(n_clusters=5,random_state=42,max_iter=1000)
kmean.fit(X)

df['cluster_kmean_padronizado'] = kmean.labels_




#%%
# Visualizando os clusters formados
sb.scatterplot(data=df,
               x="qtdeFrequencia",
               y="qtdePontosPos",
               hue="cluster_kmean_padronizado",
               palette="deep")
plt.grid()



# %%

df.groupby(by='cluster_kmean_padronizado')['IdCliente'].count()


# %%
# Visualizando os clusters formados pelos divisões "manuais" - cluster
sb.scatterplot(data=df,
               x="qtdeFrequencia",
               y="qtdePontosPos",
               hue="cluster",
               palette="deep")
plt.grid()

# %%
