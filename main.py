import argparse
from lefdef.lefdef import Tech, Design

GRAY = "\033[0;30m"
CYAN = "\033[0;36m"
RED = "\033[1;31m"
BLUE = "\033[0;34m"
YELLOW = "\033[0;33m"
GREEN = "\033[1;32m"
ENDCOLOR = "\033[0m"


def main():
    parser = argparse.ArgumentParser(
        prog="place",
        description="places the components in a def file given a def and library of macros",
        epilog=f"enjoy the script {RED}<3{ENDCOLOR}",
    )

    parser.add_argument(
        "-l", "--lef_path", help="lef file for macros used", required=True
    )
    parser.add_argument(
        "-d", "--def_path", help="the def with a placement to optimize", required=True
    )

    args = parser.parse_args()

    tech = Tech(args.lef_path)
    design = Design(args.def_path)

    print(tech.macros, design.nets)


if __name__ == "__main__":
    main()
