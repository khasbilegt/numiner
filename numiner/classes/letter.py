import logging

from datetime import datetime
from pathlib import Path

import cv2 as cv


class Letter:
    _SIZE = (28, 28)
    _KSIZE = (5, 5)
    _BORDER_THICKNESS = 2
    _THRESHOLD_MAX = 255
    _THRESHOLD_MIN = 150
    _OUPUT_FILE_EXTENSION = ".png"

    def __init__(self, path, output, *, label):
        self.path = path
        self.output = output
        self.label = label
        self.stem = path.stem
        self.source = cv.imread(str(path))

    def __repr__(self):
        return f"<Letter {self.path.name}, label={self.label}>"

    @classmethod
    def get_threshold(cls, source, method=cv.THRESH_BINARY, *, adaptive=True):
        return (
            cv.adaptiveThreshold(
                source, cls._THRESHOLD_MAX, cv.ADAPTIVE_THRESH_GAUSSIAN_C, method, 15, 15
            )
            if adaptive
            else cv.threshold(source, cls._THRESHOLD_MIN, cls._THRESHOLD_MAX, method)
        )

    @classmethod
    def get_gray_img(cls, source):
        try:
            return cv.cvtColor(source, cv.COLOR_RGB2GRAY) if source.size else None
        except AttributeError:
            return None

    @classmethod
    def get_blurred_img(cls, source):
        try:
            return cv.GaussianBlur(source, cls._KSIZE, 0) if source.size else None
        except AttributeError:
            return None

    @classmethod
    def get_char(cls, label, source):
        binary = cls.get_threshold(
            cls.get_blurred_img(cls.get_gray_img(source)), cv.THRESH_BINARY_INV
        )
        contours, _ = cv.findContours(binary, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        sorted_contours = sorted(contours, key=lambda ctr: cv.contourArea(ctr), reverse=True)
        point_x = []
        point_y = []
        for x, y, w, h in (cv.boundingRect(ctr) for ctr in sorted_contours):
            point_x.append(x)
            point_x.append(x + w)
            point_y.append(y + h)
            point_y.append(y)

        points = list(zip(sorted(point_x), sorted(point_y)))

        if not points:
            return

        max_col = points[-1][0]
        max_row = points[-1][1]
        min_col = points[0][0]
        min_row = points[0][1]

        w_a = max_col - min_col
        h_a = max_row - min_row

        if w_a > h_a:
            diff_x = 0
            diff_y = (w_a - h_a) // 2
        elif w_a < h_a:
            diff_x = (h_a - w_a) // 2
            diff_y = 0
        else:
            diff_x = 0
            diff_y = 0

        diff_x += cls._BORDER_THICKNESS
        diff_y += cls._BORDER_THICKNESS

        cropped = binary[min_row:max_row, min_col:max_col]
        cropped = cv.copyMakeBorder(
            cropped, diff_y, diff_y, diff_x, diff_x, borderType=cv.BORDER_CONSTANT, value=[0, 0, 0],
        )

        if cropped.size != 0:
            resized = cv.resize(cropped, cls._SIZE, interpolation=cv.INTER_AREA)
        else:
            print(f"[!] Ignored letter - {label}")
            logging.warning(f"[!] Ignored letter - {label}")
            return

        _, final = cls.get_threshold(resized, cv.THRESH_BINARY + cv.THRESH_OTSU, adaptive=False)
        return final

    @classmethod
    def save(cls, char, label, output, stem):
        if not output.exists():
            output.mkdir()

        char_path = output / Path(str(label))

        if not char_path.exists():
            char_path.mkdir()

        filename = (
            f"{label}_{stem}_{datetime.now().strftime('%Y%m%d%H%M%S')}{cls._OUPUT_FILE_EXTENSION}"
        )

        save_path = char_path / filename
        if char is not None:
            cv.imwrite(str(save_path), char)
        else:
            print(f"[!] Couldn't save - {label} ({filename})")
            logging.warning(f"Couldn't save - {label} ({filename})")

    def process(self, *, save=True):
        try:
            if self.source.size:
                char = self.get_char(self.label, self.source)
                return self.save(char, self.label, self.output, self.stem) if save else char
            else:
                print(f"[!] Ignored letter - {self.path}")
                logging.warning(f"Couldn't save letter - {self.label} ({self.path})")
                return None
        except AttributeError:
            print(f"[!] Ignored letter - {self.path}")
            logging.warning(f"Couldn't save letter - {self.label} ({self.path})")
            return None
