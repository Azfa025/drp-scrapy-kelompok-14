"""Simple analysis utilities for scraped book data.

Usage examples (PowerShell):

  # Average price for all books from JSON Lines file
  python .\booksracpy\analyze_books.py .\books.jl --avg-all

  # Count books in category 'Travel'
  python .\booksracpy\analyze_books.py .\books.json --count-category Travel

  # Average price in category 'Mystery'
  python .\booksracpy\analyze_books.py .\books.csv --avg-category Mystery

  # Count books in price range £10 to £20
  python .\booksracpy\analyze_books.py .\books.json --count-range 10 20

The script accepts JSON, JSONL (.jl) or CSV where price fields are either numbers
or strings like '£51.77'. It attempts to robustly parse price strings.
"""
from __future__ import annotations

import argparse
import csv
import json
from typing import Any, Dict, Iterable, List, Optional


def load_items(path: str) -> List[Dict[str, Any]]:
    path = path.replace('"', '')
    if path.lower().endswith('.csv'):
        with open(path, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return [dict(row) for row in reader]
    elif path.lower().endswith('.jl'):
        items = []
        with open(path, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                items.append(json.loads(line))
        return items
    else:
        # assume json array
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            raise ValueError('JSON file does not contain a list of items')


def normalize_price(value: Any) -> Optional[float]:
    """Try to extract float price from various input formats.

    Returns None if price cannot be parsed.
    """
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        s = value.strip()
        # handle tuple-like values sometimes created by stray commas in spider
        if s.startswith('(') and s.endswith(')'):
            s = s[1:-1].strip()
        # remove currency symbol and any non-digit except dot and comma
        # replace comma as thousand separator
        s = s.replace('£', '').replace(',', '').strip()
        # sometimes array-like string ("['£51.77']")
        if s.startswith("[") and s.endswith("]"):
            try:
                parsed = json.loads(s)
                if parsed:
                    return normalize_price(parsed[0])
            except Exception:
                pass
        try:
            return float(s)
        except Exception:
            return None
    # unknown type
    return None


def count_books_in_category(items: Iterable[Dict[str, Any]], category: str) -> int:
    cat = category.strip().lower()
    count = 0
    for it in items:
        c = it.get('category') or it.get('Category') or it.get('category_name')
        if c is None:
            continue
        if isinstance(c, (list, tuple)):
            c = c[0]
        if isinstance(c, str) and c.strip().lower() == cat:
            count += 1
    return count


def average_price_all(items: Iterable[Dict[str, Any]], price_field: str = 'price') -> Optional[float]:
    prices: List[float] = []
    for it in items:
        p = normalize_price(it.get(price_field))
        if p is not None:
            prices.append(p)
    if not prices:
        return None
    return sum(prices) / len(prices)


def average_price_in_category(items: Iterable[Dict[str, Any]], category: str, price_field: str = 'price') -> Optional[float]:
    cat = category.strip().lower()
    prices: List[float] = []
    for it in items:
        c = it.get('category') or it.get('Category')
        if c is None:
            continue
        if isinstance(c, (list, tuple)):
            c = c[0]
        if isinstance(c, str) and c.strip().lower() == cat:
            p = normalize_price(it.get(price_field))
            if p is not None:
                prices.append(p)
    if not prices:
        return None
    return sum(prices) / len(prices)


def count_books_in_price_range(items: Iterable[Dict[str, Any]], min_price: float, max_price: float, price_field: str = 'price') -> int:
    if min_price > max_price:
        min_price, max_price = max_price, min_price
    count = 0
    for it in items:
        p = normalize_price(it.get(price_field))
        if p is None:
            continue
        if min_price <= p <= max_price:
            count += 1
    return count


def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description='Analyze scraped book data (JSON/JSONL/CSV)')
    ap.add_argument('input', help='Path to input file (json, jl, csv)')
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument('--count-category', metavar='CATEGORY', help='Count number of books in CATEGORY')
    group.add_argument('--avg-all', action='store_true', help='Average price of all books')
    group.add_argument('--avg-category', metavar='CATEGORY', help='Average price of books in CATEGORY')
    group.add_argument('--count-range', nargs=2, metavar=('MIN', 'MAX'), help='Count books with price between MIN and MAX')
    ap.add_argument('--price-field', default='price', help='Field name for price (default: price)')
    return ap.parse_args()


def main() -> None:
    args = _parse_args()
    items = load_items(args.input)

    if args.count_category:
        n = count_books_in_category(items, args.count_category)
        print(f"Count books in category '{args.count_category}': {n}")
        return

    if args.avg_all:
        avg = average_price_all(items, price_field=args.price_field)
        if avg is None:
            print('No prices found to compute average')
        else:
            print(f'Average price (all books): £{avg:.2f}')
        return

    if args.avg_category:
        avg = average_price_in_category(items, args.avg_category, price_field=args.price_field)
        if avg is None:
            print(f"No prices found in category '{args.avg_category}'")
        else:
            print(f"Average price in category '{args.avg_category}': £{avg:.2f}")
        return

    if args.count_range:
        try:
            mn = float(args.count_range[0])
            mx = float(args.count_range[1])
        except ValueError:
            print('MIN and MAX must be numeric')
            return
        n = count_books_in_price_range(items, mn, mx, price_field=args.price_field)
        print(f'Count books in range £{mn:.2f} - £{mx:.2f}: {n}')
        return


if __name__ == '__main__':
    main()
