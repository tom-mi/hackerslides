import textwrap

import pytest

from hackerslides.model import TextSlide, ImageSlide, SlideOptions, SlideStyle
from hackerslides.parser import parse, ParsingError

DEFAULT_SLIDE_OPTIONS = SlideOptions(
    background='black',
    foreground='white',
    cover=False,
    style=SlideStyle.DEFAULT,
    scale=1,
)


def test_parses_minimal_presentation():
    # given
    source = textwrap.dedent('''\
    Hello
    ''')

    # when
    presentation = parse(source)

    # then
    assert len(presentation.slides) == 1
    assert presentation.slides[0] == TextSlide('Hello', options=DEFAULT_SLIDE_OPTIONS)


def test_parses_multiline_text_slides():
    # given
    source = textwrap.dedent('''\
    Hello
    World
    
    Hello
    \\
      World!
    ''')

    # when
    presentation = parse(source)

    # then
    assert len(presentation.slides) == 2
    assert presentation.slides[0] == TextSlide('Hello\nWorld', options=DEFAULT_SLIDE_OPTIONS)
    assert presentation.slides[1] == TextSlide('Hello\n\n  World!', options=DEFAULT_SLIDE_OPTIONS)


def test_ignores_comments():
    # given
    source = textwrap.dedent('''\
    Hello
    # this is a comment
    World
    
    # this is another comment
    Hello # no comment
    \\# no comment
    ''')

    # when
    presentation = parse(source)

    # then
    assert len(presentation.slides) == 2
    assert presentation.slides[0] == TextSlide('Hello\nWorld', options=DEFAULT_SLIDE_OPTIONS)
    assert presentation.slides[1] == TextSlide('Hello # no comment\n# no comment', options=DEFAULT_SLIDE_OPTIONS)


def test_parses_minimal_image_slide():
    # given
    source = textwrap.dedent('''\
    @img foo.png
    ''')

    # when
    presentation = parse(source)

    # then
    assert len(presentation.slides) == 1
    assert presentation.slides[0] == ImageSlide(image_path='foo.png', options=DEFAULT_SLIDE_OPTIONS)


def test_parses_image_slide_with_text():
    # given
    source = textwrap.dedent('''\
    @img foo.png
    This is
    some text
    ''')

    # when
    presentation = parse(source)

    # then
    assert len(presentation.slides) == 1
    assert presentation.slides[0] == ImageSlide(image_path='foo.png', text='This is\nsome text',
                                                options=DEFAULT_SLIDE_OPTIONS)


def test_parse_options():
    # when
    source = textwrap.dedent('''\
    NoOptions
    
    FirstOptions
    :fg white
    :bg blue
    :cover
    :style meme
    :scale 0.5
    ''')

    # when
    presentation = parse(source)

    # then
    assert len(presentation.slides) == 2
    assert presentation.slides[0] == TextSlide('NoOptions', options=DEFAULT_SLIDE_OPTIONS)
    assert presentation.slides[1] == TextSlide('FirstOptions',
                                               options=SlideOptions(foreground='white', background='blue', cover=True,
                                                                    style=SlideStyle.MEME, scale=0.5))


def test_parse_other_options():
    # when
    source = textwrap.dedent('''\
    :fg green
    :bg blue
    :cover
    :style meme
    :scale 0.5
    
    NoOptions
    
    OtherOptions
    :nocover
    :nostyle
    ''')

    # when
    presentation = parse(source)

    # then
    assert len(presentation.slides) == 2
    assert presentation.slides[0] == TextSlide('NoOptions',
                                               options=SlideOptions(foreground='green', background='blue', cover=True,
                                                                    style=SlideStyle.MEME, scale=0.5))
    assert presentation.slides[1] == TextSlide('OtherOptions',
                                               options=SlideOptions(foreground='green', background='blue', cover=False,
                                                                    style=SlideStyle.DEFAULT, scale=0.5))


@pytest.mark.parametrize('source, line, message', [
    (textwrap.dedent('''\
    @foo sth
    '''), 0, 'Unknown keyword @foo'),
    (textwrap.dedent('''\
    @img
    '''), 0, 'No path given in @img statement'),
    (textwrap.dedent('''\
    @img foo.png
    @img bar.png
    '''), 1, 'Only one @img statement per slide is allowed'),
    (textwrap.dedent('''\
    :foo
    '''), 0, 'Unknown keyword :foo'),
    (textwrap.dedent('''\
    :style foo
    '''), 0, 'Unknown style foo'),
])
def test_parse_errors(source, line, message):
    with pytest.raises(ParsingError) as e:
        parse(source)

    assert e.value.line == line
    assert str(e.value.message) == message
