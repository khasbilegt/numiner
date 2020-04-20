# -*- coding: utf-8 -*-

import cv2 as cv


CHARACTER_SEQUENCE = "0123456789№₮********АБВГДЕЁЖЗИЙКЛМНОӨПРСТУҮФХЦЧШЩЭЮЯ********абвгдеёжзийклмноөпрстуүфхцчшщъыьэюя*****"


class Sheet:
    def __init__(self, path, col=10, row=10, seq=CHARACTER_SEQUENCE):
        self.col = col
        self.row = row
        self.path = path
        self.seq = seq
        self.img = cv.imread(path)

    def __repr__(self):
        return f"<Sheet {self.path}, row={self.row}, col={self.col}>"

    def get_img(self):
        return self.img
