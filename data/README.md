# Data

This project uses the **Book-Crossing** dataset: three CSV files with books, users and the ratings users gave to books.

| File | Content |
|---|---|
| `Books.csv` | ISBN, title, author, year of publication, publisher, cover image URLs |
| `Users.csv` | User ID, location, age |
| `Ratings.csv` | User ID, ISBN, rating (`0` = implicit interaction, `1`–`10` = explicit rating) |

## Source

- **Download:** Kaggle, "Book Recommendation Dataset" by arashnic —
  <https://www.kaggle.com/datasets/arashnic/book-recommendation-dataset>
- **Original work:** Ziegler, C.-N., McNee, S. M., Konstan, J. A., & Lausen, G. (2005).
  Improving recommendation lists through topic diversification.
  *Proceedings of the 14th International Conference on World Wide Web*, 22–32.

The data was collected from the Book-Crossing community in 2004.

## License

The MIT license of this repository covers the code only, not the data.
Kaggle publishes this dataset under a CC0 license; the original dataset was released
with free access for research purposes. Check both sources before reusing the data.

## Folders

| Folder | In the repository? | Content |
|---|---|---|
| `data/raw/` | No (ignored by git) | The full dataset, downloaded by you |
| `data/sample/` | Yes | A small reproducible subset to run the pipeline without downloading anything |

### Getting the full dataset

1. Download the dataset from the Kaggle page above (a free Kaggle account is required).
2. Unzip it and copy `Books.csv`, `Ratings.csv` and `Users.csv` into `data/raw/`:

   ```
   data/raw/
   ├── Books.csv
   ├── Ratings.csv
   └── Users.csv
   ```

3. Run the pipeline from the repository root:

   ```bash
   python src/proyecto.py --data-dir data/raw
   ```

### How the sample was built

`data/sample/` was generated from the full dataset with:

```bash
python src/make_sample.py --data-dir data/raw --out-dir data/sample
```

The script uses seed `42`. It shuffles the explicit ratings and keeps the smallest number of them
that still leaves at least 1,000 explicit ratings with a valid age (5–100) and publication year
(1801–2004) after the ETL. It then adds implicit ratings equal to 25% of that number and keeps only
the books and users that appear in the selected ratings.

| File | Rows | Size |
|---|---|---|
| `Ratings.csv` | 2,011 (1,609 explicit + 402 implicit) | 41 KB |
| `Books.csv` | 1,758 | 465 KB |
| `Users.csv` | 1,656 | 66 KB |
