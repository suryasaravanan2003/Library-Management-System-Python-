#!/usr/bin/env python3
"""
Library Book Inventory Manager (CLI)
- Save/load records to JSON (library.json)
- Add / Search / Issue / Return / List / Reports
- Book: id (unique), title, author, total_copies, issued_count
- Library handles lookup using dicts for fast access
"""
import json
import os
from dataclasses import dataclass, asdict
from typing import Dict, Optional, List

DATA_FILE = "library.json"


@dataclass
class Book:
    book_id: str
    title: str
    author: str
    total_copies: int
    issued_count: int = 0

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(d):
        return Book(
            book_id=d["book_id"],
            title=d["title"],
            author=d["author"],
            total_copies=int(d.get("total_copies", 1)),
            issued_count=int(d.get("issued_count", 0))
        )

    @property
    def available(self):
        return self.total_copies - self.issued_count


class Library:
    def __init__(self, data_file: str = DATA_FILE):
        self.data_file = data_file
        self.books: Dict[str, Book] = {}  # keyed by book_id
        self.load()

    def load(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for bid, bdict in data.items():
                    self.books[bid] = Book.from_dict(bdict)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: failed to read data file ({e}). Starting empty library.")
                self.books = {}
        else:
            self.books = {}

    def save(self):
        try:
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump({bid: b.to_dict() for bid, b in self.books.items()}, f, indent=2)
        except IOError as e:
            print(f"Error saving library: {e}")

    def add_book(self, book: Book) -> bool:
        bid = book.book_id.strip()
        if not bid:
            print("Error: Book ID cannot be empty.")
            return False
        if bid in self.books:
            print(f"Error: Book ID '{bid}' exists. Use update to change copies.")
            return False
        self.books[bid] = book
        self.save()
        return True

    def update_book_copies(self, book_id: str, new_total: int) -> bool:
        bid = book_id.strip()
        if bid not in self.books:
            print(f"Error: Book ID '{bid}' not found.")
            return False
        book = self.books[bid]
        if new_total < book.issued_count:
            print("Error: new total copies cannot be less than currently issued copies.")
            return False
        book.total_copies = new_total
        self.save()
        return True

    def find_by_id(self, book_id: str) -> Optional[Book]:
        return self.books.get(book_id.strip())

    def search(self, keyword: str) -> List[Book]:
        kw = keyword.lower().strip()
        results = []
        for b in self.books.values():
            if kw in b.title.lower() or kw in b.author.lower():
                results.append(b)
        return results

    def issue_book(self, book_id: str) -> bool:
        b = self.find_by_id(book_id)
        if not b:
            print("Book not found.")
            return False
        if b.available <= 0:
            print("No copies available to issue.")
            return False
        b.issued_count += 1
        self.save()
        return True

    def return_book(self, book_id: str) -> bool:
        b = self.find_by_id(book_id)
        if not b:
            print("Book not found.")
            return False
        if b.issued_count <= 0:
            print("No issued copies to return.")
            return False
        b.issued_count -= 1
        self.save()
        return True

    def list_books(self):
        if not self.books:
            print("Library is empty.")
            return
        rows = []
        for bid, b in sorted(self.books.items(), key=lambda x: x[0]):
            rows.append((b.book_id, b.title, b.author, str(b.total_copies), str(b.issued_count), str(b.available)))
        print_table(["ID", "Title", "Author", "Total", "Issued", "Available"], rows)

    def report(self):
        total_books = sum(b.total_copies for b in self.books.values())
        total_issued = sum(b.issued_count for b in self.books.values())
        unique_titles = len(self.books)
        print("Library Report")
        print("--------------")
        print(f"Unique titles : {unique_titles}")
        print(f"Total copies  : {total_books}")
        print(f"Issued copies : {total_issued}")
        print(f"Available now : {total_books - total_issued}")
        # Top 5 most issued
        top = sorted(self.books.values(), key=lambda x: x.issued_count, reverse=True)[:5]
        if top:
            print("\nTop issued books:")
            for b in top:
                print(f"- {b.title} (issued: {b.issued_count})")


def print_table(headers, rows):
    cols = len(headers)
    widths = [len(str(h)) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))
    sep = " | "
    header_line = sep.join(str(h).ljust(widths[i]) for i, h in enumerate(headers))
    divider = "-+-".join("-" * widths[i] for i in range(cols))
    print(header_line)
    print(divider)
    for row in rows:
        print(sep.join(str(cell).ljust(widths[i]) for i, cell in enumerate(row)))


def prompt_int(prompt_text: str, default: Optional[int] = None) -> int:
    while True:
        v = input(prompt_text).strip()
        if not v and default is not None:
            return default
        try:
            n = int(v)
            return n
        except ValueError:
            print("Please enter a valid integer.")


def main_menu():
    print("""
Library Book Inventory Manager
------------------------------
1. Add book
2. Update book copies
3. Search books (title/author)
4. Issue book
5. Return book
6. List all books
7. Report
8. Exit
""")


def main():
    lib = Library()
    while True:
        main_menu()
        choice = input("Choose (1-8): ").strip()
        if choice == "1":
            print("\nAdd Book")
            bid = input("Book ID (unique): ").strip()
            title = input("Title: ").strip()
            author = input("Author: ").strip()
            total = prompt_int("Total copies: ", default=1)
            if not bid or not title:
                print("Book ID and Title required.")
                continue
            book = Book(book_id=bid, title=title, author=author, total_copies=total)
            if lib.add_book(book):
                print("Book added.\n")
        elif choice == "2":
            print("\nUpdate Book Copies")
            bid = input("Book ID: ").strip()
            if not bid:
                print("Book ID required.")
                continue
            book = lib.find_by_id(bid)
            if not book:
                print("Book not found.")
                continue
            print(f"Current total copies: {book.total_copies}, issued: {book.issued_count}")
            new_total = prompt_int("New total copies: ")
            if lib.update_book_copies(bid, new_total):
                print("Updated.\n")
        elif choice == "3":
            kw = input("Search keyword (title/author): ").strip()
            if not kw:
                print("Enter search keyword.")
                continue
            results = lib.search(kw)
            if not results:
                print("No results.\n")
            else:
                rows = [(b.book_id, b.title, b.author, str(b.total_copies), str(b.issued_count), str(b.available)) for b in results]
                print_table(["ID", "Title", "Author", "Total", "Issued", "Available"], rows)
                print()
        elif choice == "4":
            bid = input("Book ID to issue: ").strip()
            if lib.issue_book(bid):
                print("Book issued.\n")
        elif choice == "5":
            bid = input("Book ID to return: ").strip()
            if lib.return_book(bid):
                print("Book returned.\n")
        elif choice == "6":
            print("\nAll Books")
            lib.list_books()
            print()
        elif choice == "7":
            lib.report()
            print()
        elif choice == "8":
            print("Exiting.")
            break
        else:
            print("Invalid option.\n")


if __name__ == "__main__":
    main()
