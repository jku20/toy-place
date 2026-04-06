from enum import Enum
from io import TextIOWrapper
import argparse
from dataclasses import dataclass

GRAY = "\033[0;30m"
CYAN = "\033[0;36m"
RED = "\033[1;31m"
BLUE = "\033[0;34m"
YELLOW = "\033[0;33m"
GREEN = "\033[1;32m"
ENDCOLOR = "\033[0m"


@dataclass
class Rect:
    bot_left: tuple[float, float]
    top_right: tuple[float, float]


@dataclass
class Units:
    database_microns: float


@dataclass
class Masterslice:
    pass


@dataclass
class Cut:
    pass


class OriDir(Enum):
    H = 1
    V = 2


@dataclass
class Routing:
    pitch: float
    width: float
    spacing: float
    direction: OriDir


@dataclass
class Overlap:
    pass


LayerTy = Cut | Masterslice | Routing | Overlap


@dataclass
class Layer:
    name: str
    ty: LayerTy


def parse_box(fin: TextIOWrapper) -> Rect:
    return Rect((0, 0), (0, 0))


def parse_units(fin: TextIOWrapper) -> Units:
    units = Units(0)
    line = fin.readline().strip()
    toks = line.split()
    while toks[0] != "END":
        if toks[0] == "DATABASE" and toks[1] == "MICRONS":
            units.database_microns = float(toks[2])
        line = fin.readline().strip()
        toks = line.split()
    return units


def parse_layer(fin: TextIOWrapper, name: str) -> Layer:
    line = fin.readline().strip()
    toks = line.split()
    if toks[0] != "TYPE":
        raise Exception("Expected TYPE")

    if toks[1] == "MASTERSLICE":
        return Layer(name, Masterslice())
    elif toks[1] == "CUT":
        return Layer(name, Cut())
    elif toks[1] == "OVERLAP":
        return Layer(name, Overlap())
    elif toks[1] == "ROUTING":
        d = {}
        for i in range(4):
            toks = fin.readline().strip().split()
            d[toks[0]] = toks[1]
        dir = OriDir.H
        if d["DIRECTION"] == "VERTICAL":
            dir = OriDir.V
        return Layer(
            name,
            Routing(float(d["PITCH"]), float(d["WIDTH"]), float(d["SPACING"]), dir),
        )
    else:
        raise Exception(f"Unknown Layer type {toks[1]}")


@dataclass
class Via:
    name: str
    layers: dict[Layer, Rect]


def parse_via(fin: TextIOWrapper, name: str) -> Via:
    toks = fin.readline().strip().split()
    layers = {}
    while toks[0] != "END":
        layer_name = toks[1]
        toks = fin.readline().strip().split()
        rect = Rect((float(toks[1]), float(toks[2])), (float(toks[3]), float(toks[4])))
        layers[layer_name] = rect
        toks = fin.readline().strip().split()
    return Via(name, layers)


@dataclass
class Spacing:
    l1: str
    l2: str
    dist: float


def parse_spacing(fin: TextIOWrapper) -> list[Spacing]:
    toks = fin.readline().strip().split()
    spacings = []
    while toks[0] != "END":
        if toks[0] == "SAMENET":
            name1, name2, size = toks[1], toks[2], float(toks[3])
            spacings.append(Spacing(name1, name2, size))
        else:
            raise Exception("Expected SAMENET")
        toks = fin.readline().strip().split()
    return spacings


class SiteClass(Enum):
    PAD = 1
    CORE = 2


class Symmetry(Enum):
    X = 1
    Y = 2
    R90 = 3


@dataclass
class Site:
    name: str
    width: float
    height: float
    site_class: SiteClass
    symmetry: Symmetry


def parse_site(fin: TextIOWrapper, name: str) -> Site:
    toks = fin.readline().strip().split()

    width = None
    height = None
    site_class = None
    sym = None
    while toks[0] != "END":
        if toks[0] == "SIZE":
            width = float(toks[1])
            height = float(toks[3])
        elif toks[0] == "CLASS":
            if toks[1] == "CORE":
                site_class = SiteClass.CORE
            elif toks[1] == "PAD":
                site_class = SiteClass.PAD
            else:
                raise Exception(f"Expected site class, PAD or CORE, got {toks[1]}")
        elif toks[0] == "SYMMETRY":
            if toks[1] == "Y":
                sym = Symmetry.Y
            elif toks[1] == "X":
                sym = Symmetry.X
            elif toks[1] == "R90":
                sym = Symmetry.R90
            else:
                raise Exception(f"Expected X, Y, or R90, got {toks[1]}")
        else:
            raise Exception(f"expect CLASS, SYMMETRY, SIZE, or END, but got {toks[0]}")
        toks = fin.readline().strip().split()
    if width and height and site_class and sym:
        return Site(name, width, height, site_class, sym)
    else:
        raise Exception(f"Missing CLASS, SYMMETRY, or SIZE statements {toks[0]}")


class MacroClass(Enum):
    COVER = 1
    RING = 2
    BLOCK = 3
    PAD = 4
    CORE = 5
    ENDCAP = 6


class PinUse(Enum):
    SIGNAL = 1


@dataclass
class PinPort:
    layer_name: str
    rect: Rect


def parse_pin_port(fin: TextIOWrapper) -> PinPort:
    toks = fin.readline().strip().split()

    layer_name = rect = None
    while toks[0] != 'END':
        if toks[0] == 'LAYER':
            layer_name = toks[1]
        elif toks[0] == 'RECT':
            rect = Rect((float(toks[1]), float(toks[2])), (float(toks[3]), float(toks[4])))
        else:
            raise Exception(f'Unknown port statement {toks[0]}')
        toks = fin.readline().strip().split()

    if layer_name and rect:
        return PinPort(layer_name, rect)
    else:
        raise Exception("Missing layer name or rect when parsing port")

class MacroSiteOrient(Enum):
    N = 1
    S = 2
    E = 3
    W = 4
    FN = 5
    FS = 6
    FE = 7
    FW = 8


@dataclass
class MacroSite:
    name: str
    origin: tuple[float, float]
    orient: MacroSiteOrient
    x_count: int
    y_count: int
    x_step: int
    y_step: int


class PinDir(Enum):
    INPUT = 1
    OUTPUT = 2
    INOUT = 3
    FEEDTHRU = 4


@dataclass
class Pin:
    name: str
    pin_dir: PinDir
    use: PinUse
    port: PinPort

def parse_pin(fin: TextIOWrapper, name: str) -> Pin:
    toks = fin.readline().strip().split()
    dir = use = port = None
    while toks[0] != 'END' or toks[1] != name:
        if toks[0] == 'DIRECTION':
            dir_map = {
                "INPUT": PinDir.INPUT,
                "OUTPUT": PinDir.OUTPUT,
                "INOUT": PinDir.INOUT,
                "FEEDTHRU": PinDir.FEEDTHRU
            }

            dir = dir_map[toks[1]]
        elif toks[0] == 'USE':
            use_map = { "SIGNAL" : PinUse.SIGNAL }
            use = use_map[toks[1]]
        elif toks[0] == 'PORT':
            port = parse_pin_port(fin)
        else:
            raise Exception(f"Error parsing pin, found {toks[0]}")
        toks = fin.readline().strip().split()
    if dir and use and port:
        return Pin(name, dir, use, port)
    else:
        raise Exception("Error parsing pin")

@dataclass
class Macro:
    name: str
    macro_class: MacroClass
    width: float
    height: float
    origin: tuple[float, float]
    symmetry: Symmetry
    site: MacroSite
    pin: Pin


def parse_macro(fin: TextIOWrapper, name: str) -> Macro:
    macro_class = width = height = origin = symmetry = macro_site = pin = None
    toks = fin.readline().strip().split()
    while toks[0] != "END" or toks[1] != name:
        if toks[0] == "CLASS":
            if toks[1] == "CORE":
                macro_class = MacroClass.CORE
            elif toks[1] == "BLOCK":
                macro_class = MacroClass.BLOCK
            else:
                raise Exception(f"Expected a class but got {toks[1]}")
        elif toks[0] == "SIZE":
            width = float(toks[1])
            height = float(toks[3])
        elif toks[0] == "ORIGIN":
            origin = (float(toks[1]), float(toks[2]))
        elif toks[0] == "SYMMETRY":
            if toks[1] == "Y":
                symmetry = Symmetry.Y
            elif toks[1] == "X":
                symmetry = Symmetry.X
            elif toks[1] == "R90":
                symmetry = Symmetry.R90
        elif toks[0] == "SITE":
            orient_mapping = {
                "N": MacroSiteOrient.N,
                "S": MacroSiteOrient.S,
                "E": MacroSiteOrient.E,
                "W": MacroSiteOrient.W,
                "FN": MacroSiteOrient.FN,
                "FS": MacroSiteOrient.FS,
                "FE": MacroSiteOrient.FE,
                "FW": MacroSiteOrient.FW,
            }

            macro_site = MacroSite(
                toks[1],
                (float(toks[2]), float(toks[3])),
                orient_mapping[toks[4]],
                int(toks[6]),
                int(toks[8]),
                int(toks[10]),
                int(toks[11]),
            )
        elif toks[0] == 'PIN':
            pin = parse_pin(fin, toks[1])
        else:
            raise Exception(f"Unexpected macro statement {toks[0]}")
            
        toks = fin.readline().strip().split()
    if macro_class and width and height and origin and symmetry and macro_site and pin:
        return Macro(name, macro_class, width, height, origin, symmetry, macro_site, pin)
    else:
        raise Exception("Not all macro statements exist")



class Tech:
    def __init__(self, tech_path: str):
        self.layers = {}
        self.vias = []
        self.macros = []
        self.spacing_constraints = []
        self.sites = []
        with open(tech_path) as fin:
            self.namecase_sensitive = False

            line = fin.readline().strip()
            toks = line.split()
            while toks != ["END", "LIBRARY"]:
                print(toks)
                if not toks or toks[0] == "#":
                    pass
                elif toks[0] == "NAMESCASESENSITIVE":
                    self.namecase_sensitive = True
                elif toks[0] == "UNITS":
                    self.units = parse_units(fin)
                elif toks[0] == "LAYER":
                    layer = parse_layer(fin, toks[1])
                    self.layers[layer.name] = layer
                elif toks[0] == "VIA":
                    self.vias.append(parse_via(fin, toks[1]))
                elif toks[0] == "SPACING":
                    self.spacing_constraints = parse_spacing(fin)
                elif toks[0] == "SITE":
                    self.sites.append(parse_site(fin, toks[1]))
                elif toks[0] == "MACRO":
                    self.macros.append(parse_macro(fin, toks[1]))

                line = fin.readline().strip()
                toks = line.split()


class Design:
    def __init__(self, design_path: str, tech: Tech):
        pass


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
    print(tech.macros[0])
    design = Design(args.def_path, tech)
    print(design)


if __name__ == "__main__":
    main()
