from dataclasses import dataclass
from typing import Literal

Limit = int | Literal['max'] | None

@dataclass
class Namespace:
    id: int
    name: str
    canonical: str
    first_letter_case: bool
