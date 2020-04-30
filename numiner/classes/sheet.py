# -*- coding: utf-8 -*-
import logging

from datetime import datetime
from pathlib import Path

import cv2 as cv
import matplotlib.pyplot as plt
import numpy as np


logging.basicConfig(
    filename="numiner.log",
    level=logging.WARNING,
    format="%(asctime)s %(message)s",
    datefmt="%Y/%m/%d %I:%M:%S %p",
)


class Sheet:
    _MARGIN_THICKNESS = 4
    _THRESHOLD_MAX = 200
    _THRESHOLD_MIN = 150
    _OUPUT_FILE_EXTENSION = ".png"
    _CHARACTER_SEQUENCE = "0123456789№₮********АБВГДЕЁЖЗИЙКЛМНОӨПРСТУҮФХЦЧШЩЭЮЯ********абвгдеёжзийклмноөпрстуүфхцчшщъыьэюя*****"

    def __init__(self, path, output, skip_char="*"):
        self.path = path
        self.output = output
        self.skip_char = skip_char
        self.source = cv.imread(str(path))

    def __repr__(self):
        return f"<Sheet No.{self.get_id():0>5}, path={self.path}>"

    def get_id(self):
        return int(self.path.stem.split("_")[-1])

    def get_row_count(self):
        return int(self.path.stem.split("_")[1])

    def get_col_count(self):
        return int(self.path.stem.split("_")[2])

    @classmethod
    def get_blurred_img(cls, source):
        return cv.bilateralFilter(source, 13, 20, 20)

    @classmethod
    def get_edges(cls, source):
        return cv.Canny(source, cls._THRESHOLD_MIN, cls._THRESHOLD_MAX)

    @classmethod
    def get_form_container(cls, source):
        contours, _ = cv.findContours(
            cls.get_edges(source), cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE
        )
        # cls.show([source, cls.get_edges(source)], [121, 122], ["Source", "Edges"], 2)
        biggest_contour = sorted(
            contours, key=lambda contour: cv.contourArea(contour), reverse=True
        )[0]
        x, y, w, h = cv.boundingRect(biggest_contour)
        bounding_rect_points = rectangle2points(x, y, w, h)
        approx_curve = cv.approxPolyDP(biggest_contour, min(w, h) / 2, True)

        if len(approx_curve) == 4:
            extreme_points = [[point[0][0], point[0][1]] for point in approx_curve]
            extreme_points.sort(key=lambda point: point[0] + point[1])
            if extreme_points[1][1] - extreme_points[1][0] > 0:
                extreme_points[1], extreme_points[2] = [
                    extreme_points[2],
                    extreme_points[1],
                ]

            homog, _ = cv.findHomography(np.array(extreme_points), np.array(bounding_rect_points))
            transformed = cv.warpPerspective(
                source, homog, (int(source.shape[1]), int(source.shape[0]))
            )
            new_x, new_y, new_w, new_h = cls.compensate(x, y, w, h, offset=5)
            return transformed[new_y : new_y + new_h, new_x : new_x + new_w]
        return None

    @classmethod
    def get_characters(cls, form, label_seq: str, skip_char: str):
        h, w, _ = form.shape
        height = (h + (10 - int(str(h)[-1]))) // 10
        width = (w + (10 - int(str(w)[-1]))) // 10
        label_height = height - width + 10
        character_seq = [
            form[
                row * height + label_height : row * height + height,
                col * width : col * width + width,
            ]
            for row in range(10)
            for col in range(10)
        ]

        return tuple(
            (label, letter) for label, letter in zip(label_seq, character_seq) if label != skip_char
        )

    @classmethod
    def compensate(cls, x, y, w, h, *, offset=5):
        return (x + offset, y + offset, w - (offset * 2), h - (offset * 2))

    @classmethod
    def process_characters(cls, characters):
        return tuple((label, cls.get_char(label, char)) for label, char in characters)

    def process_sheet(self, *, save: bool = False):
        form = self.get_form_container(self.source)
        form_save_path = self.output / Path(f"{self.get_id()}_form{self._OUPUT_FILE_EXTENSION}")
        cv.imwrite(str(form_save_path), form)
        characters = self.get_characters(form, self._CHARACTER_SEQUENCE, self.skip_char)
        char_seq = self.process_characters(characters)
        return self.save(char_seq, self.output, self.get_id()) if save else char_seq

    @classmethod
    def save(cls, characters, path, sheet_id):
        if not path.exists():
            path.mkdir()
        for num, char in enumerate(characters):
            char_path = path / Path(str(num))
            if not char_path.exists():
                char_path.mkdir()
            filename = f"{sheet_id}_{num}_{datetime.now().strftime('%Y%m%d%H%M%S')}{cls._OUPUT_FILE_EXTENSION}"

            save_path = char_path / filename
            if char[1] is not None:
                cv.imwrite(str(save_path), char[1])
            else:
                logging.warning(f"Couldn't save - {char[0]} ({filename})")

    @classmethod
    def show(cls, images, positions, titles, total):
        fig = plt.figure(figsize=[6, 3.7])

        for i in range(total):
            fig.add_subplot(positions[i])
            plt.axis("off")
            plt.title(titles[i])
            plt.imshow(
                cv.cvtColor(images[i], cv.COLOR_BGR2RGB) if images[i].shape == 3 else images[i],
            )

        plt.show()


def rectangle2points(x, y, w, h):
    return ((x, y), (x + w, y), (x, y + h), (x + w, y + h))
