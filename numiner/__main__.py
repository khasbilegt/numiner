import sys


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    opts = [o for o in sys.argv[1:] if o.startswith("-")]

    print(args, opts)


if __name__ == "__main__":
    main()
