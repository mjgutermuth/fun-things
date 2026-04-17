#!/usr/bin/env python3
import asyncio
import json
import sys
from pathlib import Path

import genshin
from rich.console import Console
from rich.table import Table
from rich import box
from rich.text import Text
from rich.panel import Panel

CONFIG_PATH = Path(__file__).parent / "config.json"
ELEMENT_COLORS = {
    "Pyro":     "bold red",
    "Hydro":    "bold blue",
    "Anemo":    "bold green",
    "Electro":  "bold magenta",
    "Dendro":   "bold green",
    "Cryo":     "bold cyan",
    "Geo":      "bold yellow",
}

console = Console()


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        console.print(
            f"[red]config.json not found.[/red] Copy [bold]config.example.json[/bold] to "
            f"[bold]config.json[/bold] and fill in your cookies + UID.\n"
            f"See [bold]README[/bold] for how to get your cookies."
        )
        sys.exit(1)
    with open(CONFIG_PATH) as f:
        return json.load(f)


def element_style(element: str) -> str:
    return ELEMENT_COLORS.get(element, "white")


def rarity_stars(rarity: int) -> str:
    return "★" * rarity


def build_table(characters: list) -> Table:
    table = Table(
        title="Genshin Impact — Character Roster",
        box=box.ROUNDED,
        show_lines=True,
        header_style="bold white on dark_blue",
        title_style="bold yellow",
    )

    table.add_column("Name", style="bold white", min_width=18)
    table.add_column("Element", min_width=9)
    table.add_column("Rarity", justify="center", min_width=7)
    table.add_column("Level", justify="center", min_width=7)
    table.add_column("Const.", justify="center", min_width=7)
    table.add_column("Friendship", justify="center", min_width=10)
    table.add_column("Weapon", min_width=20)
    table.add_column("Wpn Lv.", justify="center", min_width=7)
    table.add_column("Wpn Ref.", justify="center", min_width=8)

    for char in sorted(characters, key=lambda c: (-c.rarity, -c.level, c.name)):
        elem_style = element_style(char.element)
        table.add_row(
            char.name,
            Text(char.element, style=elem_style),
            Text(rarity_stars(char.rarity), style="yellow" if char.rarity == 5 else "bright_white"),
            f"{char.level}/{char.max_level}",
            f"C{char.constellation}",
            f"Lv.{char.friendship}",
            char.weapon.name if char.weapon else "—",
            f"{char.weapon.level}/{char.weapon.max_level}" if char.weapon else "—",
            f"R{char.weapon.refinement}" if char.weapon else "—",
        )

    return table


async def fetch_and_display():
    config = load_config()

    missing = [k for k in ("ltuid_v2", "ltoken_v2", "uid") if not config.get(k)]
    if missing:
        console.print(f"[red]Missing fields in config.json:[/red] {', '.join(missing)}")
        sys.exit(1)

    cookies = {
        "ltuid_v2": config["ltuid_v2"],
        "ltoken_v2": config["ltoken_v2"],
    }
    uid = int(config["uid"])

    client = genshin.Client(cookies, game=genshin.Game.GENSHIN)

    with console.status("[bold cyan]Fetching character roster from HoYoLAB...[/bold cyan]"):
        try:
            characters = await client.get_genshin_characters(uid)
        except genshin.errors.InvalidCookies:
            console.print("[red]Invalid or expired cookies.[/red] Re-copy your ltuid_v2 / ltoken_v2 from hoyolab.com.")
            sys.exit(1)
        except genshin.errors.GenshinException as e:
            console.print(f"[red]HoYoLAB API error:[/red] {e}")
            sys.exit(1)

    table = build_table(characters)
    console.print()
    console.print(table)
    console.print(
        Panel(
            f"[bold]{len(characters)}[/bold] characters fetched  •  UID [bold]{uid}[/bold]",
            style="dim",
            expand=False,
        )
    )


def main():
    asyncio.run(fetch_and_display())


if __name__ == "__main__":
    main()
