import re
import sys
from argparse import ArgumentParser

from hackerslides.executor import DefaultExecutor
from hackerslides.formatter import Formatter
from hackerslides.model import Configuration

from .parser import parse, ParsingError


def main():
    config = parse_config()

    with open(config.path) as f:
        source = f.read()
        try:
            presentation = parse(source)
        except ParsingError as e:
            print(e)
            sys.exit(1)

        formatter = Formatter(config, presentation)
        commands = formatter.render()
        print(commands)
        executor = DefaultExecutor()
        executor.execute(commands)


def parse_config():
    parser = ArgumentParser()
    parser.add_argument('path', help='Path to hackerslides file')
    parser.add_argument('--resolution', default='1920x1080', metavar='WIDTHxHEIGHT')

    parsed_args = parser.parse_args()

    def _parse_resolution(resolution):
        m = re.match(r'^(\d+)x(\d+)$', resolution)
        if not m:
            parser.error('Resolution must be specified as WIDTHxHEIGHT')
        return int(m[1]), int(m[2])

    return Configuration(
        path=parsed_args.path,
        resolution=_parse_resolution(parsed_args.resolution)
    )
