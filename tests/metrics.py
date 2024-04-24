"""This module contains the tests for the metrics module.

It uses
"""

import os

import pytest  # type: ignore
import spacy

from spacy_syllables import SpacySyllables  # type: ignore # import is necessary for spacy to recognize the pipe

from src.metrics import Absolute, Relative


# Get the directory of the current file
test_dir = os.path.dirname(__file__)

# Load spacy model
nlp = spacy.load("nl_core_news_lg")

# Add syllables pipe to spacy
# This is necessary for the syllables_count attribute to be available on tokens
# Community package based on
nlp.add_pipe("syllables", after="tagger")


# Get the example text
example_1_path = os.path.join(test_dir, "Paard van Troje.txt")

with open(example_1_path, "r") as file:
    doc_1 = nlp(file.read())


def test_number_of_pages():
    assert Absolute.number_of_pages(doc_1) == 1


def test_number_of_sentences():
    assert Absolute.number_of_sentences(doc_1) == 5


def test_number_of_words():
    assert Absolute.number_of_words(doc_1) == 82


def test_number_of_characters():
    assert Absolute.number_of_characters(doc_1) == 455


def test_number_of_syllables():
    assert Absolute.number_of_syllables(doc_1) == 149


def test_number_of_nouns():
    assert Absolute.number_of_nouns(doc_1) == 13


def test_number_of_verbs():
    assert Absolute.number_of_verbs(doc_1) == 13


def test_number_of_unique_words():
    assert Absolute.number_of_unique_words(doc_1) == 63


def test_number_of_complex_words():
    assert Absolute.number_of_complex_words(doc_1) == 18


def test_number_of_pronouns():
    assert Absolute.number_of_pronouns(doc_1) == 6


def test_number_of_prepositions():
    assert Absolute.number_of_prepositions(doc_1) == 15


def test_tree_depth():
    assert Absolute.tree_depth(doc_1) == 18


def number_of_sentences_per_page():
    assert Relative.number_of_sentences_per_page(doc_1) == 5


def average_words_per_sentence():
    assert Relative.average_words_per_sentence(doc_1) == (82 / 5)


def average_characters_per_sentence():
    assert Relative.average_characters_per_sentence(doc_1) == (455 / 5)


def average_syllables_per_sentence():
    assert Relative.average_syllables_per_sentence(doc_1) == (150 / 5)


def average_syllables_per_word():
    assert Relative.average_syllables_per_word(doc_1) == (150 / 82)


def average_of_nouns_per_sentence():
    assert Relative.average_of_nouns_per_sentence(doc_1) == (13 / 5)


def average_of_verbs_per_sentence():
    assert Relative.average_of_verbs_per_sentence(doc_1) == (13 / 5)


def average_tree_depth_per_sentence():
    assert Relative.average_tree_depth_per_sentence(doc_1) == (18 / 5)
