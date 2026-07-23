from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def main() -> None:
    console.print(Panel("Rich makes terminals beautiful", title="rich"))

    table = Table(title="Books")
    table.add_column("Title", style="cyan")
    table.add_column("Author", style="magenta")
    table.add_column("Year", justify="right", style="green")
    table.add_row("Clean Code", "Robert Martin", "2008")
    table.add_row("Refactoring", "Martin Fowler", "1999")
    table.add_row("The Pragmatic Programmer", "Andy Hunt", "1999")
    console.print(table)

    console.print("[bold red]error[/] [green]success[/] [yellow]warning[/]")
    console.rule("done")


if __name__ == "__main__":
    main()
