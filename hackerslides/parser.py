from dataclasses import dataclass
from typing import List, Union, Tuple

from .model import Presentation, Slide, TextSlide, ImageSlide, SlideOptions, SlideStyle, CodeSlide

IMG_KEYWORD = '@img'
CODE_KEYWORD = '@code'

DEFAULT_SLIDE_OPTIONS = SlideOptions(
    background='black',
    foreground='white',
    cover=False,
    style=SlideStyle.DEFAULT,
    scale=1,
)


@dataclass
class RawLine:
    value: str
    index: int


@dataclass
class TextLine:
    text: str
    index: int
    name = 'Text line'


@dataclass
class IncludeImageLine:
    path: str
    index: int
    name = f'{IMG_KEYWORD} statement'


@dataclass
class IncludeCodeLine:
    path: str
    index: int
    name = f'{CODE_KEYWORD} statement'


@dataclass
class EmptyLine:
    index: int
    name = 'empty line'


@dataclass
class OptionLine:
    key: str
    args: List[str]
    index: int


ParsedLine = Union[EmptyLine, TextLine, IncludeImageLine, IncludeCodeLine, OptionLine]


def parse(source: str) -> Presentation:
    lines = _filter_comments(_split_into_lines(source))
    parsed_lines = [_parse_line(line) for line in lines]
    chunks = _split_into_chunks(parsed_lines)

    if _is_option_only_chunk(chunks[0]):
        _, presentation_options = _parse_options(chunks.pop(0))
    else:
        presentation_options = SlideOptions()
    presentation_default_slide_options = _with_fallback(presentation_options, DEFAULT_SLIDE_OPTIONS)

    slides = [_parse_chunk_to_slide(chunk, presentation_default_slide_options) for chunk in chunks]

    return Presentation(slides=slides)


def _split_into_lines(source: str) -> List[RawLine]:
    return [RawLine(line, i) for i, line in enumerate(source.splitlines(keepends=False))]


def _parse_line(line: RawLine) -> ParsedLine:
    if line.value.startswith('@'):
        keyword, *args = line.value.split()
        if keyword == IMG_KEYWORD:
            if len(args) == 0:
                raise ParsingError(line.index, f'No path given in {IMG_KEYWORD} statement')
            path = args[0]
            return IncludeImageLine(path, line.index)
        elif keyword == CODE_KEYWORD:
            if len(args) == 0:
                raise ParsingError(line.index, f'No path given in {CODE_KEYWORD} statement')
            path = args[0]
            return IncludeCodeLine(path, line.index)
        else:
            raise ParsingError(line.index, f'Unknown keyword {keyword}')
    elif line.value.startswith(':'):
        return _parse_option(line)
    elif line.value.startswith('\\'):
        return TextLine(line.value[1:], line.index)
    elif line.value.strip() == '':
        return EmptyLine(line.index)
    else:
        return TextLine(line.value, line.index)


def _parse_option(line: RawLine) -> OptionLine:
    keyword, *args = line.value.split()
    if keyword in [':fg', ':bg', ':scale', ':style']:
        if len(args) != 1:
            raise ParsingError(line.index, f'Expected one argument for {keyword} statement')
        return OptionLine(keyword[1:], args, line.index)
    elif keyword in [':cover', ':nocover', ':nostyle']:
        if len(args) != 0:
            raise ParsingError(line.index, f'Expected no argument for {keyword} statement')
        return OptionLine(keyword[1:], args, line.index)
    else:
        raise ParsingError(line.index, f'Unknown keyword {keyword}')


def _parse_chunk_to_slide(chunk: List[ParsedLine], presentation_default_slide_options) -> Slide:
    chunk, options = _parse_options(chunk)
    if _is_image_chunk(chunk):
        slide = _parse_image_chunk(chunk, is_meme=options.style == SlideStyle.MEME)
    elif _is_code_chunk(chunk):
        slide = _parse_code_chunk(chunk)
    else:
        slide = TextSlide(_strip_escape_char_and_join(chunk))
    slide.options = _with_fallback(options, presentation_default_slide_options)
    return slide


def _split_into_chunks(lines: List[ParsedLine]) -> List[List[ParsedLine]]:
    current_chunk = []
    all_chunks = []

    def finish_chunk():
        nonlocal current_chunk
        if len(current_chunk) > 0:
            all_chunks.append(current_chunk)
            current_chunk = []

    for line in lines:
        if isinstance(line, EmptyLine):
            finish_chunk()
        else:
            current_chunk.append(line)
    finish_chunk()
    return all_chunks


def _is_option_only_chunk(chunk: List[ParsedLine]):
    return all([isinstance(line, OptionLine) for line in chunk])


def _is_image_chunk(chunk: List[ParsedLine]):
    return any([isinstance(line, IncludeImageLine) for line in chunk])


def _is_code_chunk(chunk: List[ParsedLine]):
    return any([isinstance(line, IncludeCodeLine) for line in chunk])


def _parse_image_chunk(chunk: List[ParsedLine], is_meme: bool):
    image_path = None
    text = []
    for line in chunk:
        if isinstance(line, IncludeImageLine):
            if image_path is not None:
                raise ParsingError(line.index, f'Only one {IMG_KEYWORD} statement per slide is allowed')
            image_path = line.path
            # todo validate file exists
        elif isinstance(line, TextLine):
            if is_meme and len(text) >= 2:
                raise ParsingError(line.index, 'Image slide with style meme cannot have more than 2 lines of text')
            text.append(line)
        else:
            raise ParsingError(line.index, f'{line.name} not supported in image slide')
    return ImageSlide(image_path=image_path, text=_strip_escape_char_and_join(text) or None)


def _parse_code_chunk(chunk: List[ParsedLine]):
    code_path = None
    for line in chunk:
        if isinstance(line, IncludeCodeLine):
            if code_path is not None:
                raise ParsingError(line.index, f'Only one {CODE_KEYWORD} statement per slide is allowed')
            code_path = line.path
            # todo validate file exists
        else:
            raise ParsingError(line.index, f'{line.name} not supported in code slide')
    return CodeSlide(code_path=code_path)


def _filter_comments(lines: List[RawLine]) -> List[RawLine]:
    return [line for line in lines if not line.value.startswith('#')]


def _strip_escape_char_and_join(chunk: List[TextLine]) -> str:
    return '\n'.join([_strip_escape_char_for_line(line.text) for line in chunk])


def _strip_escape_char_for_line(line: str) -> str:
    return line[1:] if line.startswith('\\') else line


def _parse_options(chunk: List[ParsedLine]) -> Tuple[List[ParsedLine], SlideOptions]:
    options = SlideOptions()
    filtered_lines = []
    for line in chunk:
        if isinstance(line, OptionLine):
            if line.key == 'fg':
                options.foreground = line.args[0]
            elif line.key == 'bg':
                options.background = line.args[0]
            elif line.key == 'scale':
                options.scale = float(line.args[0])
            elif line.key == 'cover':
                options.cover = True
            elif line.key == 'nocover':
                options.cover = False
            elif line.key == 'style':
                if line.args[0] == 'meme':
                    options.style = SlideStyle.MEME
                else:
                    raise ParsingError(line.index, f'Unknown style {line.args[0]}')
                options.meme = True
            elif line.key == 'nostyle':
                options.style = SlideStyle.DEFAULT
            else:
                raise ValueError(f'Unsupported option key {line.key}')
        else:
            filtered_lines.append(line)
    return filtered_lines, options


def _with_fallback(options: SlideOptions, fallback: SlideOptions) -> SlideOptions:
    return SlideOptions(
        fallback.background if options.background is None else options.background,
        fallback.foreground if options.foreground is None else options.foreground,
        fallback.cover if options.cover is None else options.cover,
        fallback.style if options.style is None else options.style,
        fallback.scale if options.scale is None else options.scale,
    )


class ParsingError(Exception):

    def __init__(self, line: int, message):
        self.message = message
        self.line = line

    def __str__(self):
        return f'Error in line {self.line + 1}: {self.message}'
