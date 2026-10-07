# Ingestia zamówień

Pipeline czyta pliki z zamówieniami z `data/raw/`, czyści i waliduje rekordy, a wynik w dwóch
tabelach (zamówienia i pozycje zamówień) zapisuje do PostgreSQL. Ten sam kod potrafi też zapisać
wynik do plików CSV w `data/curated/`.

## Uruchomienie

Najpierw działający kontener z bazą (`postgres-de`) i tabele:

```
docker exec -i postgres-de psql -U postgres -d de_fundamentals < schema.sql
```

Potem pipeline:

```
uv run python -m src.main
```

Testy:

```
uv run pytest
```

## Układ projektu

- `src/clients/` - skąd biorą się dane (źródło plikowe i jego kontrakt)
- `src/transforms/` - czyszczenie, walidacja i normalizacja danych
- `src/repositories/` - dokąd trafia wynik (PostgreSQL albo CSV, ten sam kontrakt)
- `src/db/` - połączenie z bazą
- `src/main.py` - spina warstwy
- `schema.sql` - tabele docelowe
