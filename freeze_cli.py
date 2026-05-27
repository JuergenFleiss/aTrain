import multiprocessing

multiprocessing.freeze_support()

if __name__ == "__main__":
    from aTrain.cli import cli

    try:
        cli()
    except KeyboardInterrupt:
        pass
