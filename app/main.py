from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.traceback import install

from app.agents.orchestrator import LeaveOrchestrator

# Enable beautiful tracebacks automatically
install(show_locals=True)

console = Console()


def main():

    console.print()

    console.print(
        Panel.fit(
            "[bold cyan]🤖 Leave Management Assistant[/bold cyan]\n\n"
            "[white]AI-Powered Multi-Agent Leave Management System[/white]\n\n"
            "[bold green]Available Services[/bold green]\n"
            "• Apply Leave\n"
            "• Leave Balance\n"
            "• Leave Policy\n"
            "• Holiday Calendar\n"
            "• Leave Planning\n"
            "• Employee Information\n\n"
            "[yellow]Type 'exit' anytime to quit.[/yellow]",
            border_style="cyan",
            title="[bold]WELCOME[/bold]",
        )
    )

    orchestrator = LeaveOrchestrator()

    while True:

        console.print()

        query = console.input(
            "[bold green]👤 You[/bold green] [cyan]>[/cyan] "
        ).strip()

        if query.lower() == "exit":

            console.print()

            console.print(
                Panel.fit(
                    "[bold green]👋 Thank you for using Leave Management Assistant![/bold green]\n\n"
                    "Have a great day.",
                    border_style="green",
                )
            )

            break

        console.print()

        console.print(
            Rule(
                "[bold cyan]🤖 Assistant[/bold cyan]",
                style="cyan",
            )
        )

        try:

            response = orchestrator.run(query)

            console.print(
                Panel(
                    response,
                    border_style="cyan",
                    title="🤖 Assistant",
                )
            )


        except KeyboardInterrupt:

            console.print(
                "\n[bold red]Operation cancelled by user.[/bold red]"
            )

            break

        except Exception as e:

            console.print()

            console.print(
                Panel.fit(
                    f"[bold red]❌ Unexpected Error[/bold red]\n\n{e}",
                    border_style="red",
                )
            )

            raise

        console.print()

        console.print(
            Rule(style="grey50")
        )


if __name__ == "__main__":

    main()