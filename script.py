from pathlib import Path


def try_validation():
    from arcsecond import ArcsecondConfig
    from oort.common.context import Context
    from oort.cli.options import State
    from oort.uploader.uploader import FileUploader

    state = State(False, False, 'test')
    config = ArcsecondConfig(state)
    context = Context(config, 'OORT-Test3', 'oma')
    context.validate()

    root = '/Users/onekiloparsec/arcsecond/arcsecond-oort/tests/fixtures/folder1/'
    uploader = FileUploader(context, Path(root), root / Path('very_simple_1.fits'))
    uploader.upload_file()


if __name__ == '__main__':
    # try_upload()
    try_validation()
