# -*- coding: utf-8 -*-

from pathlib import Path
from typing import List, Type

import cv2 as cv
import matplotlib.pyplot as plt
import numpy as np


CHARACTER_SEQUENCE = "0123456789№₮********АБВГДЕЁЖЗИЙКЛМНОӨПРСТУҮФХЦЧШЩЭЮЯ********абвгдеёжзийклмноөпрстуүфхцчшщъыьэюя*****"
Image = Type[np.ndarray]


class Sheet:
    def __init__(
        self, path: Path, seq: str = CHARACTER_SEQUENCE,
    ):
        self.path = path
        self.seq = seq
        self.img = cv.imread(str(path))
        self.clone = self.img.copy()

    def __repr__(self):
        return f"<Sheet No.{self.get_id():0>5}, path={self.path}>"

    def get_id(self) -> int:
        return int(self.path.stem.split("_")[-1])

    def get_row_count(self) -> int:
        return int(self.path.stem.split("_")[1])

    def get_col_count(self) -> int:
        return int(self.path.stem.split("_")[2])

    def get_original_img(self) -> Image:
        return self.img

    def get_gray_img(self):
        return cv.cvtColor(self.clone, cv.COLOR_BGR2GRAY)

    def blur(self):
        return cv.bilateralFilter(self.clone, 13, 20, 20)

    def process(self):
        ...

    @classmethod
    def show(
        cls,
        images: List[Image],
        positions: List[int],
        titles: List[str],
        total: int,
        cmap: str = "color",
    ) -> None:
        fig = plt.figure(figsize=[6, 3.7])

        for i in range(total):
            fig.add_subplot(positions[i])
            plt.axis("off")
            plt.title(titles[i])
            plt.imshow(
                cv.cvtColor(
                    images[i],
                    cv.COLOR_BGR2RGB if cmap == "color" else cv.COLOR_BGR2GRAY,
                )
            )

        plt.show()
