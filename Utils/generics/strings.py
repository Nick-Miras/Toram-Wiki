class Grams:  # n word grams

    @staticmethod
    def ngrams(string):
        for i in range(1, len(string) + 1):
            yield string[0:i].lower()

    @staticmethod
    def gram(string, n: int):  # incremental
        for i in range(n, len(string) + 1):
            yield string[i - n: i].lower()

    @classmethod
    def trigram(cls, string):  # incremental
        return cls.gram(string, 3)


def remove_underscores(string: str) -> str:
    return ' '.join(string.split('_')).strip()
