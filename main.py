import argparse
import os
import sys
from pathlib import Path

from staticjinja.staticjinja import Site


def get_context() -> dict[str, str]:
    """Берет контекст для шаблонов из переменных окружения."""
    context = {}
    prefix = "SJP_"
    for key in os.environ.keys():
        if key.startswith(prefix):
            context[key.removeprefix(prefix).lower()] = os.environ[key]
    return context


def parse_args() -> argparse.Namespace:
    """Парсер аргументов"""
    parser = argparse.ArgumentParser(
        description="Render HTML pages from Jinja templates",
    )
    parser.add_argument(
        "-w",
        "--watch",
        help="Render the site, and re-render on changes to <srcpath>",
        action="store_true",
    )
    parser.add_argument(
        "--srcpath",
        help="The directory to look in for templates (defaults to './templates')",
        default=Path(".") / "templates",
        type=Path,
    )
    parser.add_argument(
        "--outpath",
        help="The directory to place rendered files in (defaults to './build')",
        default=Path(".") / "build",
        type=Path,
    )
    return parser.parse_args()


def find_unreadable_files(html_files: list[Path]) -> list[str]:
    """Возвращает список путей к файлам, которые не удалось открыть."""
    unreadable = []
    for file in html_files:
        try:
            with open(file, "r", encoding="utf-8"):
                pass
        except PermissionError:
            unreadable.append(str(file))
    return unreadable


def main() -> None:

    args = parse_args()

    src_path = args.srcpath

    try:
        with os.scandir(src_path) as it:
            next(it, None)
    except PermissionError:
        raise PermissionError(
            f"{src_path} is not readable (permission denied)"
        ) from None
    except NotADirectoryError:
        raise ValueError(
            f"{src_path} is not a directory for rendering",
        ) from None
    except FileNotFoundError:
        raise ValueError(f"{src_path} does not exist") from None

    html_files = list(src_path.glob("*.html"))
    if not html_files:
        raise ValueError(f"{src_path} does not contain any HTML files")

    unreadable_files = find_unreadable_files(html_files)
    if unreadable_files:
        files = "\n  ".join(unreadable_files)
        raise PermissionError(
            f"The following template files are not readable:\n  {files}"
        )

    output_path = args.outpath
    static_path = Path(src_path) / "assets"

    site = Site.make_site(
        searchpath=src_path,
        outpath=output_path,
        staticpaths=[
            str(static_path),
        ],
        contexts=[(".*.html", get_context)],
    )

    site.render(use_reloader=args.watch)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, PermissionError, NotADirectoryError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
