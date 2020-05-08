# -*- coding: utf-8 -*-
import logging

from datetime import datetime
from pathlib import Path

import cv2 as cv
import matplotlib.pyplot as plt
import numpy as np

from .letter import Letter


class Sheet:
    _MARGIN_THICKNESS = 4
    _THRESHOLD_MAX = 200
    _THRESHOLD_MIN = 150
    _OUPUT_FILE_EXTENSION = ".png"
    # fmt: off
    _CHARACTER_SEQUENCE = (
        (0, "0"), (1, "1"), (2, "2"), (3, "3"), (4, "4"), (5, "5"), (6, "6"), (7, "7"), (8, "8"), (9, "9"),
        (10, "А"), (11, "Б"), (12, "В"), (13, "Г"), (14, "Д"), (15, "Е"), (16, "Ё"), (17, "Ж"), (18, "З"), (19, "И"),
        (20, "Й"), (21, "К"), (22, "Л"), (23, "М"), (24, "Н"), (25, "О"), (26, "Ө"), (27, "П"), (28, "Р"), (29, "С"),
        (30, "Т"), (31, "У"), (32, "Ү"), (33, "Ф"), (34, "Х"), (35, "Ц"), (36, "Ч"), (37, "Ш"), (38, "Щ"), (39, "Э"),
        (40, "Ю"), (41, "Я"), (42, "а"), (43, "б"), (44, "в"), (45, "г"), (46, "д"), (47, "е"), (48, "ё"), (49, "ж"),
        (50, "з"), (51, "и"), (52, "й"), (53, "к"), (54, "л"), (55, "м"), (56, "н"), (57, "о"), (58, "ө"), (59, "п"),
        (60, "р"), (61, "с"), (62, "т"), (63, "у"), (64, "ү"), (65, "ф"), (66, "х"), (67, "ц"), (68, "ч"), (69, "ш"),
        (70, "щ"), (71, "ъ"), (72, "ы"), (73, "ь"), (74, "э"), (75, "ю"), (76, "я"), (77, "№"), (78, "@"), (79, "#"),
        (80, "$"), (81, "%"), (82, "&"), (83, "*"), (84, "("), (85, ")"), (86, ";"), (87, ":"), (88, "₮"), (89, ">"),
        (90, "<"), (91, "!"), (92, "?"), (93, "+"), (94, "-"), (95, "/"), (96, "≥"), (97, "≤"), (98, "~"), (99, "=")
    )
    # fmt: on

    def __init__(self, path, output, skip_char="|"):
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
        biggest_contour = sorted(
            contours, key=lambda contour: cv.arcLength(contour, True), reverse=True
        )[0]
        x, y, w, h = cv.boundingRect(biggest_contour)
        bounding_rect_points = rectangle2points(x, y, w, h)
        approx_curve = cv.approxPolyDP(
            biggest_contour, 0.01 * cv.arcLength(biggest_contour, True), True
        )

        if len(approx_curve) >= 4:
            points = tuple(
                (point[0][0] + point[0][1], point[0][0] - point[0][1], (point[0][0], point[0][1]))
                for point in approx_curve
            )
            sum_sorted_points = sorted(points, key=lambda point: point[0])
            diff_sorted_points = sorted(points, key=lambda point: point[1])

            extreme_points = (
                sum_sorted_points[0][-1],
                diff_sorted_points[-1][-1],
                diff_sorted_points[0][-1],
                sum_sorted_points[-1][-1],
            )

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
        label_height = height - width
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
        return tuple((label, Letter.get_char(label, char)) for label, char in characters)

    def process_sheet(self, *, save: bool = False):
        try:
            if not self.source:
                print(f"[!] Couldn't save sheet - {self.path}")
                logging.warning(f"[!] Couldn't save sheet - {self.path}")
        except ValueError:
            if self.source.size:
                form = self.get_form_container(self.source)
                form_save_path = self.output / Path(
                    f"{self.get_id()}_form{self._OUPUT_FILE_EXTENSION}"
                )
                try:
                    if form.any():
                        cv.imwrite(str(form_save_path), form)
                        characters = self.get_characters(
                            form, self._CHARACTER_SEQUENCE, self.skip_char
                        )
                        char_seq = self.process_characters(characters)
                        return self.save(char_seq, self.output, self.get_id()) if save else char_seq
                except AttributeError:
                    raise RuntimeError(
                        f"The given sheet ({form_save_path}) can't be processed. Check and try again."
                    )

    @classmethod
    def save(cls, characters, path, sheet_id):
        if not path.exists():
            path.mkdir()
        for label, char in characters:
            char_path = path / Path(str(label[0]))
            if not char_path.exists():
                char_path.mkdir()
            filename = f"{sheet_id}_{label[0]}_{datetime.now().strftime('%Y%m%d%H%M%S')}{cls._OUPUT_FILE_EXTENSION}"

            save_path = char_path / filename
            if char is not None:
                cv.imwrite(str(save_path), char)
            else:
                print(f"[!] Couldn't save sheet - {label = } ({filename})")
                logging.warning(f"[!] Couldn't save sheet - {label} ({filename})")

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
