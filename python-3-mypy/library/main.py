from library import service, stats
from library.db import make_engine, make_session_factory
from library.schemas import BookIn

SEED = [
    BookIn(title="Fluent Python", pages=1014, price=59.9, author="Luciano Ramalho"),
    BookIn(title="Robust Python", pages=380, price=44.5, author="Patrick Viafore"),
    BookIn(
        title="Architecture Patterns with Python", pages=304, price=39.0, author="Harry Percival"
    ),
]


def compiled(module_file: str | None) -> bool:
    return module_file is not None and not module_file.endswith(".py")


def main() -> None:
    session_factory = make_session_factory(make_engine())
    with session_factory() as session:
        if not service.list_books(session):
            for book in SEED:
                service.add_book(session, book)
        for out in service.list_books(session):
            print(out.model_dump_json())
        print(service.library_stats(session).model_dump_json())
    print(f"service compiled by mypyc: {compiled(service.__file__)}")
    print(f"stats compiled by mypyc: {compiled(stats.__file__)}")


if __name__ == "__main__":
    main()
