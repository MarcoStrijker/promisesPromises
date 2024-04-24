"""
This module contains functions to process the data.

Call process_all_programs() to process all programs. This will retrieve the text from the pdf and create a spacy doc
from the text. The text and doc will be saved to a file.

Call get_programs() to retrieve all programs. This will return a list of programs. If the programs have not been
processed yet, an exception will be raised.

The programs are stored in a list of Program objects. The Program object contains the following attributes:
    - election_type: The type of the election.
    - party: The party of the program.
    - election_date: The date of the election.
    - path: The path to the program.
    - text: The text of the program.
    - doc: The spacy doc of the program.

"""

import os
import random
import re
import time

from datetime import timedelta as td
from dataclasses import dataclass, field
from collections import Counter
from re import Pattern
from typing import Callable

import spacy
from spacy import Language
from spacy.tokens import Doc
from spacy_syllables import SpacySyllables  # type: ignore  #import is necessary for spacy to recognize the pipe

from pypdf import PdfReader

from src import utils


@dataclass(slots=True)
class Issuer:
    """A data class to represent a party or a group of parties."""
    name: str
    joined: bool = field(default=False, init=False)
    members: set[str] = field(default_factory=set, init=False)

    def __post_init__(self):
        """Post-initialization function to split the party name into members."""
        self.joined = "+" in self.name
        self.members = set(self.name.split("+"))

    def __eq__(self, other: object) -> bool:
        """Equality function to compare the Issuer object with another object.

        Args:
            other (object): The object to compare with.

        Returns:
            bool: True if the objects are equal, False otherwise.
        """

        # When searching for a string in the members of the issuer.
        if isinstance(other, str):
            return other in self.members

        # When comparing two Issuer objects.
        if isinstance(other, Issuer):
            return set(self.members) == set(other.members)

        raise TypeError(f"Cannot compare Issuer with {type(other)}")

    def __contains__(self, item: str) -> bool:
        """Contains function to check if an item is in the Issuer object.

        Args:
            item (str): The item to check.

        Returns:
            bool: True if the item is in the object, False otherwise.
        """
        return item in self.members

    def __hash__(self) -> int:
        """Hash function to hash the Issuer object.

        Returns:
            int: The hash value of the object.
        """
        return hash(self.name)

    def __str__(self) -> str:
        """String representation of the Issuer object.

        Returns:
            str: The string representation of the object.
        """
        return self.name

    def __repr__(self) -> str:
        """Representation of the Issuer object.

        Returns:
            str: The representation of the object.
        """
        return self.name


class Program:
    """
    A class to store and manipulate data. The class contains methods to retrieve the text from the pdf,
    create a spacy doc from the text and save the text and doc to a file.

    Attributes:
        text (str | None): The raw text of the program (Default: None).
        doc (Doc | None): The spacy doc instance of the program (Default: None).
        election_type (str): The type of the election.
        party (str): The party of the program.
        election_date (str): The election of the program.
        tags (list[str]): The tags of the program.
        path (str): The path to the program.

    """

    text: str | None = None
    doc: Doc | None = None

    def __init__(self, election_type: str, party: str, election_date: str, tags: list[str], path: str):
        """A class to store and manipulate data

        Arguments:
            election_type (str): The type of the election.
            party (str): The party of the program.
            election_date (str): The election of the program.
            tags (list[str]): The tags of the program.
            path (str): The path to the program.

        """
        self.election_type = election_type
        self.party = Issuer(party)
        self.election_date = election_date
        self.tags = tags
        self.path = path

    @property
    def joined_issue(self) -> bool:
        """Returns True if the program is a joined program, False otherwise."""
        return self.party.joined

    def reference(self, ext: str) -> str:
        """Return a reference to the file, including the party and election.

        Args:
            ext (str): The extension of the file.
        """
        # TODO: make more flexible for different election formats
        filename = f"{self.election_type}-{self.party}-{self.election_date}"

        # Add tags to filename, shorten tags to 3 characters
        # Also, prevent spaces in tags
        for tag in self.tags:
            filename += f"#{tag[:3]}"

        return f"{filename}.{ext}"

    def retrieve_text_from_pdf(self) -> None:
        """Retrieve the text from the pdf file. If the text has already been extracted,
        it will be retrieved from the file. Adds the text to the program object and
        saves it to a file.

        Note:
            Changes self.text
        """
        # Return text if it has already been extracted
        if self.text is not None:
            return

        # Retrieve text from the file if it exists
        path = os.path.join(_processed_text_path, self.reference("txt"))
        if os.path.exists(path) and not FORCE_REPROCESSING:
            with open(path, "r", encoding='utf-8') as f:
                self.text = f.read()
            return

        # Extract text from pdf
        text = extract_text_pdf(self.path)
        text = _remove_repeating_slogans(text)
        text = clean_pdf_text(text)

        self.text = text

        # Save text to disk
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)

    def create_doc_from_text(self) -> None:
        """Convert the text to a spacy doc. If the doc has already been created, it will be
        retrieved from the file. Adds the doc to the program object and saves it to a file.

        Note:
            Changes self.doc
        """

        # Return doc if it has already been created
        if self.doc is not None:
            return

        # Check if there is text to create a doc from
        if self.text is None:
            raise ValueError("No text to create a doc from. Call retrieve_text_from_pdf() first to retrieve the text.")

        # Compute path to file
        path = os.path.join(_processed_doc_path, self.reference("spacy"))

        # Retrieve doc from file if it exists on the disk
        if os.path.exists(path) and not FORCE_REPROCESSING:
            self.doc = Doc(nlp.vocab).from_disk(path)
            return

        # Create doc from text
        self.doc = nlp(self.text)

        # Save doc to disk
        self.doc.to_disk(path)

    def __repr__(self):
        """Return a string representation of the program."""
        name = f"{self.election_type} - {self.party} - {self.election_date}"

        for tag in self.tags:
            name += f" #{tag}"

        return name


class PathInfoExtractor:
    """ A class containing methods to extract information from a manifest path.

    When identifying programs, the path to the program contains information about the program, for example,
    election type, the election or the party. This class contains methods to extract this information from the path.

    For example, if the path is `.../TK/2017/VVD.pdf`, the election type is TK, the election date is 2017 and the party
    is VVD. The election type is always directly after the "manifests" folder in the path. In this specific example,
    the election date is always the second to last folder in the path and the party is always the file name without
    the .pdf extension. So, the output of the extractor should be like this.

    Example:
        {"election_type": "TK", "election_date": "2017", "party": "VVD"}

    When adding a new election type, the extractor should be added to the EXTRACTOR_REFERENCE dictionary and the
    extractor should be implemented as a static method in this class. The extractor should handle the parsing of the
    path for the specific path format. The reference in EXTRACTOR_REFERENCE is to automatically call the correct
    extractor for the election type.

    """

    EXTRACTOR_REFERENCE: dict[str, Callable[[str], dict[str, str]]]

    @staticmethod
    def get_election_type(path: str) -> str:
        """Helper method to extract the election type from the path. The election type is always directly after
        the "manifests" folder in the path.

        Arguments:
            path (str) -- The path to the program.

        Raises:
            ValueError: If 'manifests' is not in the path.
            IndexError: If manifest is the last folder in the path.

        Returns:
            The election type.
        """

        # Split the path on the os separator
        split_path = path.split(os.sep)

        # Since the election type is always directly after the "manifests" folder, we can find the election type
        # by finding the index of the "manifests" folder and adding 1 to it
        election_type_index = split_path.index("manifests") + 1

        return split_path[election_type_index]

    @staticmethod
    def extract_tags_and_remove_tags_from_filename(filename: str) -> tuple[str, list[str]]:
        """Extract the tags from the filename.

        The tags are the words in the filename that are lead by a hashtag. These
        tags are used to indicate the issues of the program, for example if the program
        doesn't have selectable text or the program is a concept version.

        Arguments:
            filename (str): The path to the program.

        Returns:
            tuple[str, list[str]] -- The filename without the tags and the tags.
        """
        # If there are no hashtags in the filename, return the filename and an empty list
        if "#" not in filename:
            return filename, []

        # Fetch the tags from the filename, and remove the hashtags
        # The tags are the words in the filename that are lead by a hashtag
        tags = [tag.removeprefix("#") for tag in re.findall(r"#\w+", filename)]

        # Remove the hashtags from the filename
        name = re.sub(r"\s*#\w+\s*", "", filename)

        return name, tags

    @staticmethod
    def extractor_type_date_party_tags(path: str) -> dict[str, str]:
        """Extract the election type, election date and party from the path.

        The path should be in the following format:
        .../{election_type}/{election_date}/{party}.pdf

        Arguments:
            path (str): The path to the program.

        Returns:
            The election type, election date and party.
        """
        # Remove the .pdf extension
        path = path.removesuffix(".pdf")

        # Split the path on the os separator
        split_path = path.split(os.sep)

        # Get info from the path
        filename, election_date, election_type = split_path[-1], split_path[-2], split_path[-3]

        # Extract the tags from the filename
        name, tags = PathInfoExtractor.extract_tags_and_remove_tags_from_filename(filename)

        return {"election_type": election_type, "election_date": election_date, "party": name, "tags": tags}

    EXTRACTOR_REFERENCE = {
        "TK": extractor_type_date_party_tags
    }
    """Reference to the methods to extract the information from the path for each election type"""


def extract_text_pdf(path: str) -> str:
    """Extract the text from a pdf file using pypdf

    Arguments:
        path (str): The path to the pdf file.

    Returns:
        The text from the pdf file.
    """
    reader = PdfReader(path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"

    return text


def identify_programs(target: str) -> list[Program]:
    """Walk through the directory and identify all pdf files for the programs of each party and
    election

    Arguments:
        target (str): The directory where the programs are stored.

    Returns:
        A list of programs.
    """
    found_programs = []
    for root, _, files in os.walk(target):
        for file in files:

            # Manifest are only pdf files
            if not file.endswith(".pdf"):
                continue

            # Compose full path to file
            file_path = os.path.join(root, file)

            # Retrieve election type from path
            # This is used to determine which and how the path should be parsed
            election_type_abbrev = PathInfoExtractor.get_election_type(file_path)

            if election_type_abbrev not in PathInfoExtractor.EXTRACTOR_REFERENCE:
                raise NotImplementedError(f"Unknown election type: {election_type_abbrev}. "
                                          f"Election type not implemented in PathInfoExtractor.extractor_reference."
                                          f"Currently unknown how to convert manifest path to program info. See"
                                          f"PathInfoExtractor docstring for more information.")

            extractor = PathInfoExtractor.EXTRACTOR_REFERENCE[election_type_abbrev]

            # Extract the info from the path
            info = extractor(file_path)

            # Add program to list
            found_programs.append(Program(**info, path=file_path))

    return found_programs


def clean_pdf_text(string: str) -> str:
    """Clean the text by removing special characters and newlines.

    See compiled regex patterns at definition for more information.

    Order of cleaning is important, as some patterns are dependent on the previous patterns.

    Arguments:
        string (str): The text to clean.

    Returns:
        The cleaned text.
    """

    string = special_char_pattern.sub(" ", string)
    string = page_num_pattern.sub(" ", string)
    string = hyphenation_pattern.sub("", string)
    string = newline_pattern.sub(" ", string)
    string = tab_pattern.sub(" ", string)
    string = double_dot_pattern.sub(". ", string)
    string = form_feed_pattern.sub(" ", string)
    string = large_numbers_pattern.sub(" ", string)
    string = single_char_pattern.sub(" ", string)
    string = double_space_pattern.sub(" ", string)

    return string.strip()


def _remove_repeating_slogans(text: str, start_size: int | None = None) -> str:
    """Removes repeating slogans from a text. A slogan is a sequence of words that occurs multiple times in the text
    which are not valuable for the analysis. This functions starts with a large snippet size and decreases it until the
    optimal snippet size is found. It checks if the most common snippet occurs often enough to be considered a slogan.
    If it does, it removes all occurrences of it and recursively calls itself to check if there are more slogans.

    Args:
        text (str): The text from which the slogans should be removed.

    Keyword Arguments:
        start_size (int): The size of the first snippet. Used to do efficient recursion. (default: {None})

    Returns:
        The text without slogans.

    """

    # Define parameters, these are the parameters that can be tweaked to change the behavior of this function.
    characters_per_page = 2200
    end_snippet_size = 34
    max_snippet_size = 200
    slogan_occurrence = 0.95

    # If the text is shorter than a page, identification of slogans is not possible.
    if len(text) < characters_per_page:
        return text

    # When functions is not called recursively, start_size is None. In that case, set it to the maximum snippet size.
    if not start_size:
        start_size = max_snippet_size

    # Calculate the number of pages in the text and the number of occurrences of the slogan for
    # it to be considered a slogan.
    pages = len(text) / characters_per_page
    occurrences_for_slogan = pages * slogan_occurrence

    # Loop over all possible snippet sizes until optimal size is found.
    for snippet_size in range(start_size, end_snippet_size - 1, -1):
        # Snippets are all the substrings of the text with length snippet_size.
        # So first we get the first snippet_size characters, then it moves one character to the right and gets the next
        # snippet_size characters, etc.
        snippets = [text[i:i + snippet_size] for i in range(0, len(text) - snippet_size)]

        # Count the number of occurrences of each snippet and get the two most common snippets.
        two_most_common = Counter(snippets).most_common(2)

        # When the two most common snippets occur equally often, optimal snippet size is not found yet.
        if two_most_common[0][1] == two_most_common[1][1]:
            continue

        # If the most common snippet does not occur often enough, continue with the next snippet size.
        if occurrences_for_slogan > two_most_common[0][1]:
            continue

        # If the most common snippet occurs often enough, remove all occurrences of it.
        # TODO: improve replacement to prevent removing sentence structure. e.g.:
        # TODO: "This is a repeating slogan. " instead of ". This is a repeating slogan. "
        text = text.replace(two_most_common[0][0], '')

        # Recursively call this function to check if there are more slogans.
        text = _remove_repeating_slogans(text, snippet_size - 1)

    return text


def process_all_programs() -> None:
    """Process all programs by retrieving the text from the pdf, creating a doc from the text
    and saving the text and doc to a file.

    """
    global _programs_processed, _programs

    print(f"Will process {len(_programs)} programs")

    # Randomize the order of the programs to prevent the same program from being processed first every time
    _programs = random.sample(_programs, len(_programs))

    for i, p in enumerate(_programs):
        s = time.perf_counter()
        # TODO: suppress and collect stdout and stderr
        p.retrieve_text_from_pdf()
        p.create_doc_from_text()

        e = time.perf_counter()

        # Create a suffix to show the remaining time and the current program
        remaining_time = utils.calculate_remaining_processing_time(i, len(_programs), e - s)
        remaining_time = str(td(seconds=remaining_time))
        suffix = f"{remaining_time} remaining -- {p}"

        utils.progress(i + 1, len(_programs), suffix)

    # Change variable to true to indicate that all programs have been processed
    # This enables the user to call the get_programs() api
    _programs_processed = True
    print("All programs processed, ready for analysis")


def get_all_programs() -> list[Program]:
    """Return all programs. If the programs have not been processed yet, an exception will be raised.

    Raises:
        Exception: If the programs have not been processed yet.

    Returns:
        A list of all programs.
    """
    if not _programs_processed:
        raise RuntimeError("Programs have not been processed yet. To process them, run process_all_programs()"
                           " before calling this function.")

    return _programs


def get_programs(*, election_type: str | None = None, party: str | None = None,
                 election_date: str | None = None, joined_issue: bool = False,
                 tags: list[str] | None = None) -> list[Program]:
    """Return a list of programs based on the election type, party, election date and tags. If no parameters are given,
    all programs will be returned. If the programs have not been processed yet, or no programs are found, an exception
    will be raised.

    Keyword Arguments:
        election_type (str): The type of the election. (default: {None})
        party (str): The party of the program. (default: {None})
        election_date (str): The date of the election. (default: {None})
        joined_issue (bool): Whether the program is a joined issue. (default: {False})
        tags (list[str]): The tags of the program. (default: {None})

    Returns:
        A list of requested programs.

    Raises:
        AssertionError: If any of the parameters are not of the correct type.
        RuntimeError: If the programs have not been processed yet.
        ValueError: If no program is found.
    """

    # Validate parameters
    assert isinstance(election_type, str) or election_type is None, "Election type must be a string or None."
    assert isinstance(party, str) or party is None, "Party must be a string or None."
    assert isinstance(election_date, str) or election_date is None, "Election date must be a string or None."
    assert isinstance(joined_issue, bool), "Joined issue must be a boolean."
    assert isinstance(tags, list) or tags is None, "Tags must be a list or None."

    # Raise if programs have not been processed yet
    if not _programs_processed:
        raise RuntimeError("Programs have not been processed yet. To process them, run process_all_programs()"
                           " before calling this function.")

    # Loop over all programs and find the programs that match the given parameters
    found_programs = [p for p in _programs
                      if (election_type is None or p.election_type == election_type)
                      and (party is None or p.party == party)
                      and (election_date is None or p.election_date == election_date)
                      and p.joined_issue == joined_issue
                      and (tags is None or all(tag in p.tags for tag in tags))]

    # Return found programs if any are found
    if found_programs:
        return found_programs

    # Raise if no program is found
    raise ValueError(f"No program found for election type: {election_type},"
                     f" party: {party}, election date: {election_date}")


def get_specific_program(*, election_type: str, party: str, election_date: str, joined_issue: bool = False,
                         tags: list[str] | None = None) -> Program:
    """Return a program by election type, party and election date. If no program is found, or the programs have not
    been processed yet, an exception will be raised.

    Arguments:
        election_type (str): The type of the election.
        party (str): The party of the program.
        election_date (str): The date of the election.

    Keyword Arguments:
        joined_issue (bool): Whether the program is a joined issue.
        tags (list[str]): The tags of the program. (default: {None})

    Returns:
        Program -- The requested program.

    Raises:
        AssertionError: If any of the parameters are not of the correct type.
        ValueError: If no program is found.
        RuntimeError: If the programs have not been processed yet.
    """

    # Validate parameters
    assert isinstance(election_type, str) or election_type is None, "Election type must be a string or None."
    assert isinstance(party, str) or party is None, "Party must be a string or None."
    assert isinstance(election_date, str) or election_date is None, "Election date must be a string or None."
    assert isinstance(joined_issue, bool), "Joined issue must be a boolean."
    assert isinstance(tags, list) or tags is None, "Tags must be a list or None."

    if not _programs_processed:
        raise RuntimeError("Programs have not been processed yet. To process them, run process_all_programs()"
                           " before calling this function.")

    properties = (election_type, party, election_date, joined_issue)

    # Find program
    for p in _programs:
        # Check if program matches properties
        if (p.election_type, p.party, p.election_date, p.joined_issue) != properties:
            continue

        # Check if program has all tags
        if tags is not None and not all(tag in p.tags for tag in tags):
            continue

        # Return found program
        return p

    raise ValueError(f"No program found for election type: {election_type},"
                     f" party: {party}, election date: {election_date}")


FORCE_REPROCESSING = False
"""For debugging purposes, set to true to force (re)processing of all programs.
If set to true, the text and doc will always be retrieved from the pdf and saved to a file."""

# Define regex patterns to clean the parsed text from a pdf file
# TODO: Add more special characters
# TODO: Refine regex patterns

special_char_pattern: Pattern = re.compile(r'[▶◀·•▪▫▬▭▮▯▰▱◆◇◈◊○◌◍◎●◐◑◒◓◔◕◖◗◘◙◢◣◤◥◦◧◨◩◪◫◬◭◮◯◸◹◺◻◼◽◾◿]')
"""Regex pattern that matches special characters"""

newline_pattern: Pattern = re.compile(r"(?<=\w)(\s*\n\s*)+(?=\w)")
"""Regex pattern that matches new lines that are present inbetween words"""

double_space_pattern: Pattern = re.compile(r"\s+")
"""Regex pattern that matches multiple spaces"""

double_dot_pattern: Pattern = re.compile(r"(\s*\.\s*)+")
"""Regex pattern that matches multiple dots, whitespace is allowed between and around the dots"""

tab_pattern: Pattern = re.compile(r"\t")
"""Regex pattern that matches tabs"""

page_num_pattern: Pattern = re.compile(r"\n+\s*\d+\s*\n+")
"""Regex pattern that matches page numbers, which is a number surrounded by newlines
and possibly spaces on either side"""

large_numbers_pattern: Pattern = re.compile(r"[\d\s\n]{9,}")
"""Regex pattern that matches large numbers, which is a number with potentially spaces between these numbers.
Only matches when digits, spaces and new lines that are 9 characters or longer"""

form_feed_pattern: Pattern = re.compile(r"\f")
"""Regex pattern that matches form feeds"""

hyphenation_pattern: Pattern = re.compile(r"-\x02|(?<=\w)-\s*\n\s*(?=\w+)")
"""Regex pattern that matches hyphenation. When hyphenation occurs, one word is split in two and a hyphen is 
added at the end of the first part, however, when extracting the text from the pdf, the hyphen should be 
removed and the two parts should be joined together."""

single_char_pattern: Pattern = re.compile(r"(?<=\s)\w(?=\s|$)")
"""Regex pattern that matches single characters, which are characters that 
are surrounded by whitespace or the end of the string"""

single_char_start_pattern: Pattern = re.compile(r"^\w\s")
"""Regex pattern that matches single characters at the start of the string"""

# Define paths
_directory: str = os.path.dirname(os.path.realpath(__file__))
_project_root: str = os.path.dirname(_directory)
_data_path: str = os.path.join(_project_root, "data")
_manifest_path: str = os.path.join(_data_path, "manifests")
_processed_path: str = os.path.join(_project_root, "processed")
_processed_text_path: str = os.path.join(_processed_path, "text")
_processed_doc_path: str = os.path.join(_processed_path, "doc")

# Ensure output folders exist
if not os.path.exists(_processed_path):
    os.mkdir(_processed_path)
if not os.path.exists(_processed_text_path):
    os.mkdir(_processed_text_path)
if not os.path.exists(_processed_doc_path):
    os.mkdir(_processed_doc_path)


_programs_processed = False
"""Indicates whether all programs have been processed by the process_all_programs() function
This is necessary to prevent the user from calling the get_programs() api before the programs have been processed"""

nlp: Language = spacy.load("nl_core_news_lg")
"""The core spacy model for the Dutch language. This is used to create a spacy doc from the text."""

# Add syllables pipe to spacy, this is necessary for the syllables_count attribute to be available on tokens
nlp.add_pipe("syllables", after="tagger")

_programs: list[Program] = identify_programs(_manifest_path)
"""Internal list of all programs"""

if __name__ == "__main__":
    process_all_programs()
