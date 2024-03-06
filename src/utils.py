"""
Utility functions that are used in the project.

Functions:
  - progress: Prints a progress bar to the console.

"""


def progress(count: int, total: int, suffix: object | str | None = None) -> None:
    """
    Prints a progress bar to the console. Pycharm does not support this out of the box, so
    set emulate terminal in output console to true in the run configuration.

    Args:
        count (int): The current count, this is the index + 1 of the current iteration.
        total (int): The total number of iterations.

    Keyword Arguments:
        suffix (str): The suffix to be printed after the progress bar. (default: {None})

    Raises:
        AssertionError: Raised if count is not an integer.
        AssertionError: Raised if total is not an integer.
        AssertionError: Raised if count is negative.
        AssertionError: Raised if total is not positive.
        AssertionError: Raised if count is larger than total.

    """

    # TODO: until the progress bar is finished silence and collect the stdout.

    # Quickly check if the arguments are valid.
    assert isinstance(count, int), "Count must be an integer."
    assert isinstance(total, int), "Total must be an integer."
    assert count >= 0, "Count must be positive."
    assert total > 0, "Total must be positive."
    assert count <= total, "Count must be smaller or equal to total."

    # If no suffix is given, set it to "progressing".
    if suffix is None:
        suffix = "progressing"

    bar_len = 70

    # Calculate the percentage of the progress.
    filled_len = int(round(bar_len * count / float(total)))

    percents = str(round(100.0 * count / float(total), 1))
    # Ensure that the percentage is always 4
    percents = " " * (4 - len(percents)) + percents

    # Create the progress bar.
    bar_graphics = '=' * filled_len + '-' * (bar_len - filled_len)

    trailing_spaces = 24 * " "
    # Print the progress bar
    print(f"[{bar_graphics}] {percents}% -- {suffix}{trailing_spaces}\r", end="")

    # If the progress is finished, print a newline.
    if count == total:
        print()
