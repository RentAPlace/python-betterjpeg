import concurrent.futures
import logging
import os
import os.path
import subprocess
import sys
import threading
import time

from rap.common import dictutils
from rap.common import filesystem as fs

import click

from . import __description__, __pkgname__, __version__

EXECUTABLE = "mozcjpeg"
EXTS = ("jpeg", "jpg", "JPEG", "JPG")
COUNT_WARNING_LIMIT = 50
SIZE_WARNING_LIMIT = 100 * (1024**2)  # 100MB
LOG_LOCK = threading.RLock()

HELP = {
    "additional-args":  "Additional arguments to pass to CJPEG.",
    "log":              "Where to log execution informations.",
    "verbose":          "Show execution related informations.",
    "workers":          "Number of parallel workers.",
    "ignore-warnings":  "Supress all user prompts."
}


@click.command()
@click.argument("directory", type=click.Path(exists=True))
@click.option("-a", "--additional-args", type=click.STRING, help=HELP["additional-args"])
@click.option("-l", "--log", type=click.Path(exists=False, file_okay=True), help=HELP["log"])
@click.option("-v", "--verbose", is_flag=True, help=HELP["verbose"])
@click.option("-w", "--workers", type=click.INT, default=2, help=HELP["workers"])
@click.option("-y", "--ignore-warnings", is_flag=True, help=HELP["ignore-warnings"])
@click.version_option()
def cli(directory, additional_args=None, log=None, verbose=None, workers=None, ignore_warnings=None):
    print("Welcome to BetterJPEG...")

    logger = init_logger(verbose, log)

    files        = fs.walk_by_extensions(directory, EXTS)
    absfiles     = list(os.path.abspath(file) for file in files)
    output_files = [file + ".out" for file in absfiles]

    total_size  = sum(fs.get_filesize(file) for file in absfiles)
    pretty_size = fs.pretty_filesize(total_size)
    file_count  = len(absfiles)

    if not ignore_warnings and (file_count > COUNT_WARNING_LIMIT or \
                                total_size > SIZE_WARNING_LIMIT):
        warning = "There are {0} optimizable files, totaling {1}. Continue ?"
        click.confirm(warning.format(file_count, pretty_size), abort=True)

    start_time = time.time()

    io_tasks = zip(absfiles, output_files)
    global_task_context = {"args": additional_args, "logger": logger}
    with concurrent.futures.ThreadPoolExecutor(workers) as executor:
        task_contexts = (dictutils.merge(global_task_context, {"input": input, "output": output}) for input, output in io_tasks)
        pending_tasks = list(executor.submit(optimize_routine, **ctx) for ctx in task_contexts)
        concurrent.futures.wait(pending_tasks)

    end_time = time.time()
    timespan = end_time - start_time
    end_size = sum(fs.get_filesize(file) for file in absfiles)
    size_diff = total_size - end_size

    print("Finished optimizing {0} files, totaling {1} ({2} saved).".format(file_count, fs.pretty_filesize(end_size), fs.pretty_filesize(size_diff)))
    print("Execution took {0:.2f} seconds.".format(timespan))


def optimize_routine(input=None, output=None, args=None, logger=None):
    if not args: args = ""
    with LOG_LOCK:
        logger.debug("input file \"{0}\"".format(input))
    command = "{0} {1} \"{2}\" > \"{3}\"".format(EXECUTABLE, args, input, output)
    subprocess.call(command, stderr=subprocess.DEVNULL, shell=True)
    if fs.get_filesize(output) > 0:
        os.remove(input)
        os.rename(output, input)
    else:
        with LOG_LOCK:
            logger.error("Optimization unsuccessful for input \"{0}\", discarded changes".format(input))
        os.remove(output)


def init_logger(verbose, log):
    log_format = "[%(asctime)s] %(levelname)s - %(message)s"
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
