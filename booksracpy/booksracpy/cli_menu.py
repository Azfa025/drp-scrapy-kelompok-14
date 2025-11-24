"""Interactive terminal menu for analyzing scraped book data.

This CLI uses the functions from `booksracpy.analyze_books` to allow the user
to pick one of the four analyses interactively.
"""
from __future__ import annotations

import sys
from typing import Optional

from analyze_books import (
    load_items,
    count_books_in_category,
    average_price_all,
    average_price_in_category,
    count_books_in_price_range,
)


def ask(prompt: str, default: Optional[str] = None) -> str:
    if default is None:
        return input(prompt)
    val = input(f"{prompt} [{default}]: ")
    return val.strip() or default


def choose_file() -> list:
    while True:
        path = input('Path to scraped file (json/jsonl/jl/csv): ').strip()
        if not path:
            print('Please provide a file path.')
            continue
        try:
            items = load_items(path)
            print(f'Loaded {len(items)} items from {path}')
            return items
        except Exception as e:
            print(f'Error loading file: {e}')


def run_menu():
    print('Books analysis — interactive menu')
    items = choose_file()

    while True:
        print('\nSelect action:')
        print('  1) Count books in a category')
        print('  2) Average price (all books)')
        print('  3) Average price in a category')
        print('  4) Count books in a price range')
        print('  5) Reload file')
        print('  0) Exit')

        choice = input('Choice: ').strip()
        if choice == '0':
            print('Goodbye')
            return

        if choice == '1':
            cat = input('Category name: ').strip()
            if not cat:
                print('Category cannot be empty')
                continue
            n = count_books_in_category(items, cat)
            print(f"Count books in category '{cat}': {n}")

        elif choice == '2':
            price_field = ask('Price field name', 'price')
            avg = average_price_all(items, price_field=price_field)
            if avg is None:
                print('No valid prices found to compute average')
            else:
                print(f'Average price (all books) using field "{price_field}": £{avg:.2f}')

        elif choice == '3':
            cat = input('Category name: ').strip()
            if not cat:
                print('Category cannot be empty')
                continue
            price_field = ask('Price field name', 'price')
            avg = average_price_in_category(items, cat, price_field=price_field)
            if avg is None:
                print(f"No valid prices found in category '{cat}'")
            else:
                print(f"Average price in category '{cat}' using field '{price_field}': £{avg:.2f}")

        elif choice == '4':
            mn = input('Minimum price (e.g. 5): ').strip()
            mx = input('Maximum price (e.g. 20): ').strip()
            try:
                mnf = float(mn)
                mxf = float(mx)
            except ValueError:
                print('Please enter numeric values for min and max')
                continue
            price_field = ask('Price field name', 'price')
            n = count_books_in_price_range(items, mnf, mxf, price_field=price_field)
            print(f'Count books in range £{mnf:.2f} - £{mxf:.2f} (field "{price_field}"): {n}')

        elif choice == '5':
            items = choose_file()

        else:
            print('Unknown choice — enter a number from the menu')


def main() -> None:
    try:
        run_menu()
    except KeyboardInterrupt:
        print('\nInterrupted — exiting')
        sys.exit(0)


if __name__ == '__main__':
    main()
