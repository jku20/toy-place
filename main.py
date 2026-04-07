from random import randint
import argparse
from lefdef import Tech, Design, CompFixed, Component
from math import exp

GRAY = "\033[0;30m"
CYAN = "\033[0;36m"
RED = "\033[1;31m"
BLUE = "\033[0;34m"
YELLOW = "\033[0;33m"
GREEN = "\033[1;32m"
ENDCOLOR = "\033[0m"

ONE_OVER_GAMMA = 0.5

Placement = dict[str, tuple[float, float]]


def wl_cost(placement: Placement, design: Design, tech: Tech) -> float:
    cost = 0.0
    for net in design.nets:
        max_num = [0, 0]
        max_den = [0, 0]
        min_num = [0, 0]
        min_den = [0, 0]
        for pin in net.pins:
            pin_pos = design.pin_midpoint(pin)
            for i in range(2):
                p = pin_pos[i]
                max_num[i] += p * exp(ONE_OVER_GAMMA * p)
                max_den[i] += exp(ONE_OVER_GAMMA * p)
                min_num[i] += p * exp(-ONE_OVER_GAMMA * p)
                min_den[i] += exp(-ONE_OVER_GAMMA * p)
        for i in range(2):
            cost += max_num[i] / max_den[i] - min_num[i] / min_den[i]
    return cost


def global_place(design: Design, tech: Tech) -> dict[str, tuple[float, float]]:
    fixed: list[Component] = []
    unfixed: list[Component] = []
    for comp in design.comps.values():
        if isinstance(comp.ty, CompFixed):
            fixed.append(comp)
        else:
            unfixed.append(comp)

    placement = {}
    for comp in fixed:
        if isinstance(comp.ty, CompFixed):
            placement[comp.comp_name] = comp.ty.pt
        else:
            raise Exception("Every comp here should be Fixed")

    for comp in unfixed:
        x = randint(0, design.x_gcell_grid.num_tracks - 1)
        y = randint(0, design.y_gcell_grid.num_tracks - 1)
        placement[comp.comp_name] = (x, y)

    print(f"random placement cost: {wl_cost(placement, design, tech)}")

    return placement


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
    design = Design(args.def_path, tech)

    _ = global_place(design, tech)


if __name__ == "__main__":
    main()
