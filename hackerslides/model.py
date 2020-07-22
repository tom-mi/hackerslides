from dataclasses import dataclass
from enum import Enum
from typing import Optional, Union, List, Tuple


class SlideStyle(Enum):
    DEFAULT = 'default'
    MEME = 'meme'


@dataclass
class SlideOptions:
    background: Optional[str] = None
    foreground: Optional[str] = None
    cover: Optional[bool] = None
    style: Optional[SlideStyle] = None
    scale: Optional[float] = None


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


@dataclass
class Configuration:
    path: str
    resolution: Tuple[int, int]
