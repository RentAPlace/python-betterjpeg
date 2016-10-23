import click

import functools
import itertools
import logging
import os
import os.path
import subprocess
import sys
import time

EXTS = ('jpeg', 'jpg', 'JPEG', 'JPG')
COUNT_WARNING_LIMIT = 50

@click.command()
@click.argument('directory', type=click.Path(exists=True))
@click.option('-y/--ignore-warnings', is_flag=True, help='Ignore large image quantity warnings.')
@click.option('-v/--verbose', is_flag=True, help='Show execution related informations.')
@click.option('--log', type=click.Path(exists=False, file_okay=True), help='Where to log execution informations.')
def cli(directory, y, v, log=None):
    print('Welcome to BetterJPEG...')

    ignore_warnings = y
    verbose = v

    logger = init_logger(verbose, log)

    files = find_files(directory, EXTS)
    output_files = [file + '.out' for file in files]

    file_count = len(files)
    if not ignore_warnings and file_count > COUNT_WARNING_LIMIT:
        click.confirm('There are {} optimizable files. Continue ?'.format(file_count), abort=True)

    start_time = time.time()

    for input, output in zip(files, output_files):
        logger.debug('input file "{0}"'.format(input))
        command = 'cjpeg "{0}" > "{1}"'.format(input, output)
        # FIXME: The subprocess.call function blocks until subprocess is finished.
        #        Should find a non-blocking alternative.
        subprocess.call(command, shell=True)
        os.remove(input);
        os.rename(output, input);

    end_time = time.time()
    timespan = end_time - start_time

    print('Finished optimizing {0} files. Execution took {1:.2f} seconds.'.format(file_count, timespan))


def init_logger(verbose, log):
    log_format = '[%(asctime)s] %(levelname)s - %(message)s'
    formatter = logging.Formatter(log_format)
    level = logging.DEBUG
    logger = logging.getLogger(__name__)
    logger.setLevel(level)
    if verbose:
        stdout_logger = logging.StreamHandler(sys.stdout)
        stdout_logger.setLevel(level)
        stdout_logger.setFormatter(formatter)
        logger.addHandler(stdout_logger)
    if log:
        file_logger = logging.FileHandler(log)
        file_logger.setLevel(level)
        file_logger.setFormatter(formatter)
        logger.addHandler(file_logger)
    return logger


def find_files(path, extensions):
    walking = os.walk(path)
    files_segments = ((os.path.join(dirname, filename) for filename in filenames)
                      for dirname, _, filenames in walking)
    files = itertools.chain.from_iterable(files_segments)
    filtered_files = filter(functools.partial(filter_extension, extensions), files)
    files_abspaths = tuple(os.path.abspath(image) for image in filtered_files)
    return files_abspaths


def filter_extension(extensions, filename):
    _, filename = os.path.split(filename)
    _, file_extension = os.path.splitext(filename)
    return any(extension in file_extension for extension in extensions)
