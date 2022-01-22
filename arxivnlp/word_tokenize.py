from typing import List

from arxivnlp.data.dnm import DnmStr


def word_tokenize(sentence: DnmStr) -> List[DnmStr]:
    words = []
    word_start = 0
    for i in range(len(sentence)):
        if sentence.string[i].isspace():
            if word_start != i:
                words.append(sentence[word_start:i])
            word_start = i + 1
        if sentence.string[i] in {'.', ',', ':', ';', '!', '?', ')', '(', '[', ']', '{', '}', '-', '”', '“'}:
            if word_start != i:
                words.append(sentence[word_start:i])
            words.append(sentence[i])
            word_start = i + 1
    if word_start != len(sentence):
        words.append(sentence[word_start:])
    return words
