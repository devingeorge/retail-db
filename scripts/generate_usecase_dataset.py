#!/usr/bin/env python3
"""
Generate a compact retail dataset for two demo use cases:
1) Store associate assist
2) Merchandising analysis
"""

from __future__ import annotations

import argparse
import csv
import json
import random
from pathlib import Path


CATEGORIES = ["Denim", "Tees", "Dresses", "Sneakers", "Outerwear", "Athleisure"]
COLORS = ["Black", "White", "Navy", "Olive", "Red", "Pink", "Gray", "Beige", "Blue"]
SIZES = ["XS", "S", "M", "L", "XL", "2", "4", "6", "8", "10", "12"]
REGIONS = ["Northeast", "Southeast", "Midwest", "Southwest", "West"]
TIERS = ["Bronze", "Silver", "Gold", "Platinum"]

REGION_CITY_STREET = {
    "Northeast": [
        ("Boston", "Boylston Street"),
        ("New York", "Fifth Avenue"),
        ("Philadelphia", "Market Street"),
        ("Providence", "Main Street"),
        ("Hartford", "Broad Street"),
        ("Newark", "Canal Street"),
    ],
    "Southeast": [
        ("Atlanta", "Peachtree Street"),
        ("Charlotte", "Tryon Street"),
        ("Nashville", "Broadway"),
        ("Orlando", "Orange Avenue"),
        ("Miami", "Biscayne Boulevard"),
        ("Raleigh", "Hillsborough Street"),
    ],
    "Midwest": [
        ("Chicago", "Michigan Avenue"),
        ("Columbus", "High Street"),
        ("Detroit", "Woodward Avenue"),
        ("Cleveland", "Euclid Avenue"),
        ("Indianapolis", "Meridian Street"),
        ("Milwaukee", "Wisconsin Avenue"),
    ],
    "Southwest": [
        ("Dallas", "Elm Street"),
        ("Austin", "Congress Avenue"),
        ("Phoenix", "Camelback Road"),
        ("Houston", "Westheimer Road"),
        ("San Antonio", "Commerce Street"),
        ("Albuquerque", "Central Avenue"),
    ],
    "West": [
        ("Los Angeles", "Sunset Boulevard"),
        ("San Diego", "Gaslamp Quarter"),
        ("Seattle", "Pine Street"),
        ("Portland", "NW 23rd Avenue"),
        ("San Francisco", "Market Street"),
        ("Las Vegas", "Las Vegas Boulevard"),
    ],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate compact use-case dataset.")
    parser.add_argument("--output-dir", default="data/generated/usecases_demo_small")
    parser.add_argument("--seed", type=int, default=20260319)
    parser.add_argument("--styles", type=int, default=300)
    parser.add_argument("--skus", type=int, default=2400)
    parser.add_argument("--stores", type=int, default=120)
    parser.add_argument("--customers", type=int, default=2000)
    parser.add_argument("--season", default="Q4-2025")
    return parser.parse_args()


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def build_store_locations(store_count: int) -> list[tuple[int, str, str]]:
    stores: list[tuple[int, str, str]] = []
    for store_id in range(1, store_count + 1):
        region = REGIONS[(store_id - 1) % len(REGIONS)]
        city_streets = REGION_CITY_STREET[region]
        city, street = city_streets[(store_id - 1) % len(city_streets)]
        store_name = f"Store-{store_id:03d} ({region}) - {city}, {street}"
        stores.append((store_id, store_name, region))

    # Keep this exact example stable for demo prompts.
    if store_count >= 56:
        stores[55] = (56, "Store-056 (Northeast) - Boston, Boylston Street", "Northeast")
    return stores


def write_styles(output: Path, rng: random.Random, style_count: int, season: str) -> list[str]:
    path = output / "styles.csv"
    style_ids: list[str] = []
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "style_id",
                "style_name",
                "category",
                "season",
                "planned_cc_count",
                "core_vs_fashion",
                "strategic_priority",
            ]
        )
        for i in range(1, style_count + 1):
            style_id = f"STY-{i:04d}"
            category = rng.choice(CATEGORIES)
            core_vs_fashion = rng.choices(["core", "fashion"], weights=[0.62, 0.38], k=1)[0]
            strategic_priority = rng.choices(["maintain", "grow", "optimize"], weights=[0.35, 0.45, 0.20], k=1)[0]
            planned_cc_count = rng.randint(3, 12)
            writer.writerow(
                [
                    style_id,
                    f"{category} Style {i:04d}",
                    category,
                    season,
                    planned_cc_count,
                    core_vs_fashion,
                    strategic_priority,
                ]
            )
            style_ids.append(style_id)
    return style_ids


def write_skus(output: Path, rng: random.Random, sku_count: int, style_ids: list[str]) -> list[tuple[str, str]]:
    path = output / "skus.csv"
    skus: list[tuple[str, str]] = []
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "sku",
                "style_id",
                "color_name",
                "size",
                "msrp",
                "cost",
                "substitute_style_id",
                "trade_up_style_id",
            ]
        )

        for i in range(1, sku_count + 1):
            style_id = rng.choice(style_ids)
            substitute_style_id = rng.choice(style_ids)
            trade_up_style_id = rng.choice(style_ids)
            msrp = round(rng.uniform(24, 220), 2)
            cost = round(msrp * rng.uniform(0.34, 0.58), 2)
            sku = f"SKU-{i:06d}"
            writer.writerow(
                [
                    sku,
                    style_id,
                    rng.choice(COLORS),
                    rng.choice(SIZES),
                    f"{msrp:.2f}",
                    f"{cost:.2f}",
                    substitute_style_id if substitute_style_id != style_id else "",
                    trade_up_style_id if trade_up_style_id != style_id else "",
                ]
            )
            skus.append((sku, style_id))
    return skus


def write_inventory(output: Path, rng: random.Random, skus: list[tuple[str, str]], store_count: int) -> None:
    path = output / "inventory.csv"
    stores = build_store_locations(store_count)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "store_id",
                "store_name",
                "region",
                "sku",
                "on_hand_units",
                "available_for_transfer",
                "available_online_dc",
            ]
        )
        for sku, _style_id in skus:
            for store_id, store_name, region in rng.sample(stores, k=min(12, len(stores))):
                on_hand = max(0, int(rng.gauss(14, 9)))
                writer.writerow(
                    [
                        store_id,
                        store_name,
                        region,
                        sku,
                        on_hand,
                        "true" if on_hand > 3 else "false",
                        max(0, int(rng.gauss(48, 20))),
                    ]
                )


def write_sales_summary(output: Path, rng: random.Random, skus: list[tuple[str, str]]) -> None:
    path = output / "sales_summary.csv"
    periods = ["2025-10", "2025-11", "2025-12"]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "period",
                "sku",
                "style_id",
                "units_sold",
                "net_sales",
                "gross_margin_pct",
                "sell_through_pct",
                "markdown_rate",
                "return_rate",
                "store_count",
            ]
        )
        for period in periods:
            for sku, style_id in skus:
                units_sold = max(0, int(rng.gauss(26, 14)))
                avg_price = rng.uniform(28, 175)
                net_sales = round(units_sold * avg_price * rng.uniform(0.83, 0.98), 2)
                gross_margin_pct = round(rng.uniform(38, 68), 2)
                sell_through_pct = round(rng.uniform(22, 93), 2)
                markdown_rate = round(rng.uniform(2, 34), 2)
                return_rate = round(rng.uniform(1, 19), 2)
                store_count = rng.randint(9, 96)
                writer.writerow(
                    [
                        period,
                        sku,
                        style_id,
                        units_sold,
                        f"{net_sales:.2f}",
                        f"{gross_margin_pct:.2f}",
                        f"{sell_through_pct:.2f}",
                        f"{markdown_rate:.2f}",
                        f"{return_rate:.2f}",
                        store_count,
                    ]
                )


def write_customer_profiles(output: Path, rng: random.Random, customer_count: int, skus: list[tuple[str, str]]) -> None:
    path = output / "customer_profiles.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "customer_id",
                "name",
                "tier",
                "preferred_sizes",
                "preferred_colors",
                "favorite_categories",
                "recent_purchases",
            ]
        )
        for customer_id in range(1, customer_count + 1):
            first = rng.choice(["Leah", "Mason", "Ava", "Olivia", "Noah", "Ethan", "Sofia", "Liam", "Aria"])
            last = rng.choice(["Grubb", "Smith", "Johnson", "Carter", "Patel", "Nguyen", "Martinez", "Brown"])
            if customer_id == 1:
                first, last = "Leah", "Grubb"

            recent = [{"sku": rng.choice(skus)[0], "qty": rng.randint(1, 2)} for _ in range(rng.randint(2, 5))]
            writer.writerow(
                [
                    customer_id,
                    f"{first} {last}",
                    rng.choices(TIERS, weights=[0.45, 0.32, 0.18, 0.05], k=1)[0],
                    "{" + ",".join(rng.sample(SIZES, k=3)) + "}",
                    "{" + ",".join(rng.sample(COLORS, k=3)) + "}",
                    "{" + ",".join(rng.sample(CATEGORIES, k=2)) + "}",
                    json.dumps(recent),
                ]
            )


def main() -> None:
    args = parse_args()
    rng = random.Random(args.seed)
    output = Path(args.output_dir).resolve()
    ensure_dir(output)

    style_ids = write_styles(output, rng, args.styles, args.season)
    skus = write_skus(output, rng, args.skus, style_ids)
    write_inventory(output, rng, skus, args.stores)
    write_sales_summary(output, rng, skus)
    write_customer_profiles(output, rng, args.customers, skus)
    print(f"Generated use-case dataset in {output}")


if __name__ == "__main__":
    main()
