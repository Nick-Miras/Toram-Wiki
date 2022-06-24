class Grams:  # n word grams

    @staticmethod
    def ngrams(string):
        for i in range(1, len(string) + 1):
            yield string[0:i].lower()

    @staticmethod
    def gram(string, n: int):  # incremental
        """create grams of length n from string"""
        for i in range(len(string) - n + 1):
            yield string[i:i + n].lower()

    @classmethod
    def trigram(cls, string):
        return cls.gram(string, 3)


def remove_underscores(string: str) -> str:
    """replace underscores from a string with whitespace if it does not start with an underscore"""
    if string.startswith("_"):
        return string
    return string.replace("_", " ")
