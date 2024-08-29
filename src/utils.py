"""
Utility functions that are used in the project.

Functions:
  - progress: Prints a progress bar to the console.
  - calculate_remaining_processing_time: Calculates the remaining processing time for the remaining programs.

"""

import os
import sys
from typing import Self, TextIO

_run_times = []
"""List of run times of the programs"""


class StdoutCollector:
    """
    A class that can collect the output of the standard output and standard error.

    Can be run with verbose mode, which will not collect the output. This is useful for testing.

    Example:
        collector = StdoutCollector()

        with collector:
            print("Hello world")

        collector.print_output()
        # Output: Hello world
    """

    def __init__(self) -> None:
        """Initializes the class."""
        self._output = ""
        self._stdout: TextIO | None = None
        self._stderr: TextIO | None = None

    @property
    def has_output(self) -> bool:
        """Returns True if there is output, False otherwise."""
        return bool(self._output)

    def write(self, message: str) -> None:
        """Represents the write method of the standard output."""
        self._output += message

    def flush(self) -> None:
        """Represents the flush method of the standard output."""

    def print_output(self) -> None:
        """Prints the collected output."""
        print(self._output)

    def __enter__(self) -> Self:
        """Enters the context manager and sets the standard output to this class."""
        self._stdout = sys.stdout
        self._stderr = sys.stderr
        sys.stdout = self  # type: ignore
        sys.stderr = self  # type: ignore
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exits the context manager and sets the standard output back to the original.

        Args:
            exc_type: The type of the exception.
            exc_val: The exception value.
            exc_tb: The exception traceback.
        """
        sys.stdout = self._stdout  # type: ignore
        sys.stderr = self._stderr  # type: ignore


def get_pdf_files_recursive(target: str) -> set[str]:
    """Get all pdf files recursively from a target directory.

    Args:
        target (str): The target directory.

    Returns:
        set: A set of file locations.
    """
    file_locations = set()
    for root, _, files in os.walk(target):
        for file in files:
            # Manifest are only pdf files
            if not file.endswith(".pdf"):
                continue

            # Compose full path to file
            file_locations.add(os.path.join(root, file))

    return file_locations


def progress(count: int, total: int, suffix: object | str = None):
    """
    Prints a progress bar to the console. Pycharm does not support this out of the box, so
    set emulate terminal in output console to true in the run configuration.

    Args:
        count (int): The current count, this is the index + 1 of the current iteration.
        total (int): The total number of iterations.

    Keyword Arguments:
        suffix (object | str | None): The suffix to be printed after the progress bar. (default: {None})

    Raises:
        AssertionError: Raised if count is not an integer.
        AssertionError: Raised if total is not an integer.
        AssertionError: Raised if count is negative.
        AssertionError: Raised if total is not positive.
        AssertionError: Raised if count is larger than total.

    """

    # Quickly check if the arguments are valid.
    assert isinstance(count, int), "Count must be an integer."
    assert isinstance(total, int), "Total must be an integer."
    assert count >= 0, "Count must be positive."
    assert total > 0, "Total must be positive."
    assert count <= total, "Count must be smaller or equal to total."

    bar_len = 50

    # If no suffix is given, set it to "progressing".
    suffix = suffix or "progressing"

    # Calculate the percentage of the progress.
    filled_len = int(round(bar_len * count / float(total)))

    percents = str(round(100.0 * count / float(total), 1))
    # Ensure that the percentage is always 4
    percents = " " * (4 - len(percents)) + percents

    # Create the progress bar.
    bar_graphics = "=" * filled_len + "-" * (bar_len - filled_len)

    trailing_spaces = 35 * " "
    # Print the progress bar
    print(f"[{bar_graphics}] {percents}% -- {suffix}{trailing_spaces}\r", end="")

    # If the progress is finished, print a newline.
    if count == total:
        print()


def calculate_remaining_processing_time(current: int, total: int, run_time: int | float) -> int:
    """Calculates the remaining processing time for the remaining programs.

    Args:
        current (int): The current index of the program.
        total (int): The total number of programs.
        run_time (int | float): The time it took to process the current program.

    Returns:
        The remaining processing time in seconds.
    """
    # Add last run time to global list
    _run_times.append(run_time)

    # Calculate the average time needed to process a program
    average_time = sum(_run_times) / len(_run_times)

    # Calculate the remaining time
    remaining = total - current

    remaining_run_time = int(remaining * average_time)

    return remaining_run_time or 1 if remaining - 1 else 0
