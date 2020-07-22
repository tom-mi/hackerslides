from dataclasses import dataclass
from typing import List, Tuple, Union, Optional

from hackerslides.model import Presentation, TextSlide, Configuration, ImageSlide, SlideOptions, Slide


@dataclass
class ExecCommand:
    command: List[str]


@dataclass
class RmDirCommand:
    path: str


@dataclass
class MkDirCommand:
    path: str


Command = Union[ExecCommand, RmDirCommand, MkDirCommand]

DEFAULT_SLIDE_OPTIONS = SlideOptions(
    background='white',
    foreground='black',
    cover=False,
    meme=False,
    scale=1,
)


class Formatter:

    def __init__(self, configuration: Configuration, presentation: Presentation):
        self.configuration = configuration
        self.presentation = presentation

    def render(self) -> List[Command]:
        commands = [RmDirCommand('out'), MkDirCommand('out')]
        for i, slide in enumerate(self.presentation.slides):
            commands.append(self.SlideFormatter(self.configuration, self.presentation, slide, i).render())

        return commands

    class SlideFormatter:
        def __init__(self, configuration: Configuration, presentation: Presentation, slide: Slide, index: int):
            self.configuration = configuration
            self.slide = slide
            self.options = slide.options.with_default(presentation.options.with_default(DEFAULT_SLIDE_OPTIONS))
            self.index = index

        def render(self) -> Command:
            if isinstance(self.slide, TextSlide):
                return self._render_text_slide()
            elif isinstance(self.slide, ImageSlide):
                return self._render_image_slide()
            else:
                raise ValueError(f'Cannot render unsupported slide {self.slide}')

        def _render_text_slide(self) -> Command:
            return ExecCommand([
                *self._render_background(),
                *self._render_text(self.slide.text),
                '-gravity', 'Center',
                '-layers', 'flatten',
                self._slide_filename(),
            ])

        def _render_image_slide(self) -> Command:
            return ExecCommand([
                *self._render_background(),
                *self._render_image(self.slide.image_path),
                *self._render_text(self.slide.text),
                '-flatten',
                self._slide_filename(),
            ])

        def _render_background(self) -> List[str]:
            return [
                'convert',
                '-size', self._format_resolution(self.configuration.resolution),
                f'xc:{self.options.background}',
            ]

        def _render_text(self, text: Optional[str]) -> List[str]:
            if text is None:
                return []
            return [
                '-page', self._scaled_geometry(),
                '-size', self._scaled_size(),
                '-background', 'transparent',
                '-fill', self.options.foreground,
                '-font', 'DeJaVu-Sans',
                '-gravity', 'Center',
                f'label:{text}',
            ]

        def _render_image(self, path: str) -> List[str]:
            return [
                '-background', 'transparent',
                '-gravity', 'Center',
                path,
                '-resize', self._format_resolution(self.configuration.resolution) + ('^' if self.options.cover else ''),
                '-extent', self._format_resolution(self.configuration.resolution),
            ]

        @staticmethod
        def _format_resolution(resolution: Tuple[int, int]) -> str:
            return f'{resolution[0]}x{resolution[1]}'

        def _scaled_geometry(self):
            w, h = self.configuration.resolution
            scaled_w = w * self.options.scale
            scaled_h = h * self.options.scale
            offset_x = (w - scaled_w) / 2
            offset_y = (h - scaled_h) / 2
            return f'{scaled_w}x{scaled_h}+{offset_x}+{offset_y}'

        def _scaled_size(self):
            w, h = self.configuration.resolution
            scaled_w = w * self.options.scale
            scaled_h = h * self.options.scale
            return f'{scaled_w}x{scaled_h}'


        def _slide_filename(self) -> str:
            return f'out/slide_{self.index:03d}.png'
