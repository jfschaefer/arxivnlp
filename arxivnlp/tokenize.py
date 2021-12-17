from typing import List
from arxivnlp.data.dnm import SubString

def sentence_tokenize(substring: SubString) -> List[SubString]:
    sentences = []
    sent_start = 0
    for i in range(len(substring)):
        if substring.string[i] == '.':
            sentences.append(substring[sent_start:i+1].strip().normalize_spaces())
            sent_start = i+1
    return sentences