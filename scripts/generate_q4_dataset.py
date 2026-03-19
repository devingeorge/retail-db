#!/usr/bin/env python3
"""
Generate a deterministic synthetic Q4 retail dataset and emit CSV files.

Default output targets Fortune-1000-scale local analytics:
- ~10M transactions in Q4 2025
- Chunked sales CSV files for efficient local import
"""

from __future__ import annotations

import argparse
import csv
import json
import random
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Dict, List, Sequence, Tuple


FIRST_NAMES = [
    "Ava", "Liam", "Noah", "Emma", "Olivia", "Sophia", "Elijah", "Lucas", "Mia", "Amelia",
    "Harper", "Evelyn", "James", "Benjamin", "Isabella", "Mason", "Charlotte", "Logan", "Ethan",
    "Abigail", "Sofia", "Aiden", "Jackson", "Aria", "Daniel", "Henry", "Sebastian", "Scarlett",
    "Camila", "Levi", "Mateo", "Nora", "Chloe", "Ella", "Avery", "David", "Wyatt", "Asher",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez",
    "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor",
    "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez",
    "Clark", "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King", "Wright",
]

REGIONS = ["Northeast", "Southeast", "Midwest", "Southwest", "West"]
STATE_CODES = ["CA", "TX", "FL", "NY", "IL", "WA", "GA", "NC", "OH", "PA", "AZ", "MA"]
CITIES = ["San Diego", "Austin", "Miami", "Brooklyn", "Chicago", "Seattle", "Atlanta", "Charlotte", "Columbus", "Phoenix"]

TIERS = ["Bronze", "Silver", "Gold", "Platinum"]
TIER_WEIGHTS = [0.47, 0.31, 0.17, 0.05]

LTV_BANDS = ["Low", "Medium", "High", "VIP"]
TIER_TO_LTV_WEIGHTS = {
    "Bronze": [0.72, 0.24, 0.04, 0.00],
    "Silver": [0.23, 0.59, 0.16, 0.02],
    "Gold": [0.06, 0.36, 0.46, 0.12],
    "Platinum": [0.01, 0.08, 0.39, 0.52],
}

SIZES = ["XS", "S", "M", "L", "XL", "XXL", "2", "4", "6", "8", "10", "12", "32", "34", "36", "38"]
COLORS = ["Black", "White", "Blue", "Red", "Green", "Navy", "Beige", "Gray", "Pink", "Brown"]
OCCASIONS = ["Work", "Weekend", "Travel", "Formal", "Athleisure", "Holiday", "Gift"]

BRAND_NAMES = [
    "Northline", "Everpeak", "Oakstone", "Vela", "Aurora", "SummitCo", "Ridgeway", "BlueAtlas",
    "Lumen", "Harbor", "MetroThread", "Elm&Ash", "Kindred", "Stellar", "Fieldhouse", "Tidal",
    "Mariner", "Foundry", "Portland", "ClassicLine", "Willow", "Canyon", "Aspen", "Vantage",
    "Keystone", "Lark", "Pioneer", "CloudNine", "Monarch", "Drift", "Arcadia", "Merit", "Axiom",
    "Slate", "Mosaic", "Crescent", "Anchor", "Prairie", "Helix", "Verdant", "Peakline", "Riverbend",
]

CATEGORIES = ["Tops", "Bottoms", "Outerwear", "Footwear", "Accessories", "Beauty", "Home", "Kids", "Activewear"]
CATEGORY_WEIGHTS = [0.19, 0.17, 0.11, 0.14, 0.10, 0.07, 0.08, 0.07, 0.07]

RETURN_REASONS = [
    "size_issue",
    "quality_issue",
    "damaged_in_shipping",
    "late_delivery",
    "changed_mind",
    "wrong_item",
]

PAYMENT_METHODS = ["card", "cash", "wallet", "gift_card"]
PAYMENT_WEIGHTS = [0.59, 0.17, 0.19, 0.05]

CHANNELS = ["in_store", "online", "mobile"]
CHANNEL_WEIGHTS = [0.55, 0.30, 0.15]

STYLIST_NOTES = [
    "Prefers capsule wardrobe and neutral layering pieces.",
    "Responds well to premium basics and tailored fits.",
    "Shops for seasonal refreshes and holiday gifting bundles.",
    "Looks for value bundles and family essentials.",
    "Frequently adds accessories to complete outfits.",
    "Prefers breathable fabrics and comfort-first silhouettes.",
    "Leans toward trend-forward colors in limited runs.",
]


@dataclass
class ProductInfo:
    product_id: int
    category: str
    unit_price: float


class CsvChunkWriter:
    def __init__(self, base_dir: Path, file_prefix: str, header: Sequence[str], chunk_size: int) -> None:
        self.base_dir = base_dir
        self.file_prefix = file_prefix
        self.header = list(header)
        self.chunk_size = chunk_size
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.part_index = 0
        self.rows_in_part = 0
        self.total_rows = 0
        self._file = None
        self._writer = None
        self.files: List[str] = []
        self._open_new_part()

    def _open_new_part(self) -> None:
        if self._file is not None:
            self._file.close()
        self.part_index += 1
        filename = f"{self.file_prefix}_part_{self.part_index:04d}.csv"
        path = self.base_dir / filename
        self._file = path.open("w", newline="", encoding="utf-8")
        self._writer = csv.writer(self._file)
        self._writer.writerow(self.header)
        self.rows_in_part = 0
        self.files.append(str(path))

    def write_row(self, row: Sequence[object]) -> None:
        assert self._writer is not None
        if self.rows_in_part >= self.chunk_size:
            self._open_new_part()
        self._writer.writerow(row)
        self.rows_in_part += 1
        self.total_rows += 1

    def close(self) -> None:
        if self._file is not None:
            self._file.close()
            self._file = None


def weighted_choice(rng: random.Random, values: Sequence[str], weights: Sequence[float]) -> str:
    return rng.choices(values, weights=weights, k=1)[0]


def random_subset(rng: random.Random, values: Sequence[str], min_size: int, max_size: int) -> List[str]:
    size = rng.randint(min_size, max_size)
    return rng.sample(list(values), k=min(size, len(values)))


def q4_dates_with_weights() -> Tuple[List[date], List[float]]:
    start = date(2025, 10, 1)
    end = date(2025, 12, 31)
    days: List[date] = []
    weights: List[float] = []
    current = start
    while current <= end:
        weight = 1.0
        if current.month == 11:
            weight *= 1.20
        if current.month == 12:
            weight *= 1.65
        if current == date(2025, 11, 28):  # Black Friday
            weight *= 6.0
        if current == date(2025, 12, 1):  # Cyber Monday
            weight *= 4.0
        if current.weekday() in (4, 5, 6):  # Fri-Sun
            weight *= 1.35
        days.append(current)
        weights.append(weight)
        current += timedelta(days=1)
    return days, weights


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate synthetic retail Q4 CSV dataset.")
    parser.add_argument("--output-dir", default="data/generated/q4_2025", help="Output directory for generated CSV files.")
    parser.add_argument("--seed", type=int, default=1001, help="Random seed for deterministic generation.")
    parser.add_argument("--customers", type=int, default=750_000, help="Number of customers to generate.")
    parser.add_argument("--stores", type=int, default=1_100, help="Number of stores to generate.")
    parser.add_argument("--products", type=int, default=120_000, help="Number of products to generate.")
    parser.add_argument("--transactions", type=int, default=10_000_000, help="Number of Q4 transactions to generate.")
    parser.add_argument("--chunk-size", type=int, default=1_000_000, help="Rows per chunk for large sales CSV outputs.")
    parser.add_argument("--saved-item-rate", type=float, default=0.39, help="Fraction of customers with at least one saved item.")
    parser.add_argument("--return-rate", type=float, default=0.09, help="Base return rate at line-item level.")
    return parser


def ensure_dirs(root: Path) -> Dict[str, Path]:
    paths = {
        "reference": root / "reference",
        "core": root / "core",
        "sales": root / "sales",
        "meta": root / "meta",
    }
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    return paths


def generate_reference_files(
    rng: random.Random,
    dirs: Dict[str, Path],
    store_count: int,
    product_count: int,
) -> Dict[int, ProductInfo]:
    stores_path = dirs["reference"] / "stores.csv"
    brands_path = dirs["reference"] / "brands.csv"
    products_path = dirs["reference"] / "products.csv"
    calendar_path = dirs["reference"] / "calendar_q4.csv"

    with stores_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["store_id", "store_name", "region", "state_code", "city"])
        for store_id in range(1, store_count + 1):
            region = rng.choice(REGIONS)
            state = rng.choice(STATE_CODES)
            city = rng.choice(CITIES)
            writer.writerow([store_id, f"Store-{store_id:04d}", region, state, city])

    with brands_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["brand_id", "brand_name"])
        for i, brand in enumerate(BRAND_NAMES, start=1):
            writer.writerow([i, brand])

    product_map: Dict[int, ProductInfo] = {}
    with products_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["product_id", "sku", "product_name", "category", "brand_id", "color", "size_code", "list_price"])
        for product_id in range(1, product_count + 1):
            category = weighted_choice(rng, CATEGORIES, CATEGORY_WEIGHTS)
            brand_id = rng.randint(1, len(BRAND_NAMES))
            color = rng.choice(COLORS)
            size_code = rng.choice(SIZES)
            base_price = {
                "Tops": 49,
                "Bottoms": 59,
                "Outerwear": 139,
                "Footwear": 99,
                "Accessories": 39,
                "Beauty": 24,
                "Home": 69,
                "Kids": 36,
                "Activewear": 54,
            }[category]
            price = round(max(8, rng.gauss(base_price, base_price * 0.28)), 2)
            sku = f"SKU-{category[:3].upper()}-{product_id:07d}"
            name = f"{category} Item {product_id:07d}"
            writer.writerow([product_id, sku, name, category, brand_id, color, size_code, f"{price:.2f}"])
            product_map[product_id] = ProductInfo(product_id=product_id, category=category, unit_price=price)

    q4_days, _ = q4_dates_with_weights()
    with calendar_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["calendar_date", "month", "day_of_week", "is_weekend", "is_black_friday", "is_cyber_monday"])
        for d in q4_days:
            writer.writerow(
                [
                    d.isoformat(),
                    d.month,
                    d.strftime("%A"),
                    d.weekday() >= 5,
                    d == date(2025, 11, 28),
                    d == date(2025, 12, 1),
                ]
            )

    return product_map


def generate_core_files(
    rng: random.Random,
    dirs: Dict[str, Path],
    customer_count: int,
    store_count: int,
    product_count: int,
    saved_item_rate: float,
) -> None:
    customers_path = dirs["core"] / "customers.csv"
    prefs_path = dirs["core"] / "customer_preferences.csv"
    saved_items_path = dirs["core"] / "saved_items.csv"

    saved_item_id = 1
    with (
        customers_path.open("w", newline="", encoding="utf-8") as fc,
        prefs_path.open("w", newline="", encoding="utf-8") as fp,
        saved_items_path.open("w", newline="", encoding="utf-8") as fs,
    ):
        c_writer = csv.writer(fc)
        p_writer = csv.writer(fp)
        s_writer = csv.writer(fs)
        c_writer.writerow(
            [
                "customer_id",
                "loyalty_id",
                "first_name",
                "last_name",
                "tier",
                "preferred_store_id",
                "stylist_notes",
                "lifetime_value_band",
                "created_at",
            ]
        )
        p_writer.writerow(
            [
                "customer_id",
                "preferred_sizes",
                "preferred_colors",
                "preferred_brands",
                "shopping_occasions",
                "updated_at",
            ]
        )
        s_writer.writerow(["saved_item_id", "customer_id", "product_id", "saved_at"])

        for customer_id in range(1, customer_count + 1):
            tier = weighted_choice(rng, TIERS, TIER_WEIGHTS)
            ltv_band = weighted_choice(rng, LTV_BANDS, TIER_TO_LTV_WEIGHTS[tier])
            preferred_store_id = ((customer_id * 7) % store_count) + 1
            first_name = rng.choice(FIRST_NAMES)
            last_name = rng.choice(LAST_NAMES)
            loyalty_id = f"LOY-{customer_id:010d}"
            created_at = date(2020, 1, 1) + timedelta(days=rng.randint(0, 2100))

            c_writer.writerow(
                [
                    customer_id,
                    loyalty_id,
                    first_name,
                    last_name,
                    tier,
                    preferred_store_id,
                    rng.choice(STYLIST_NOTES),
                    ltv_band,
                    created_at.isoformat(),
                ]
            )

            sizes = random_subset(rng, SIZES, 2, 4)
            colors = random_subset(rng, COLORS, 2, 4)
            brands = random_subset(rng, BRAND_NAMES, 3, 7)
            occasions = random_subset(rng, OCCASIONS, 2, 4)
            updated_at = datetime(2025, 12, rng.randint(1, 28), rng.randint(0, 23), rng.randint(0, 59), rng.randint(0, 59))
            p_writer.writerow(
                [
                    customer_id,
                    "{" + ",".join(sizes) + "}",
                    "{" + ",".join(colors) + "}",
                    "{" + ",".join(brands) + "}",
                    "{" + ",".join(occasions) + "}",
                    updated_at.isoformat(),
                ]
            )

            if rng.random() < saved_item_rate:
                num_saved = rng.randint(1, 8)
                for _ in range(num_saved):
                    saved_ts = datetime(2025, rng.randint(10, 12), rng.randint(1, 28), rng.randint(0, 23), rng.randint(0, 59), rng.randint(0, 59))
                    s_writer.writerow([saved_item_id, customer_id, rng.randint(1, product_count), saved_ts.isoformat()])
                    saved_item_id += 1


def choose_return_probability(base_rate: float, category: str, channel: str) -> float:
    category_modifier = {
        "Tops": 1.05,
        "Bottoms": 1.15,
        "Outerwear": 0.90,
        "Footwear": 1.25,
        "Accessories": 0.70,
        "Beauty": 0.45,
        "Home": 0.55,
        "Kids": 1.10,
        "Activewear": 0.95,
    }[category]
    channel_modifier = {"in_store": 0.9, "online": 1.2, "mobile": 1.1}[channel]
    return min(0.65, base_rate * category_modifier * channel_modifier)


def generate_sales_files(
    rng: random.Random,
    dirs: Dict[str, Path],
    customer_count: int,
    store_count: int,
    transaction_count: int,
    chunk_size: int,
    product_map: Dict[int, ProductInfo],
    base_return_rate: float,
) -> Dict[str, int | List[str]]:
    tx_writer = CsvChunkWriter(
        base_dir=dirs["sales"],
        file_prefix="transactions",
        header=[
            "transaction_id",
            "customer_id",
            "store_id",
            "transaction_ts",
            "sales_channel",
            "payment_method",
            "gross_amount",
            "discount_amount",
            "net_amount",
        ],
        chunk_size=chunk_size,
    )
    item_writer = CsvChunkWriter(
        base_dir=dirs["sales"],
        file_prefix="transaction_items",
        header=[
            "transaction_item_id",
            "transaction_id",
            "product_id",
            "quantity",
            "unit_price",
            "discount_amount",
            "line_total",
        ],
        chunk_size=chunk_size,
    )
    return_writer = CsvChunkWriter(
        base_dir=dirs["sales"],
        file_prefix="returns",
        header=["return_id", "transaction_item_id", "customer_id", "return_ts", "reason_code", "refund_amount"],
        chunk_size=chunk_size,
    )

    q4_days, q4_weights = q4_dates_with_weights()
    transaction_item_id = 1
    return_id = 1

    for transaction_id in range(1, transaction_count + 1):
        customer_id = rng.randint(1, customer_count)
        preferred_store_id = ((customer_id * 7) % store_count) + 1
        store_id = preferred_store_id if rng.random() < 0.62 else rng.randint(1, store_count)

        tx_date = rng.choices(q4_days, weights=q4_weights, k=1)[0]
        tx_time = time(rng.randint(8, 22), rng.randint(0, 59), rng.randint(0, 59))
        tx_ts = datetime.combine(tx_date, tx_time)
        channel = weighted_choice(rng, CHANNELS, CHANNEL_WEIGHTS)
        payment_method = weighted_choice(rng, PAYMENT_METHODS, PAYMENT_WEIGHTS)

        item_count = rng.choices([1, 2, 3, 4, 5], weights=[0.44, 0.30, 0.16, 0.07, 0.03], k=1)[0]
        gross = 0.0
        discount = 0.0

        for _ in range(item_count):
            product_id = rng.randint(1, len(product_map))
            product = product_map[product_id]
            quantity = rng.choices([1, 2, 3], weights=[0.78, 0.18, 0.04], k=1)[0]
            unit_price = product.unit_price
            line_gross = unit_price * quantity

            holiday_multiplier = 1.0
            if tx_date in (date(2025, 11, 28), date(2025, 12, 1)):
                holiday_multiplier = 1.8
            elif tx_date.month == 12:
                holiday_multiplier = 1.25
            promo_rate = min(0.52, max(0.0, rng.gauss(0.11 * holiday_multiplier, 0.06)))

            line_discount = round(line_gross * promo_rate, 2)
            line_total = round(line_gross - line_discount, 2)
            gross += line_gross
            discount += line_discount

            item_writer.write_row(
                [
                    transaction_item_id,
                    transaction_id,
                    product_id,
                    quantity,
                    f"{unit_price:.2f}",
                    f"{line_discount:.2f}",
                    f"{line_total:.2f}",
                ]
            )

            if rng.random() < choose_return_probability(base_return_rate, product.category, channel):
                return_delay = rng.randint(3, 50)
                return_ts = tx_ts + timedelta(days=return_delay, hours=rng.randint(0, 23), minutes=rng.randint(0, 59))
                refund_ratio = rng.uniform(0.78, 1.00)
                refund_amount = round(line_total * refund_ratio, 2)
                reason = rng.choice(RETURN_REASONS)
                return_writer.write_row(
                    [return_id, transaction_item_id, customer_id, return_ts.isoformat(), reason, f"{refund_amount:.2f}"]
                )
                return_id += 1

            transaction_item_id += 1

        net = round(gross - discount, 2)
        tx_writer.write_row(
            [
                transaction_id,
                customer_id,
                store_id,
                tx_ts.isoformat(),
                channel,
                payment_method,
                f"{gross:.2f}",
                f"{discount:.2f}",
                f"{net:.2f}",
            ]
        )

    tx_writer.close()
    item_writer.close()
    return_writer.close()

    return {
        "transactions_rows": tx_writer.total_rows,
        "transaction_items_rows": item_writer.total_rows,
        "returns_rows": return_writer.total_rows,
        "transactions_files": tx_writer.files,
        "transaction_items_files": item_writer.files,
        "returns_files": return_writer.files,
    }


def count_csv_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8") as f:
        return sum(1 for _ in f) - 1


def write_manifest(
    output_root: Path,
    config: argparse.Namespace,
    sales_meta: Dict[str, int | List[str]],
) -> None:
    core_dir = output_root / "core"
    reference_dir = output_root / "reference"
    meta = {
        "dataset_name": "fortune1000_retail_q4_2025",
        "generated_at_utc": datetime.utcnow().isoformat() + "Z",
        "random_seed": config.seed,
        "scale": {
            "customers": config.customers,
            "stores": config.stores,
            "products": config.products,
            "transactions": config.transactions,
        },
        "period": {"start": "2025-10-01", "end": "2025-12-31"},
        "row_counts": {
            "stores": count_csv_rows(reference_dir / "stores.csv"),
            "brands": count_csv_rows(reference_dir / "brands.csv"),
            "products": count_csv_rows(reference_dir / "products.csv"),
            "customers": count_csv_rows(core_dir / "customers.csv"),
            "customer_preferences": count_csv_rows(core_dir / "customer_preferences.csv"),
            "saved_items": count_csv_rows(core_dir / "saved_items.csv"),
            "transactions": sales_meta["transactions_rows"],
            "transaction_items": sales_meta["transaction_items_rows"],
            "returns": sales_meta["returns_rows"],
        },
        "files": {
            "reference": [str(p) for p in sorted(reference_dir.glob("*.csv"))],
            "core": [str(p) for p in sorted(core_dir.glob("*.csv"))],
            "sales": {
                "transactions": sales_meta["transactions_files"],
                "transaction_items": sales_meta["transaction_items_files"],
                "returns": sales_meta["returns_files"],
            },
        },
    }

    manifest_path = output_root / "meta" / "manifest.json"
    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
        f.write("\n")


def main() -> None:
    args = build_arg_parser().parse_args()
    rng = random.Random(args.seed)

    output_root = Path(args.output_dir).resolve()
    dirs = ensure_dirs(output_root)

    product_map = generate_reference_files(
        rng=rng,
        dirs=dirs,
        store_count=args.stores,
        product_count=args.products,
    )

    generate_core_files(
        rng=rng,
        dirs=dirs,
        customer_count=args.customers,
        store_count=args.stores,
        product_count=args.products,
        saved_item_rate=args.saved_item_rate,
    )

    sales_meta = generate_sales_files(
        rng=rng,
        dirs=dirs,
        customer_count=args.customers,
        store_count=args.stores,
        transaction_count=args.transactions,
        chunk_size=args.chunk_size,
        product_map=product_map,
        base_return_rate=args.return_rate,
    )

    write_manifest(output_root=output_root, config=args, sales_meta=sales_meta)
    print(f"Dataset generated at: {output_root}")
    print(f"Manifest: {output_root / 'meta' / 'manifest.json'}")


if __name__ == "__main__":
    main()
