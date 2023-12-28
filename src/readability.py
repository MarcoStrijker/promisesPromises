import collections

import numpy as np

from spacy.tokens import Doc


def flesch_douma_index(doc: Doc) -> float:  # noqa: C901
    """
    Calculates the Flesch-Douma index for a given text.

    Formula:
        Flesch-Douma = 206.835 - (1.015 x gemiddelde zinslengte) - (84.6 x gemiddelde woordlengte)

    Args:
        doc {Doc} -- The spacy doc for which the Flesch-Douma index should be calculated.

    Returns:
        float: The Flesch-Douma index.
    """

    # Calculate the average sentence length
    avg_sentence_length = average_sentence_length(doc)
    avg_syllables_per_word = average_syllables_per_word(doc)

    # Calculate the Flesch-Douma index
    return 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)


def average_sentence_length(doc: Doc) -> float:
    """
    Calculates the average sentence length for a given text.

    Args:
        doc {Doc} -- The spacy doc for which the average sentence length should be calculated.

    Returns:
        float: The average sentence length.
    """

    return np.mean([len(sent) for sent in doc.sents])


def average_word_length(doc: Doc) -> float:
    """
    Calculates the average word length for a given text.

    Args:
        doc {Doc} -- The spacy doc for which the average word length should be calculated.

    Returns:
        float: The average word length.
    """

    return np.mean([len(token) for token in doc if token.is_alpha])


def average_syllables_per_word(doc: Doc) -> float:
    """
    Calculates the average number of syllables per word for a given text.

    Args:
        doc {Doc} -- The spacy doc for which the average number of syllables per word should be calculated.

    Returns:
        float: The average number of syllables per word.
    """

    return np.mean([token._.syllables_count for token in doc if token.is_alpha])


def average_syllables_per_sentence(doc: Doc) -> float:
    """
    Calculates the average number of syllables per sentence for a given text.

    Args:
        doc {Doc} -- The spacy doc for which the average number of syllables per sentence should be calculated.

    Returns:
        float: The average number of syllables per sentence.
    """

    return np.mean([sum([token._.syllables_count for token in sent if token.is_alpha]) for sent in doc.sents])


def average_words_per_sentence(doc: Doc) -> float:
    """
    Calculates the average number of words per sentence for a given text.

    Args:
        doc {Doc} -- The spacy doc for which the average number of words per sentence should be calculated.

    Returns:
        float: The average number of words per sentence.
    """

    return np.mean([len(sent) for sent in doc.sents])


def entropy(doc: Doc) -> float:
    """
    Calculates the entropy for a given text. The entropy is a measure of the
    amount of information contained in a text. The higher the entropy, the
    more unique words are used.

    Formula:
        Entropy = - sum(p_i * log(p_i))

    Args:
        doc {Doc} -- The spacy doc for which the entropy should be calculated.

    Returns:
        float: The entropy.
    """

    # Calculate the relative frequency of each word
    words = [token.text for token in doc if token.is_alpha]
    c = collections.Counter(words)
    relative_freq = {word: c[word] / len(words) for word in c}

    # Calculate the entropy
    # See: https://www.princeton.edu/~wbialek/rome/refs/shannon_51.pdf
    return -sum(relative_freq[word] * np.log2(relative_freq[word]) for word in relative_freq)
