import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import argparse
import warnings

warnings.filterwarnings('ignore')

# Parametros de ejecucion
parser = argparse.ArgumentParser()
parser.add_argument("--data-dir", default="data/raw",
                    help="Carpeta con Books.csv, Ratings.csv y Users.csv")
parser.add_argument("--figures-dir", default="reports/figures",
                    help="Carpeta donde se guardan las graficas")
parser.add_argument("--min-ratings", type=int, default=50,
                    help="Minimo de calificaciones explicitas para promediar por editorial o autor")
args = parser.parse_args()

DATA_DIR = args.data_dir
FIG_DIR = args.figures_dir
MIN_RATINGS = args.min_ratings

# Crear carpeta para guardar gráficas
os.makedirs(FIG_DIR, exist_ok=True)

# IMPORTAR BASES DE DATOS
books_df = pd.read_csv(os.path.join(DATA_DIR, "Books.csv"))
ratings_df = pd.read_csv(os.path.join(DATA_DIR, "Ratings.csv"))
users_df = pd.read_csv(os.path.join(DATA_DIR, "Users.csv"))

# Limpiar columnas
books_df.columns = [c.strip().replace('\ufeff', '') for c in books_df.columns]
ratings_df.columns = [c.strip().replace('\ufeff', '') for c in ratings_df.columns]
users_df.columns = [c.strip().replace('\ufeff', '') for c in users_df.columns]

# Fusionar tablas
df = ratings_df.merge(books_df, on='ISBN', how='left')
df = df.merge(users_df, on='User-ID', how='left')

# Limpiar datos atípicos
df['Year-Of-Publication'] = pd.to_numeric(df['Year-Of-Publication'], errors='coerce')

df['Age'] = pd.to_numeric(df['Age'], errors='coerce')

# 2004 es el año de recolección del dataset
df = df[df['Year-Of-Publication'].between(1801, 2004)]
df = df[df['Age'].between(5, 100)]

# Normalizar autores y editoriales antes de agrupar: la clave ignora
# mayusculas y espacios extremos, y cada grupo se muestra con su
# escritura original mas frecuente (en empate, la primera alfabeticamente)
for col in ['Book-Author', 'Publisher']:
    original = df[col].str.strip()
    clave = original.str.casefold()
    conteo = pd.DataFrame({'clave': clave, 'original': original}).value_counts().reset_index(name='n')
    conteo = conteo.sort_values(['clave', 'n', 'original'], ascending=[True, False, True])
    escritura = conteo.drop_duplicates('clave').set_index('clave')['original']
    df[col] = clave.map(escritura)

print("Registros totales:", len(df))
print("Columnas:", df.columns.tolist())


# EDA 1 - NUMERICO
# Año de publicación vs Calificación promedio
print("\nEDA 1: Año de publicación vs Calificación promedio")

df_h1 = df[['Year-Of-Publication', 'Book-Rating']].dropna()
df_h1 = df_h1[df_h1['Book-Rating'] > 0]

corr1 = df_h1['Year-Of-Publication'].corr(df_h1['Book-Rating'])

print(f"Correlacion año - calificacion: {corr1:.4f}")
print(df_h1.describe())
yearly_rating = (df_h1.groupby('Year-Of-Publication')['Book-Rating'].mean().reset_index())

plt.figure(figsize=(10, 5))
plt.plot(yearly_rating['Year-Of-Publication'], yearly_rating['Book-Rating'],
         marker='o', color='blue', linewidth=2)
plt.xlabel("Año de publicación")
plt.ylabel("Calificación promedio")
plt.title("Hallazgo 1: Año de publicación vs Calificación promedio")
plt.grid(axis='y', alpha=0.4)
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, "h1_year_vs_rating.png"))
plt.show()
plt.close()


# EDA 2 - NUMERICO
# Edad del usuario vs Calificación promedio
print("\n-----------------------------------------------------------------")
print("\nEDA 2: Edad del usuario vs Calificación promedio")

df_h2 = df[['Age', 'Book-Rating']].dropna()
df_h2 = df_h2[df_h2['Book-Rating'] > 0]

corr2 = df_h2['Age'].corr(df_h2['Book-Rating'])

print(f"Correlacion edad - calificacion: {corr2:.4f}")
print(df_h2.describe())

# Crear grupos de edad
df_h2['Grupo_Edad'] = pd.cut(
    df_h2['Age'],
    bins=[0, 12, 18, 30, 45, 60, 100],
    labels=['Niños', 'Adolescentes', 'Jovenes', 'Adultos', 'Maduros', 'Mayores'])

age_rating = (df_h2.groupby('Grupo_Edad')['Book-Rating'].mean().reset_index())

plt.figure(figsize=(10, 5))
plt.bar(age_rating['Grupo_Edad'], age_rating['Book-Rating'], color='orange')
plt.xlabel("Grupo de edad")
plt.ylabel("Calificación promedio")
plt.title("Hallazgo 2: Edad del usuario vs Calificación promedio")
plt.grid(axis='y', alpha=0.4)
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, "h2_age_vs_rating.png"))
plt.show()
plt.close()


# EDA 3 - CATEGORICO
# Editorial vs Calificación promedio
print("\n-----------------------------------------------------------------")
print("\nHALLAZGO 3: Editorial vs Calificación promedio")

df_h3 = df[['Publisher', 'Book-Rating']].dropna()
df_h3 = df_h3[df_h3['Book-Rating'] > 0]

publisher_stats = df_h3.groupby('Publisher')['Book-Rating'].agg(['mean', 'count'])
publisher_stats = publisher_stats[publisher_stats['count'] >= MIN_RATINGS]
publisher_rating = (publisher_stats['mean'].sort_values(ascending=False).head(15).reset_index())
publisher_rating.columns = ['Publisher', 'Avg_Rating']

if publisher_rating.empty:
    print(f"Aviso: ninguna editorial tiene al menos {MIN_RATINGS} calificaciones explicitas; no se genera la grafica")
else:
    print(publisher_rating)

    plt.figure(figsize=(10, 6))
    plt.barh(publisher_rating['Publisher'], publisher_rating['Avg_Rating'], color='green')
    plt.xlabel("Calificación promedio")
    plt.title("Hallazgo 3: Editorial vs Calificación promedio")
    plt.gca().invert_yaxis()
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "h3_publisher_vs_rating.png"))
    plt.show()
    plt.close()


# EDA 4 - CATEGORICO
# Autor vs Cantidad de ratings
print("\n-----------------------------------------------------------------")
print("\nHALLAZGO 4: Autor vs Cantidad de ratings")

df_h4 = df[['Book-Author', 'Book-Rating']].dropna()
df_h4 = df_h4[df_h4['Book-Rating'] > 0]

author_rating = (df_h4.groupby('Book-Author')['Book-Rating'].count().sort_values(ascending=False).head(15).reset_index())
author_rating.columns = ['Book-Author', 'Cantidad_Ratings']
print(author_rating)

plt.figure(figsize=(10, 6))
plt.barh(author_rating['Book-Author'], author_rating['Cantidad_Ratings'], color='red')
plt.xlabel("Cantidad de ratings")
plt.title("Hallazgo 4: Autor vs Cantidad de ratings")
plt.gca().invert_yaxis()
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, "h4_author_vs_ratings_count.png"))
plt.show()
plt.close()


# JUSTIFICACION DEL EDA
print("\nJustificacion Hallazgo 1:")
print(df_h1[['Year-Of-Publication', 'Book-Rating']].corr())

print("\nJustificacion Hallazgo 2:")
print(df_h2.groupby('Grupo_Edad')['Book-Rating'].mean())

print("\nJustificacion Hallazgo 3:")
print(df_h3.groupby('Publisher')['Book-Rating'].count().sort_values(ascending=False).head(10))

print("\nJustificacion Hallazgo 4:")
author_stats = df_h4.groupby('Book-Author')['Book-Rating'].agg(['mean', 'count'])
author_stats = author_stats[author_stats['count'] >= MIN_RATINGS]
if author_stats.empty:
    print(f"Aviso: ningun autor tiene al menos {MIN_RATINGS} calificaciones explicitas")
else:
    print(author_stats['mean'].sort_values(ascending=False).head(10))


# ANALISIS PREDICTIVO
from sklearn.model_selection import train_test_split
from sklearn.metrics import (confusion_matrix, f1_score, r2_score, mean_squared_error)
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import (RandomForestClassifier, RandomForestRegressor)
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.dummy import (DummyRegressor, DummyClassifier)


# Hallazgo 1: Regresión Lineal
print("\n-----------------------------------------------------------------")
print("\nANALISIS PREDICTIVO | Hallazgo 1: Regresion Lineal")

df_h1 = df[['Year-Of-Publication', 'Book-Rating']].dropna()

df_h1 = df_h1[df_h1['Book-Rating'] > 0]

X = df_h1[['Year-Of-Publication']]
Y = df_h1['Book-Rating']

X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2, random_state=42)

modeloRL = LinearRegression()
modeloRL.fit(X_train, Y_train)

prediccionRL = modeloRL.predict(X_test)
rmse_rl = np.sqrt(mean_squared_error(Y_test, prediccionRL))
r2_rl = r2_score(Y_test, prediccionRL)
print("RMSE:", rmse_rl)
print("R2:", r2_rl)

# Baseline: predice siempre la media
baselineRL = DummyRegressor(strategy="mean")
baselineRL.fit(X_train, Y_train)
prediccionBL = baselineRL.predict(X_test)
print("Baseline RMSE:", np.sqrt(mean_squared_error(Y_test, prediccionBL)))
print("Baseline R2:", r2_score(Y_test, prediccionBL))

# Prueba random
prueba_h1 = pd.DataFrame([{ 'Year-Of-Publication': 2005 }])
pred_h1 = modeloRL.predict(prueba_h1)
print(pred_h1)


# Hallazgo 2: Random Forest Regressor
print("\n-----------------------------------------------------------------")
print("\nANALISIS PREDICTIVO | Hallazgo 2: Random Forest Regressor")

df_h2 = df[['Age', 'Year-Of-Publication', 'Book-Rating']].dropna()

df_h2 = df_h2[df_h2['Book-Rating'] > 0]

X = df_h2[['Age', 'Year-Of-Publication']]
Y = df_h2['Book-Rating']

X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2, random_state=42)

modeloRF = RandomForestRegressor(n_estimators=100, random_state=42)
modeloRF.fit(X_train, Y_train)

prediccionRF = modeloRF.predict(X_test)
rmse_rf = np.sqrt(mean_squared_error(Y_test, prediccionRF))
r2_rf = r2_score(Y_test, prediccionRF)
print("RMSE:", rmse_rf)
print("R2:", r2_rf)

# Baseline: predice siempre la media
baselineRF = DummyRegressor(strategy="mean")
baselineRF.fit(X_train, Y_train)
prediccionBL = baselineRF.predict(X_test)
print("Baseline RMSE:", np.sqrt(mean_squared_error(Y_test, prediccionBL)))
print("Baseline R2:", r2_score(Y_test, prediccionBL))

# Prueba random
prueba_h2 = pd.DataFrame([{
    'Age': 30,
    'Year-Of-Publication': 2000 }])
pred_h2 = modeloRF.predict(prueba_h2)
print(pred_h2)


# Hallazgo 3: Random Forest Classifier
print("\n-----------------------------------------------------------------")
print("\nANALISIS PREDICTIVO | Hallazgo 3: Random Forest")

df_h3 = df[['Age', 'Year-Of-Publication', 'Book-Rating']].dropna()

df_h3 = df_h3[df_h3['Book-Rating'] > 0]

# Clasificación binaria
df_h3['Rating_Alto'] = np.where(df_h3['Book-Rating'] >= 5, 'Alto', 'Bajo')

X = df_h3[['Age', 'Year-Of-Publication']]
Y = df_h3['Rating_Alto']

X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2, random_state=42)

modeloRF = RandomForestClassifier(n_estimators=100, random_state=42)
modeloRF.fit(X_train, Y_train)

prediccionRF = modeloRF.predict(X_test)
mcRF = confusion_matrix(Y_test, prediccionRF)
print(mcRF)
f1RF = f1_score(Y_test, prediccionRF, average=None)
print(f1RF)
print("F1 macro:", f1_score(Y_test, prediccionRF, average='macro'))

# Baseline: predice al azar respetando la proporcion de clases
baselineRFC = DummyClassifier(strategy="stratified", random_state=42)
baselineRFC.fit(X_train, Y_train)
prediccionBL = baselineRFC.predict(X_test)
print("Baseline F1:", f1_score(Y_test, prediccionBL, average=None))
print("Baseline F1 macro:", f1_score(Y_test, prediccionBL, average='macro'))

# Prueba random
prueba_h3 = pd.DataFrame([{
    'Age': 25,
    'Year-Of-Publication': 2010 }])
pred_h3 = modeloRF.predict(prueba_h3)
print(pred_h3)


# Hallazgo 4: Decision Tree
print("\n-----------------------------------------------------------------")
print("\nANALISIS PREDICTIVO | Hallazgo 4: Decision Tree")

df_h4 = df[['Age', 'Year-Of-Publication', 'Book-Rating']].dropna()

df_h4 = df_h4[df_h4['Book-Rating'] > 0]

df_h4['Grupo_Rating'] = pd.cut(df_h4['Book-Rating'],
    bins=[0, 3, 6, 10],
    labels=['Bajo', 'Medio', 'Alto'])

X = df_h4[['Age', 'Year-Of-Publication']]
Y = df_h4['Grupo_Rating']

X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2, random_state=42)

modeloDT = DecisionTreeClassifier(max_depth=5, random_state=42)
modeloDT.fit(X_train, Y_train)

prediccionDT = modeloDT.predict(X_test)
mcDT = confusion_matrix(Y_test, prediccionDT)
print(mcDT)
f1DT = f1_score(Y_test, prediccionDT, average=None)
print(f1DT)
print("F1 macro:", f1_score(Y_test, prediccionDT, average='macro'))

# Baseline: predice al azar respetando la proporcion de clases
baselineDT = DummyClassifier(strategy="stratified", random_state=42)
baselineDT.fit(X_train, Y_train)
prediccionBL = baselineDT.predict(X_test)
print("Baseline F1:", f1_score(Y_test, prediccionBL, average=None))
print("Baseline F1 macro:", f1_score(Y_test, prediccionBL, average='macro'))

# Prueba random
prueba_h4 = pd.DataFrame([{
    'Age': 40,
    'Year-Of-Publication': 1995 }])
pred_h4 = modeloDT.predict(prueba_h4)
print(pred_h4)