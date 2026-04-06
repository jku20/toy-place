from enum import Enum
from io import TextIOWrapper
import argparse
from dataclasses import dataclass

GRAY="\033[0;30m"
CYAN="\033[0;36m"
RED="\033[1;31m"
BLUE="\033[0;34m"
YELLOW="\033[0;33m"
GREEN="\033[1;32m"
ENDCOLOR="\033[0m"

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

class Dir(Enum):
    H = 1
    V = 2

@dataclass
class Routing:
    pitch: float
    width: float
    spacing: float
    direction: Dir

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
    while toks[0] != 'END':
        if toks[0] == 'DATABASE' and toks[1] == 'MICRONS':
            units.database_microns = float(toks[2])
        line = fin.readline().strip()
        toks = line.split()
    return units

def parse_layer(fin: TextIOWrapper, name: str) -> Layer:
    line = fin.readline().strip()
    toks = line.split()
    if toks[0] != 'TYPE':
        raise Exception('Expected TYPE')

    if toks[1] == 'MASTERSLICE':
        return Layer(name, Masterslice())
    elif toks[1] == 'CUT':
        return Layer(name, Cut())
    elif toks[1] == 'OVERLAP':
        return Layer(name, Overlap())
    elif toks[1] == 'ROUTING':
        d = {}
        for i in range(4):
            toks = fin.readline().strip().split()
            d[toks[0]] = toks[1]
        dir = Dir.H
        if d['DIRECTION'] == 'VERTICAL':
            dir = Dir.V
        return Layer(name, Routing(float(d['PITCH']), float(d['WIDTH']), float(d['SPACING']), dir))
    else:
        raise Exception(f'Unknown Layer type {toks[1]}')


@dataclass
class Via:
    name: str
    layers: dict[Layer, Rect]

def parse_via(fin: TextIOWrapper, name: str) -> Via:
    toks = fin.readline().strip().split()
    layers = {}
    while toks[0] != 'END':
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
    while toks[0] != 'END':
        if toks[0] == 'SAMENET':
            name1, name2, size = toks[1], toks[2], float(toks[3])
            spacings.append(Spacing(name1, name2, size))
        else:
            raise Exception('Expected SAMENET')
        toks = fin.readline().strip().split()
    return spacings

# @dataclass
# class Macro:
#     pass
# 
# def parse_macro(fin: TextIOWrapper, name: str) -> Macro:
#     pass

class Tech:
    def __init__(self, tech_path: str):
        self.layers = {}
        self.vias = []
        self.macros = []
        self.spacing_constraints = []
        with open(tech_path) as fin:
            self.namecase_sensitive = False

            line = fin.readline().strip()
            toks = line.split()
            while toks != ['END', 'LIBRARY']:
                print(toks)
                if not toks or toks[0] == '#':
                    pass
                elif toks[0] == 'NAMESCASESENSITIVE':
                    self.namecase_sensitive = True
                elif toks[0] == 'UNITS':
                    self.units = parse_units(fin)
                elif toks[0] == 'LAYER':
                    layer = parse_layer(fin, toks[1])
                    self.layers[layer.name] = layer
                elif toks[0] == 'VIA':
                    self.vias.append(parse_via(fin, toks[1]))
                elif toks[0] == 'SPACING':
                    self.spacing_constraints = parse_spacing(fin)
                elif toks[0] == 'MACRO':
                    break
                    # self.macros.append(parse_macro(fin, toks[1]))
                
                line = fin.readline().strip()
                toks = line.split()
class Design:
    def __init__(self, design_path: str, tech: Tech):
        pass

def main():
    parser = argparse.ArgumentParser(
        prog='place',
        description="places the components in a def file given a def and library of macros",
        epilog=f'enjoy the script {RED}<3{ENDCOLOR}'
    )

    parser.add_argument('-l', '--lef_path', help="lef file for macros used", required=True)
    parser.add_argument('-d', '--def_path', help="the def with a placement to optimize", required=True)

    args = parser.parse_args()

    tech = Tech(args.lef_path)
    print(tech.spacing_constraints)
    design = Design(args.def_path, tech)
    print(design)

if __name__ == "__main__":
    main()
