import logging
import re
import sys
from argparse import ArgumentParser

from hackerslides.model import Configuration
from .parser import parse, ParsingError
from .renderer import ImageMagickRenderer


def main():
    config = parse_config()

    with open(config.path) as f:
        source = f.read()
        try:
            presentation = parse(source)
        except ParsingError as e:
            print(e)
            sys.exit(1)

        renderer = ImageMagickRenderer(config)
        renderer.render(presentation)


def parse_config():
    parser = ArgumentParser()
    parser.add_argument('path', help='Path to hackerslides file')
    parser.add_argument('--resolution', default='1920x1080', metavar='WIDTHxHEIGHT')
    parser.add_argument('-v', '--verbose', default=False, action='store_true')

    parsed_args = parser.parse_args()

    configure_logging(parsed_args.verbose)

    def _parse_resolution(resolution):
        m = re.match(r'^(\d+)x(\d+)$', resolution)
        if not m:
            parser.error('Resolution must be specified as WIDTHxHEIGHT')
        return int(m[1]), int(m[2])

    return Configuration(
        path=parsed_args.path,
        resolution=_parse_resolution(parsed_args.resolution)
    )


def configure_logging(verbose: bool):
    logging.basicConfig(format='%(levelname)-8s %(message)s', level=logging.DEBUG if verbose else logging.INFO)
