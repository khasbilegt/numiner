import logging

import cv2 as cv


class Letter:
    _SIZE = 28
    _BORDER_THICKNESS = 4

    @classmethod
    def get_threshold(cls, source, method=cv.THRESH_BINARY, *, adaptive=True):
        return (
            cv.adaptiveThreshold(source, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C, method, 15, 15)
            if adaptive
            else cv.threshold(source, cls._THRESHOLD_MIN, 255, method)
        )

    @classmethod
    def get_gray_img(cls, source):
        return cv.cvtColor(source, cv.COLOR_RGB2GRAY)

    @classmethod
    def process(cls, label, source):
        binary = cls.get_threshold(cls.get_gray_img(source), cv.THRESH_BINARY_INV)
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

        max_col = points[-1][0]
        max_row = points[-1][1]
        min_col = points[0][0]
        min_row = points[0][1]

        w_a = max_col - min_col
        h_a = max_row - min_row

        if w_a > h_a:
            diff_x = 0
            diff_y = (max(w_a, h_a) - min(w_a, h_a)) // 2
        elif w_a < h_a:
            diff_x = (max(w_a, h_a) - min(w_a, h_a)) // 2
            diff_y = 0
        else:
            diff_x = 0
            diff_y = 0

        cropped = binary[min_row - diff_y : max_row + diff_y, min_col - diff_x : max_col + diff_x]

        if cropped.size != 0:
            resized = cv.resize(cropped, (20, 20), interpolation=cv.INTER_AREA)
        else:
            logging.warning(f"[!] Ignored - {label}")
            return

        bordered = cv.copyMakeBorder(
            resized,
            cls._BORDER_THICKNESS,
            cls._BORDER_THICKNESS,
            cls._BORDER_THICKNESS,
            cls._BORDER_THICKNESS,
            borderType=cv.BORDER_CONSTANT,
            value=[0, 0, 0],
        )
        _, final = cls.get_threshold(bordered, cv.THRESH_BINARY + cv.THRESH_OTSU, adaptive=False)
        # cls.show(
        #     [source, binary, cropped, resized, bordered, final],
        #     [131, 132, 133, 231, 232, 233],
        #     ["source", "binary", "cropped", "resized", "bordered", "final"],
        #     6,
        # )
        return final
