from dataclasses import dataclass
from typing import Optional, Union, List, Tuple, ForwardRef


@dataclass
class SlideOptions:
    background: Optional[str] = None
    foreground: Optional[str] = None
    cover: Optional[bool] = None
    meme: Optional[bool] = None
    scale: Optional[float] = None

    def with_default(self, other: ForwardRef('SlideOptions')) -> ForwardRef('SlideOptions'):
        return SlideOptions(
            other.background if self.background is None else self.background,
            other.foreground if self.foreground is None else self.foreground,
            other.cover if self.cover is None else self.cover,
            other.meme if self.meme is None else self.meme,
            other.scale if self.scale is None else self.scale,
        )




@dataclass
class TextSlide:
    text: str
    options: SlideOptions = SlideOptions()


@dataclass
class ImageSlide:
    image_path: str
    text: Optional[str] = None
    options: SlideOptions = SlideOptions()


@dataclass
class CodeSlide:
    code_path: str
    options: SlideOptions = SlideOptions()


Slide = Union[TextSlide, ImageSlide, CodeSlide]


@dataclass
class Presentation:
    slides: List[Slide]
    options: SlideOptions = SlideOptions()


@dataclass
class Configuration:
    path: str
    resolution: Tuple[int, int]
