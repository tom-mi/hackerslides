import textwrap

import pytest

from hackerslides.model import TextSlide, ImageSlide, SlideOptions
from hackerslides.parser import parse, ParsingError


def test_parses_minimal_presentation():
    # given
    source = textwrap.dedent('''\
    Hello
    ''')

    # when
    presentation = parse(source)

    # then
    assert len(presentation.slides) == 1
    assert presentation.slides[0] == TextSlide('Hello')


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
    assert presentation.slides[0] == TextSlide('Hello\nWorld')
    assert presentation.slides[1] == TextSlide('Hello\n\n  World!')


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
    assert presentation.slides[0] == TextSlide('Hello\nWorld')
    assert presentation.slides[1] == TextSlide('Hello # no comment\n# no comment')


def test_parses_minimal_image_slide():
    # given
    source = textwrap.dedent('''\
    @img foo.png
    ''')

    # when
    presentation = parse(source)

    # then
    assert len(presentation.slides) == 1
    assert presentation.slides[0] == ImageSlide(image_path='foo.png')


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
    assert presentation.slides[0] == ImageSlide(image_path='foo.png', text='This is\nsome text')


def test_parse_options():
    # when
    source = textwrap.dedent('''\
    :meme
    
    NoOptions
    
    FirstOptions
    :fg white
    :bg blue
    :cover
    :meme
    :scale 0.5
    
    OtherOptions
    :nocover
    :nomeme
    ''')

    # when
    presentation = parse(source)

    # then
    assert len(presentation.slides) == 3
    assert presentation.options == SlideOptions(meme=True)
    assert presentation.slides[0] == TextSlide('NoOptions', options=SlideOptions())
    assert presentation.slides[1] == TextSlide('FirstOptions',
                                               options=SlideOptions(foreground='white', background='blue', cover=True,
                                                                    meme=True, scale=0.5))
    assert presentation.slides[2] == TextSlide('OtherOptions',
                                               options=SlideOptions(cover=False, meme=False))


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
])
def test_parse_errors(source, line, message):
    with pytest.raises(ParsingError) as e:
        parse(source)

    assert e.value.line == line
    assert str(e.value.message) == message
