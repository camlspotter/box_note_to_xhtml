#!/usr/bin/env python3

import json
import argparse
import os
from dataclasses import dataclass
from typeguard import typechecked
from io import TextIOWrapper

# from icecream import ic # type: ignore

class Ast:
    def print(self, out:TextIOWrapper) -> None:
        assert False

def prints(out:TextIOWrapper, cs : list[Ast]) -> None:
    for c in cs:
        c.print(out)

class Top(Ast):
    content : list[Ast]

    def __init__(self, cs : list[Ast]):
        self.content = cs

    def print(self, out:TextIOWrapper) -> None:
        prints(out, self.content)

class Text(Ast):
    text : str

    def __init__(self, s : str):
        self.text = s

    def print(self, out:TextIOWrapper) -> None:
        out.write(self.text)

class Paragraph(Ast):
    content : list[Ast]

    def __init__(self, cs : list[Ast]):
        self.content = cs

    def print(self, out:TextIOWrapper) -> None:
        out.write("<p>\n")
        prints(out, self.content)
        out.write("<p/>\n")

class Heading(Ast):
    level : int
    content : list[Ast]

    def __init__(self, level : int, cs : list[Ast]):
        self.level = level
        self.content = cs

    def print(self, out:TextIOWrapper) -> None:
        out.write(f'<h{self.level}>')
        prints(out, self.content)
        out.write(f'</h{self.level}>\n')

class List(Ast):
    content : list[list[Ast]]

    def __init__(self, cs : list[list[Ast]]):
        self.content = cs

    def print(self, out:TextIOWrapper) -> None:
        out.write('<ul>')
        for c in self.content:
            out.write('<li>')
            for cc in c:
                # <li> <p> => <li>
                if isinstance(cc, Paragraph):
                    prints(out, cc.content)
                else:
                    cc.print(out)
        out.write('</ul>')

class Hard_break(Ast):
    def __init__(self):
        pass

    def print(self, out:TextIOWrapper) -> None:
        out.write('<br/>')

class Unknown(Ast):
    type : str

    def __init__(self, type : str):
        self.type = type

    def print(self, out:TextIOWrapper) -> None:
        out.write(f'unknown {self.type}')

class Href(Ast):
    url : str
    content : list[Ast]

    def __init__(self, url : str, cs : list[Ast]):
        self.url = url
        self.content = cs

    def print(self, out:TextIOWrapper) -> None:
        out.write(f'<a href="{self.url}">')
        prints(out, self.content)
        out.write(f'</a>')
    
def parse_top(d : dict) -> Ast:
    version = d['version']
    schema_version = d['schema_version']
    doc = d['doc']
    return parse_doc(doc)

def parse_doc(d : dict) -> Ast:
    match d['type']:
        case 'doc':
            return Top(parse_content(d))
        case 'text':
            t = Text(d['text'])
            if 'marks' in d:
                return parse_marks(d['marks'], t)
            else:
                return t
        case 'heading':
            return Heading(d['attrs']['level'], parse_content(d))
        case 'paragraph':
            return Paragraph(parse_content(d))
        case 'bullet_list':
            return List([parse_list_item(i) for i in d['content']])
        case 'hard_break':
            return Hard_break()
        case _:
            return Unknown(d['type'])
    assert False

def parse_marks(marks : dict, d : Ast) -> Ast:
    for m in marks:
        match m['type']:
            case 'link':
                d = Href(m['attrs']['href'], [d])
            case _:
                pass
    return d
    
def parse_content(d : dict) -> list[Ast]:
    return [ parse_doc(e) for e in d['content'] ]

def parse_list_item(d : dict) -> list[Ast]:
    return parse_content(d)
    
@dataclass
class Options:
    note : list[str]

@typechecked
def get_options() -> Options:
    parser = argparse.ArgumentParser(prog='bntm.py', description="Convert Box notes to XHTML")
    # parser.add_argument('notes', help='Box note files', type=str, nargs='+')
    parser.add_argument('note', nargs='*', help='Box note files')
    return Options(**vars(parser.parse_args()))

opts = get_options()

for i in opts.note:
    print('input', i)
    with open(i, 'r') as file:
        d = json.load(file)
        p = parse_top(d)
        body, _ = os.path.splitext(i)
        outfn = body + ".html"
        with open(outfn, 'w') as out:
            p.print(out)
