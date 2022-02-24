import requests
from arxivnlp.config import Config


def single_query(content: str) -> str:
    result = requests.get('https://query.wikidata.org/sparql', params={'query': content}, headers={'Accept': 'text/csv'})
    return result.text





# if __name__ == '__main__':
#     import sys
#     for file in sys.argv[1:]:
#         print(file)
#         with open(file) as fp1:
#             with open(file[:-6]+'.csv', 'w') as fp2:
#                 fp2.write(query(fp1.read()))
