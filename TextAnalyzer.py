import re


class TextAnalyzer:

    def __init__(self, keyword=()):
        self.keyword = keyword
        self.threshold = 1

    def update_settings(self,settings):
        self.keyword = settings.get("keyword").split(',')
        self.threshold = settings.get("keyword_threshold")

    def count_keyword(self, text):
        result = {}
        for word in self.keyword:
            if word:
                occurrence = re.findall(word, text)
                if len(occurrence) >= self.threshold:
                    result[word] = len(occurrence)
        return sum(result.values())
