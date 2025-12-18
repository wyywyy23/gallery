import os
import sys

PATH = os.path.abspath(os.path.dirname(__file__) + "/../")
PHOTO_PATH = os.path.abspath(os.path.dirname(__file__) + "/../photos/")


def main(mode):
    print(
        "Sorting images in {filename} by {mode}...".format(
            filename=PATH + "/config.json", mode=mode
        )
    )


if __name__ == "__main__":
    main(sys.argv[1])
