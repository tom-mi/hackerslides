import os
import shutil
import subprocess
from typing import List, Optional, Tuple
import logging

from hackerslides.model import Presentation, Configuration, TextSlide, ImageSlide, Slide, SlideStyle, CodeSlide


class Renderer:

    def render(self, presentation: Presentation):
        raise NotImplementedError


class ImageMagickRenderer(Renderer):

    def __init__(self, configuration: Configuration):
        self.configuration = configuration

    def render(self, presentation: Presentation):
        self._recreate_empty_directory('out')
        for i, slide in enumerate(presentation.slides):
            ImageMagickSlideRenderer(configuration=self.configuration, slide=slide, slide_index=i).render()

    @staticmethod
    def _recreate_empty_directory(path):
        if os.path.exists(path):
            shutil.rmtree(path)
        os.makedirs(path)


class ImageMagickSlideRenderer:

    def __init__(self, configuration: Configuration, slide: Slide, slide_index: int):
        self.configuration = configuration
        self.slide = slide
        self.slide_index = slide_index
        self.image_size: Optional[Tuple[int, int]] = None

    def render(self):
        if isinstance(self.slide, TextSlide):
            return self._render_text_slide()
        elif isinstance(self.slide, ImageSlide):
            return self._render_image_slide()
        elif isinstance(self.slide, CodeSlide):
            return self._render_code_slide()
        else:
            raise ValueError(f'Cannot render unsupported slide {self.slide}')

    def _render_text_slide(self):
        _exec([
            *self._render_background(),
            *self._render_text(),
            self._slide_filename(),
        ])

    def _render_image_slide(self):
        self._determine_raw_image_size()
        text_cmd = self._render_meme_text() if self.slide.options.style == SlideStyle.MEME else self._render_text()
        _exec([
            *self._render_background(),
            *self._render_image(),
            *text_cmd,
            self._slide_filename(),
        ])
        pass

    def _render_code_slide(self):
        rendered_code_path = self._code_filename()
        _exec([
            'pygmentize',
            '-O', 'line_numbers=False',
            '-O', 'font_size=100',
            '-O', 'style=vim',
            '-O', 'font_name=DejaVu Sans Mono',
            '-o', rendered_code_path,
            self.slide.code_path
        ])
        _exec([
            *self._render_background(),
            '-background', 'transparent',
            '-gravity', 'Center',
            rendered_code_path,
            '-sample', f'{self.width}x{self.height}',
            '-extent', f'{self.width}x{self.height}',
            '-composite',
            self._slide_filename(),
        ])

    def _render_background(self) -> List[str]:
        return [
            'convert',
            '-size', f'{self.width}x{self.height}',
            f'xc:{self.slide.options.background}',
        ]

    def _render_text(self) -> List[str]:
        if self.slide.text is None:
            return []
        w, h = self._scaled_size()
        return [
            '-size', f'{w}x{h}',
            '-background', 'transparent',
            '-fill', self.slide.options.foreground,
            '-font', 'DeJaVu-Sans',
            '-gravity', 'Center',
            f'label:{self.slide.text}',
            '-composite'
        ]

    def _render_meme_text(self):
        if self.slide.text is None:
            return []
        lines = self.slide.text.splitlines(keepends=False)
        if len(lines) > 2:
            raise ValueError('Cannot render a meme with more than 2 lines of text')
        elif len(lines) == 1:
            lines.append('')

        w, h = self._background_size()
        scaled_h = h / 6 * self.slide.options.scale
        strokewidth = int(min(w, h) * self.slide.options.scale / 100)
        offset_y = int((h - scaled_h) / 2)
        common_options = [
            '-size', f'{w}x{scaled_h}',
            '-background', 'transparent',
            '-fill', 'white',
            '-stroke', 'black',
            '-strokewidth', str(strokewidth),
            '-font', 'Impact',
        ]
        return [
            *common_options,
            '-gravity', 'Center',
            f'label:{lines[0]}',
            '-geometry', f'+0-{offset_y}',
            '-composite',
            *common_options,
            '-gravity', 'Center',
            f'label:{lines[1]}',
            '-geometry', f'+0+{offset_y}',
            '-composite'
        ]

    def _render_image(self) -> List[str]:
        return [
            '-background', 'transparent',
            '-gravity', 'Center',
            self.slide.image_path,
            '-resize', f'{self.width}x{self.height}' + ('^' if self.slide.options.cover else ''),
            '-extent', f'{self.width}x{self.height}',
            '-composite',
        ]

    @property
    def width(self):
        return self.configuration.resolution[0]

    @property
    def height(self):
        return self.configuration.resolution[1]

    def _background_size(self) -> Tuple[int, int]:
        if self.image_size is None or self.slide.options.cover:
            width, height = self.width, self.height
        else:
            im_w, im_h = self.image_size
            width = min(self.width, int(self.height * im_w / im_h))
            height = min(self.height, int(self.width * im_h / im_w))
        return width, height

    def _scaled_size(self):
        width, height = self._background_size()

        scaled_w = width * self.slide.options.scale
        scaled_h = height * self.slide.options.scale
        return scaled_w, scaled_h

    def _determine_raw_image_size(self):
        output = _exec(['identify', '-format', '%w %h', self.slide.image_path])
        parts = output.split()
        self.image_size = int(parts[0]), int(parts[1])

    def _slide_filename(self) -> str:
        return f'out/slide_{self.slide_index:03d}.png'

    def _code_filename(self) -> str:
        return f'tmp/slide_{self.slide_index:03d}_code.png'


def _exec(command: List[str]) -> str:
    logging.debug(f'Executing command: {command}')
    return subprocess.check_output(command)
