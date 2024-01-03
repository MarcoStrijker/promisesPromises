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
import re
from collections import Counter
from dataclasses import dataclass

import spacy
from spacy_syllables import SpacySyllables  # type: ignore  #import is necessary for spacy to recognize the pipe

from pypdf import PdfReader
from spacy.tokens import Doc

from src import utils


@dataclass(slots=True)
class Program:
    """A dataclass to store the information of a program.

    Arguments:
        election_type {str} -- The type of the election.
        party {str} -- The party of the program.
        election {str} -- The election of the program.
        path {str} -- The path to the program.
    """
    election_type: str
    party: str
    election_date: str
    path: str

    text: str = None
    doc: Doc = None

    def reference(self, ext: str) -> str:
        """Return a reference to the file, including the party and election.

        Args:
            ext {str} -- The extension of the file.
        """
        # TODO: make more flexible for different election formats

        return f"{self.election_type} - {self.party} - {self.election_date}.{ext}"

    def retrieve_text_from_pdf(self) -> None:
        """Retrieve the text from the pdf file. If the text has already been extracted,
        it will be retrieved from the file. Adds the text to the program object and
        saves it to a file.

        Returns:
            str -- The text of the program.
        """
        # Return text if it has already been extracted
        if self.text is not None:
            return

        # Retrieve text from file if it exists
        path = os.path.join(processed_text_path, self.reference("txt"))
        if os.path.exists(path) and not FORCE_REPROCESSING:
            with open(path, "r", encoding='utf-8') as f:
                self.text = f.read()
            return

        # Extract text from pdf
        text = extract_text_pdf(self.path)
        text = remove_repeating_slogans(text)
        text = clean_pdf_text(text)

        self.text = text

        # Save text to disk
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)

    def create_doc_from_text(self) -> None:
        """Convert the text to a spacy doc. If the doc has already been created,
        it will be retrieved from the file. Adds the doc to the program object and
        saves it to a file.
        """

        # Return doc if it has already been created
        if self.doc is not None:
            return

        # Compute path to file
        path = os.path.join(processed_doc_path, self.reference("doc"))

        # Retrieve doc from file if it exists on the disk
        if os.path.exists(path) and not FORCE_REPROCESSING:
            self.doc = Doc(nlp.vocab).from_disk(path)
            return

        # Create doc from text
        self.doc = nlp(self.text)

        # Save doc to disk
        self.doc.to_disk(path)

    def __repr__(self):
        return f"{self.party} - {self.election_type} - {self.election_date}"


class PathInfoExtractor:
    """ A class containing methods to extract information from a manifest path.

    When identifying programs, the path to the program contains information about the program, for example,
    election type, the election or the party. This class contains methods to extract this information from the path.

    When adding a new election type, the extractor should be added to the EXTRACTOR_REFERENCE dictionary and the
    extractor should be implemented as a static method in this class. The extractor should handle the parsing of the
    path for the specific path format. The reference in EXTRACTOR_REFERENCE is to automatically call the correct
    extractor for the election type.

    For example, if the path is .../TK/2017/VVD.pdf, the election type is TK, the election date is 2017 and the party
    is VVD. The election type is always directly after the "manifests" folder in the path. In this specific example,
    the election date is always the second to last folder in the path and the party is always the file name without
    the .pdf extension. So, the output of the extractor should be like this:

    {"election_type": "TK", "election_date": "2017", "party": "VVD"}

    """

    @staticmethod
    def get_election_type(path: str) -> str:
        """Helper method to extract the election type from the path. The election type is always directly after
        the "manifests" folder in the path.

        Arguments:
            path {str} -- The path to the program.

        Raises:
            ValueError: If 'manifests' is not in the path.
            IndexError: If manifest is the last folder in the path.

        Returns:
            str -- The election type.
        """

        # Split the path on the os separator
        split_path = path.split(os.sep)

        # Since the election type is always directly after the "manifests" folder, we can find the election type
        # by finding the index of the "manifests" folder and adding 1 to it
        election_type_index = split_path.index("manifests") + 1

        return split_path[election_type_index]

    @staticmethod
    def extractor_type_date_party(path: str) -> dict[str]:
        """Extract the election type, election date and party from the path.

        The path should be in the following format:
        .../{election_type}/{election_date}/{party}.pdf

        Arguments:
            path {str} -- The path to the program.

        Returns:
            tuple[str, str, str] -- The election type, election date and party.
        """
        # Remove the .pdf extension
        path = path.removesuffix(".pdf")

        # Split the path on the os separator
        split_path = path.split(os.sep)

        return {"election_type": split_path[-3], "election_date": split_path[-2], "party": split_path[-1]}

    # Reference to the methods to extract the information from the path for each election type
    EXTRACTOR_REFERENCE = {"TK": extractor_type_date_party}


def extract_text_pdf(path: str) -> str:
    """Extract the text from a pdf file using pypdf

    Arguments:
        path {str} -- The path to the pdf file.

    Returns:
        str -- The text from the pdf file.
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
        target {str} -- The directory where the programs are stored.

    Returns:
        list[Program] -- A list of programs.
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
        string {str} -- The text to clean.

    Returns:
        str -- The cleaned text.
    """

    string = HYPHENATION.sub("", string)
    string = SPECIAL_CHAR.sub(" ", string)
    string = PAGE_NUM.sub(" ", string)
    string = NEWLINE.sub(" ", string)
    string = TAB.sub(r"\. ", string)
    string = DOUBLE_DOT.sub(r"\. ", string)
    string = FORM_FEED.sub(" ", string)
    string = LARGE_NUMBERS.sub(" ", string)
    string = SINGLE_CHAR.sub(" ", string)
    string = DOUBLE_SPACE.sub(" ", string)

    return string.strip()


def remove_repeating_slogans(text: str, start_size: int | None = None) -> str:
    """Removes repeating slogans from a text. A slogan is a sequence of words that occurs multiple times in the text
    which are not valuable for the analysis. This functions starts with a large snippet size and decreases it until the
    optimal snippet size is found. It checks if the most common snippet occurs often enough to be considered a slogan.
    If it does, it removes all occurrences of it and recursively calls itself to check if there are more slogans.

    Args:
        text {str} -- The text from which the slogans should be removed.

    Keyword Arguments:
        start_size {int} -- The size of the first snippet. Used to do efficient recursion. (default: {None})

    Returns:
        str -- The text without slogans.

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
        print(f"Removed {two_most_common[0][0]}")  # TODO: remove this print statement.

        # Recursively call this function to check if there are more slogans.
        text = remove_repeating_slogans(text, snippet_size - 1)

    return text


def process_all_programs() -> None:
    """Process all programs by retrieving the text from the pdf, creating a doc from the text
    and saving the text and doc to a file.

    Arguments:
        programs {list[Program]} -- A list of programs.
    """
    global programs_processed

    print(f"Will process {len(_programs)} programs")

    for i, p in enumerate(_programs):
        utils.progress(i + 1, len(_programs), p)

        # TODO: suppress and collect stdout and stderr
        p.retrieve_text_from_pdf()
        p.create_doc_from_text()

    # Change variable to true to indicate that all programs have been processed
    # This enables the user to call the get_programs() api
    programs_processed = True
    print("All programs processed, ready for analysis")


def get_programs() -> list[Program]:
    """Return all programs. If the programs have not been processed yet, an exception will be raised.

    Raises:
        Exception: If the programs have not been processed yet.

    Returns:
        list[Program] -- A list of programs.
    """
    if programs_processed:
        raise RuntimeError("Programs have not been processed yet. To process them, run process_all_programs()"
                           " before calling this function.")

    return _programs


# For debugging purposes, set to true to force (re)processing of all programs
FORCE_REPROCESSING = False

# Define regex patterns to clean the parsed text from a pdf file
# TODO: Add more special characters
# TODO: Refine regex patterns
# Matches special characters
SPECIAL_CHAR = re.compile(r'[▶◀·•▪▫▬▭▮▯▰▱◆◇◈◊○◌◍◎●◐◑◒◓◔◕◖◗◘◙◢◣◤◥◦◧◨◩◪◫◬◭◮◯◸◹◺◻◼◽◾◿]')
# Matches newlines inbetween words
NEWLINE = re.compile(r"(?<=\w)\n+(?=\w)")
# Matches multiple spaces
DOUBLE_SPACE = re.compile(r"\s+")
# Matches multiple dots, whitespace is allowed between the dots
DOUBLE_DOT = re.compile(r"\s*\.\s*\.\s*")
# Matches tabs
TAB = re.compile(r"\t")
# Matches page numbers, which is a number surrounded by newlines and possibly spaces on either side
PAGE_NUM = re.compile(r"\n?\s*\d+\s*\n?")
# Matches large numbers, which is a number with potentially spaces between these numbers
# Only matches when digits, spaces and new lines that are 9 characters or longer
LARGE_NUMBERS = re.compile(r"[\d\s\n]{9,}")
# Matches form feeds
FORM_FEED = re.compile(r"\f")
# When hyphenation occurs, one word is split in two and a hyphen is added at
# the end of the first part, however, when extracting the text from the pdf,
# the hyphen should be removed and the two parts should be joined together.
HYPHENATION = re.compile(r"\x02|(?<=\w-)\n(?=\w+)")
# Matches single characters
SINGLE_CHAR = re.compile(r"(?<=\s)\w(?=\s|$)")
SINGLE_CHAR_START = re.compile(r"^\w\s")

# Define paths
directory = os.path.dirname(os.path.realpath(__file__))
project_root = os.path.dirname(directory)
data_path = os.path.join(project_root, "data")
manifest_path = os.path.join(data_path, "manifests")
processed_path = os.path.join(project_root, "processed")
processed_text_path = os.path.join(processed_path, "text")
processed_doc_path = os.path.join(processed_path, "doc")

# Ensure output folders exist
if not os.path.exists(processed_path):
    os.mkdir(processed_path)
if not os.path.exists(processed_text_path):
    os.mkdir(processed_text_path)
if not os.path.exists(processed_doc_path):
    os.mkdir(processed_doc_path)

# Ensure programs have been processed when user calls the get_programs() api
# This variable is set to true when all programs have been processed
programs_processed = False

# Load spacy model
nlp = spacy.load("nl_core_news_lg")

# Add syllables pipe to spacy
# This is necessary for the syllables_count attribute to be available on tokens
# Community package based on
nlp.add_pipe("syllables", after="tagger")

# Get all programs
_programs = identify_programs(manifest_path)


if __name__ == "__main__":
    process_all_programs()
