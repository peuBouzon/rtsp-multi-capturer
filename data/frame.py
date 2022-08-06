from dataclasses import dataclass
import numpy as np


@dataclass
class Frame:
    ret: bool
    frame: np.array
    conn_str: str
