""" Module that contains the functions to analyze the data.

Classes:
    - Absolute: Class that contains the absolute metrics.
    - Relative: Class that contains the relative metrics.

"""
from spacy.tokens import Doc, Token

from src.constants import CHARACTERS_PER_PAGES


class Absolute:
    """ Class that contains the absolute metrics,
    which are the metrics that are not relative to the length of the text.

    Methods:
        - number_of_pages: Calculates the number of pages in a given text.
        - number_of_sentences: Calculates the number of sentences in a given text.
        - number_of_words: Calculates the number of words in a given text.
        - number_of_characters: Calculates the number of characters in a given text.
        - number_of_syllables: Calculates the number of syllables in a given text.
        - number_of_nouns: Calculates the number of nouns in a given text.
        - number_of_verbs: Calculates the number of verbs in a given text.
        - number_of_unique_words: Calculates the number of unique words in a given text.
        - number_of_complex_words: Calculates the number of complex words in a given text.
        - number_of_pronouns: Calculates the number of pronouns in a given text.
        - number_of_prepositions: Calculates the number of prepositions in a given text.
        - tree_depth: Calculates the tree depth of a given text.

    """
    @staticmethod
    def number_of_pages(doc: Doc) -> int:
        """
        Calculates the number of pages in a given text.

        Args:
            doc (Doc): The spacy doc for which the number of pages should be calculated.

        Returns:
            int: The number of pages.
        """

        number_of_characters = Absolute.number_of_characters(doc)
        # If the number of characters is not divisible by the number of characters per page, add a page.
        add_page = 1 if number_of_characters % CHARACTERS_PER_PAGES else 0

        return number_of_characters // CHARACTERS_PER_PAGES + add_page

    @staticmethod
    def number_of_sentences(doc: Doc) -> int:
        """
        Calculates the number of sentences in a given text.

        Args:
            doc (Doc): The spacy doc for which the number of sentences should be calculated.

        Returns:
            int: The number of sentences.
        """

        return len(list(doc.sents))

    @staticmethod
    def number_of_words(doc: Doc) -> int:
        """
        Calculates the number of words in a given text.

        Args:
            doc (Doc): The spacy doc for which the number of words should be calculated.

        Returns:
            int: The number of words.
        """

        return len([token for token in doc if token.is_alpha])

    @staticmethod
    def number_of_characters(doc: Doc) -> int:
        """
        Calculates the number of characters in a given text.

        Args:
            doc (Doc): The spacy doc for which the number of characters should be calculated.

        Returns:
            int: The number of characters.
        """

        return len([char for char in doc.text if char.isalpha()])

    @staticmethod
    def number_of_syllables(doc: Doc) -> int:
        """
        Calculates the number of syllables in a given text.

        Args:
            doc (Doc): The spacy doc for which the number of syllables should be calculated.

        Returns:
            int: The number of syllables.
        """

        return sum(token._.syllables_count for token in doc if token.is_alpha)

    @staticmethod
    def number_of_nouns(doc: Doc) -> int:
        """
        Calculates the number of nouns in a given text.

        Args:
            doc (Doc): The spacy doc for which the number of nouns should be calculated.

        Returns:
            int: The number of nouns.
        """

        return len([token for token in doc if token.pos_ == "NOUN"])

    @staticmethod
    def number_of_verbs(doc: Doc) -> int:
        """
        Calculates the number of verbs in a given text.

        Args:
            doc (Doc): The spacy doc for which the number of verbs should be calculated.

        Returns:
            int: The number of verbs.
        """

        return len([token for token in doc if token.pos_ == "VERB"])

    @staticmethod
    def number_of_unique_words(doc: Doc) -> int:
        """
        Calculates the number of unique words in a given text.

        Args:
            doc (Doc): The spacy doc for which the number of unique words should be calculated.

        Returns:
            int: The number of unique words.
        """

        return len({token.text for token in doc if token.is_alpha})

    @staticmethod
    def number_of_complex_words(doc: Doc) -> int:
        """
        Calculates the number of complex words in a given text.

        Args:
            doc (Doc): The spacy doc for which the number of complex words should be calculated.

        Returns:
            int: The number of complex words.
        """

        return len([token for token in doc if token.is_alpha and token._.syllables_count > 2])

    @staticmethod
    def number_of_pronouns(doc: Doc) -> int:
        """
        Calculates the number of pronouns in a given text.

        Args:
            doc (Doc): The spacy doc for which the number of pronouns should be calculated.

        Returns:
            int: The number of pronouns.
        """

        return len([token for token in doc if token.pos_ == "PRON"])

    @staticmethod
    def number_of_prepositions(doc: Doc) -> int:
        """
        Calculates the number of prepositions in a given text.

        Args:
            doc (Doc): The spacy doc for which the number of prepositions should be calculated.

        Returns:
            int: The number of prepositions.
        """

        return len([token for token in doc if token.pos_ == "ADP"])

    @staticmethod
    def tree_depth(doc: Doc) -> int:
        """
        Calculates the tree depth of a given text.

        Args:
            doc (Doc): The spacy doc for which the tree depth should be calculated.

        Returns:
            int: The tree depth.
        """

        def walk_tree(node: Token, depth: int) -> int:
            """ Walks the tree and calculate the depth of the tree.

            Based on: https://stackoverflow.com/a/64605146/11083222

            Args:
                node (Token): The current node.
                depth (int): The current depth of the tree.

            Returns:
                int: The depth of the tree.
            """
            if node.n_lefts + node.n_rights > 0:
                return max(walk_tree(child, depth + 1) for child in node.children)

            return depth

        return sum(walk_tree(sent.root, 0) for sent in doc.sents)



class Relative:
    """ Class that contains the relative metrics,
    which are the metrics that are relative to the length of the text.

    Methods:
        - number_of_sentences_per_page: Calculates the number of sentences per page for a given text.
        - average_words_per_sentence: Calculates the average number of words per sentence for a given text.
        - average_characters_per_sentence: Calculates the average number of characters per word for a given text.
        - average_syllables_per_sentence: Calculates the average number of syllables per sentence for a given text.
        - average_syllables_per_word: Calculates the average number of syllables per word for a given text.
        - average_of_nouns_per_sentence: Calculates the average number of nouns per sentence for a given text.
        - average_of_verbs_per_sentence: Calculates the average number of verbs per sentence for a given text.
        - average_tree_depth_per_sentence: Calculates the average tree depth per sentence for a given text.
    """

    @staticmethod
    def number_of_sentences_per_page(doc: Doc) -> float:
        """
        Calculates the number of sentences per page for a given text.

        Args:
            doc (Doc): The spacy doc for which the number of sentences per page should be calculated.

        Returns:
            float: The number of sentences per page.
        """

        return Absolute.number_of_sentences(doc) / Absolute.number_of_pages(doc)

    @staticmethod
    def average_words_per_sentence(doc: Doc) -> float:
        """
        Calculates the average number of words per sentence for a given text.

        Args:
            doc (Doc): The spacy doc for which the average number of words per sentence should be calculated.

        Returns:
            float: The average number of words per sentence.
        """

        return Absolute.number_of_words(doc) / Absolute.number_of_sentences(doc)

    @staticmethod
    def average_characters_per_sentence(doc: Doc) -> float:
        """
        Calculates the average number of characters per word for a given text.

        Args:
            doc (Doc): The spacy doc for which the average number of characters per word should be calculated.

        Returns:
            float: The average number of characters per word.
        """

        return Absolute.number_of_characters(doc) / Absolute.number_of_sentences(doc)

    @staticmethod
    def average_syllables_per_sentence(doc: Doc) -> float:
        """
        Calculates the average number of syllables per sentence for a given text.

        Args:
            doc (Doc): The spacy doc for which the average number of syllables per sentence should be calculated.

        Returns:
            float: The average number of syllables per sentence.
        """

        return Absolute.number_of_syllables(doc) / Absolute.number_of_sentences(doc)

    @staticmethod
    def average_syllables_per_word(doc: Doc) -> float:
        """
        Calculates the average number of syllables per word for a given text.

        Args:
            doc (Doc): The spacy doc for which the average number of syllables per word should be calculated.

        Returns:
            float: The average number of syllables per word.
        """

        return Absolute.number_of_syllables(doc) / Absolute.number_of_words(doc)

    @staticmethod
    def average_of_nouns_per_sentence(doc: Doc) -> float:
        """
        Calculates the average number of nouns per sentence for a given text.

        Args:
            doc (Doc): The spacy doc for which the average number of nouns per sentence should be calculated.

        Returns:
            float: The average number of nouns per sentence.
        """

        return Absolute.number_of_nouns(doc) / Absolute.number_of_sentences(doc)

    @staticmethod
    def average_of_verbs_per_sentence(doc: Doc) -> float:
        """
        Calculates the average number of verbs per sentence for a given text.

        Args:
            doc (Doc): The spacy doc for which the average number of verbs per sentence should be calculated.

        Returns:
            float: The average number of verbs per sentence.
        """

        return Absolute.number_of_verbs(doc) / Absolute.number_of_sentences(doc)

    @staticmethod
    def average_tree_depth_per_sentence(doc: Doc) -> float:
        """
        Calculates the average tree depth per sentence for a given text.

        Args:
            doc (Doc): The spacy doc for which the average tree depth per sentence should be calculated.

        Returns:
            float: The average tree depth per sentence.
        """
        return Absolute.tree_depth(doc) / Absolute.number_of_sentences(doc)
