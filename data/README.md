# Generated Dataset Layout

Synthetic dataset outputs are generated under `data/generated/q4_2025` by default.

## Folder structure

- `reference/`
  - `stores.csv`
  - `brands.csv`
  - `products.csv`
  - `calendar_q4.csv`
- `core/`
  - `customers.csv`
  - `customer_preferences.csv`
  - `saved_items.csv`
- `sales/`
  - `transactions_part_0001.csv`, `transactions_part_0002.csv`, ...
  - `transaction_items_part_0001.csv`, `transaction_items_part_0002.csv`, ...
  - `returns_part_0001.csv`, `returns_part_0002.csv`, ...
- `meta/`
  - `manifest.json`

`manifest.json` records scale parameters, row counts, and exact file paths produced by the generator.
