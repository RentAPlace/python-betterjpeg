import click

import concurrent.futures
import functools
import itertools
import logging
import os
import os.path
import subprocess
import sys
import threading
import time

EXTS = ('jpeg', 'jpg', 'JPEG', 'JPG')
COUNT_WARNING_LIMIT = 50
SIZE_WARNING_LIMIT = 100 * (1024**2)  # 100MB
LOG_LOCK = threading.RLock()

HELP = {
    'ignore_warnings':  'Supress all user prompts.',
    'verbose':          'Show execution related informations.',
    'log':              'Where to log execution informations.',
    'workers':          'Number of parallel workers.'
}


@click.command()
@click.argument('directory', type=click.Path(exists=True))
@click.option('-y/--ignore-warnings', is_flag=True, help=HELP['ignore_warnings'])
@click.option('-v/--verbose', is_flag=True, help=HELP['verbose'])
@click.option('--log', type=click.Path(exists=False, file_okay=True), help=HELP['log'])
@click.option('--workers', type=click.INT, default=2, help=HELP['workers'])
def cli(directory, y, v, log=None, workers=None):
    print('Welcome to BetterJPEG...')

    ignore_warnings = y
    verbose = v

    logger = init_logger(verbose, log)

    files = find_files(directory, EXTS)
    output_files = [file + '.out' for file in files]

    total_size = sum(get_filesize(file) for file in files)
    file_count = len(files)
    if not ignore_warnings and (file_count > COUNT_WARNING_LIMIT or \
                                total_size > SIZE_WARNING_LIMIT):
        warning = 'There are {0} optimizable files, totaling {1}. Continue ?'
        click.confirm(warning.format(file_count, pretty_filesize(total_size)), abort=True)

    start_time = time.time()

    io_tasks = zip(files, output_files)
    with concurrent.futures.ThreadPoolExecutor(workers) as executor:
        task_contexts = ({'input': input, 'output': output} for input, output in io_tasks)
        pending_tasks = tuple(executor.submit(optimize_routine, logger=logger, **ctx) for ctx in task_contexts)
        concurrent.futures.wait(pending_tasks)

    end_time = time.time()
    timespan = end_time - start_time
    end_size = sum(get_filesize(file) for file in files)
    size_diff = total_size - end_size

    print('Finished optimizing {0} files, totaling {1} ({2} saved).'.format(file_count, pretty_filesize(end_size), pretty_filesize(size_diff)))
    print('Execution took {0:.2f} seconds.'.format(timespan))


def optimize_routine(input=None, output=None, logger=None):
    with LOG_LOCK:
        logger.debug('input file "{0}"'.format(input))
    subprocess.call('cjpeg "{0}" > "{1}"'.format(input, output), shell=True)
    os.remove(input)
    os.rename(output, input)


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


def get_filesize(path):
    return os.stat(path).st_size


def pretty_filesize(bytes):
    if bytes >= 1024**3:
        return '{:.2f}'.format(bytes/1024**3) + 'GB'
    elif bytes >= 1024**2:
        return '{:.2f}'.format(bytes/1024**2) + 'MB'
    elif bytes >= 1024:
        return '{:.2f}'.format(bytes/1024) + 'KB'
    else:
        return '{}B'.format(bytes)


def filter_extension(extensions, filename):
    _, filename = os.path.split(filename)
    _, file_extension = os.path.splitext(filename)
    return any(extension in file_extension for extension in extensions)
