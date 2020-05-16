import random

from pathlib import Path

import cv2 as cv
import numpy


class Converter:
    DESTINATION = Path().cwd()
    TEST_LABELS_PATH = Path("t10k-labels-idx1-ubyte")
    TEST_IMAGES_PATH = Path("t10k-images-idx3-ubyte")
    TRAIN_LABELS_PATH = Path("train-labels-idx1-ubyte")
    TRAIN_IMAGES_PATH = Path("train-images-idx3-ubyte")

    @classmethod
    def get_images(cls, path, size=0):
        if not path.exists():
            raise FileNotFoundError

        if not path.is_dir():
            raise NotADirectoryError

        image_paths = list(
            (
                label,
                tuple(
                    cv.imread(str(image), -1)
                    for image in dir.iterdir()
                    if image.suffix in (".png", ".jgp")
                    and image.stat().st_size > 0
                    and cv.imread(str(image), -1).size > 0
                ),
            )
            for label, dir in enumerate(
                sorted((subdir for subdir in path.iterdir() if subdir.is_dir()))
            )
        )

        data = []
        for label, length, images in (
            (label, len(images), images) for label, images in image_paths
        ):
            if length < (count := size if size > 0 else length):
                raise KeyError(
                    f"The folder No.{label} has {length} images which is less than the specified size."
                )

            sampled_images = random.sample(images, count)
            for image in sampled_images:
                data.append((label, image))

        return data

    @classmethod
    def make_arrays(cls, data, ratio=20):
        if ratio == "train":
            ratio = 0
        elif ratio == "test":
            ratio = 1
        else:
            ratio = float(ratio) / 100

        count = len(data)
        labels, images = tuple(zip(*data))
        train_size = int(count * (1 - ratio))
        test_size = count - train_size

        train_images = numpy.zeros((train_size, 28, 28), dtype=numpy.uint8)
        test_images = numpy.zeros((test_size, 28, 28), dtype=numpy.uint8)
        train_labels = numpy.zeros(train_size, dtype=numpy.uint8)
        test_labels = numpy.zeros(test_size, dtype=numpy.uint8)

        for index in range(train_size):
            train_images[index] = images[index]
            train_labels[index] = labels[index]

        for index in range(test_size):
            test_images[index] = images[train_size + index]
            test_labels[index] = labels[train_size + index]

        return train_images, train_labels, test_images, test_labels

    @classmethod
    def compress(cls):
        import gzip
        import shutil

        for path in cls.DESTINATION.glob("*ubyte"):
            with open(path, "rb") as f_in:
                with gzip.open(f"{path}.gz", "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)

    @classmethod
    def write_data(cls, data, output, *, writeLabel=True):
        header = (
            numpy.array([0x0801, len(data)], dtype=">i4")
            if writeLabel
            else numpy.array([0x0803, len(data), 28, 28], dtype=">i4")
        )
        with open(output, "wb") as f:
            f.write(header.tobytes())
            f.write(data.tobytes())

    @classmethod
    def process(cls, src, dst, *, size, ratio):
        if dst.exists():
            cls.DESTINATION = dst

        cls.TEST_LABELS_PATH = cls.DESTINATION / "t10k-labels-idx1-ubyte"
        cls.TEST_IMAGES_PATH = cls.DESTINATION / "t10k-images-idx3-ubyte"
        cls.TRAIN_LABELS_PATH = cls.DESTINATION / "train-labels-idx1-ubyte"
        cls.TRAIN_IMAGES_PATH = cls.DESTINATION / "train-images-idx3-ubyte"

        images = cls.get_images(src, size)
        random.shuffle(images)

        train_images, train_labels, test_images, test_labels = cls.make_arrays(images, ratio)

        if size == "train":
            cls.write_data(train_labels, cls.TRAIN_LABELS_PATH)
            cls.write_data(train_images, cls.TRAIN_IMAGES_PATH, writeLabel=False)
        elif size == "test":
            cls.write_data(test_labels, cls.TEST_LABELS_PATH)
            cls.write_data(test_images, cls.TEST_IMAGES_PATH, writeLabel=False)
        else:
            cls.write_data(train_labels, cls.TRAIN_LABELS_PATH)
            cls.write_data(train_images, cls.TRAIN_IMAGES_PATH, writeLabel=False)
            cls.write_data(test_labels, cls.TEST_LABELS_PATH)
            cls.write_data(test_images, cls.TEST_IMAGES_PATH, writeLabel=False)

        cls.compress()
