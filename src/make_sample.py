import pandas as pd
import os
import argparse

# Genera una muestra reproducible de Books.csv, Ratings.csv y Users.csv
# para ejecutar proyecto.py sin descargar el dataset completo.

parser = argparse.ArgumentParser()
parser.add_argument("--data-dir", default="data/raw",
                    help="Carpeta con los CSV completos")
parser.add_argument("--out-dir", default="data/sample",
                    help="Carpeta donde se guarda la muestra")
parser.add_argument("--min-explicit", type=int, default=1000,
                    help="Calificaciones explicitas validas que deben quedar tras el ETL")
args = parser.parse_args()

SEED = 42
# Proporcion de calificaciones implicitas (0) respecto a las explicitas
IMPLICIT_RATIO = 0.25

# Leer como texto para guardar los valores sin alterarlos
books_df = pd.read_csv(os.path.join(args.data_dir, "Books.csv"), dtype=str, keep_default_na=False)
ratings_df = pd.read_csv(os.path.join(args.data_dir, "Ratings.csv"), dtype=str, keep_default_na=False)
users_df = pd.read_csv(os.path.join(args.data_dir, "Users.csv"), dtype=str, keep_default_na=False)

# Limpiar columnas
books_df.columns = [c.strip().replace('﻿', '') for c in books_df.columns]
ratings_df.columns = [c.strip().replace('﻿', '') for c in ratings_df.columns]
users_df.columns = [c.strip().replace('﻿', '') for c in users_df.columns]

# Marcar las calificaciones que pasan los filtros del ETL de proyecto.py
anio = books_df.drop_duplicates('ISBN').set_index('ISBN')['Year-Of-Publication']
edad = users_df.drop_duplicates('User-ID').set_index('User-ID')['Age']

anio_rating = pd.to_numeric(ratings_df['ISBN'].map(anio), errors='coerce')
edad_rating = pd.to_numeric(ratings_df['User-ID'].map(edad), errors='coerce')
valida = anio_rating.between(1801, 2004) & edad_rating.between(5, 100)

explicita = pd.to_numeric(ratings_df['Book-Rating'], errors='coerce') > 0

# Priorizar explicitas: tomar el menor numero de ellas (en orden aleatorio)
# con el que se alcanzan las explicitas validas pedidas
explicitas = ratings_df[explicita].sample(frac=1, random_state=SEED)
validas_acum = valida[explicitas.index].cumsum()
n_explicitas = int((validas_acum < args.min_explicit).sum()) + 1
explicitas = explicitas.iloc[:n_explicitas]

n_implicitas = int(n_explicitas * IMPLICIT_RATIO)
implicitas = ratings_df[~explicita].sample(n=n_implicitas, random_state=SEED)

ratings_sample = pd.concat([explicitas, implicitas]).sort_index()

# Filtrar libros y usuarios a los que aparecen en la muestra
books_sample = books_df[books_df['ISBN'].isin(ratings_sample['ISBN'])]
users_sample = users_df[users_df['User-ID'].isin(ratings_sample['User-ID'])]

os.makedirs(args.out_dir, exist_ok=True)
ratings_sample.to_csv(os.path.join(args.out_dir, "Ratings.csv"), index=False)
books_sample.to_csv(os.path.join(args.out_dir, "Books.csv"), index=False)
users_sample.to_csv(os.path.join(args.out_dir, "Users.csv"), index=False)

print("Calificaciones:", len(ratings_sample),
      f"({n_explicitas} explicitas, {n_implicitas} implicitas)")
print("Explicitas validas tras el ETL:", int(valida[explicitas.index].sum()))
print("Libros:", len(books_sample))
print("Usuarios:", len(users_sample))
