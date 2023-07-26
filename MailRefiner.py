import re

class TextRefiner:
    escape = ()
    stop_at = () # regex
    keyword = () # regex
    text = 'If you see this default text, it means you have not read your own text (correctly).'

    class _RefinedText:
        text = ''
        counts = {}
        def __init__(self, text,counts):
            self.text = text
            self.counts = counts

    def __init__(self, escape=(), stop_at=(), keyword=()):
        self.escape = escape
        self.stop_at = stop_at
        self.keyword = keyword

    def read_text(self,text):
        if text:
            self.text = text

    def escape_markdown(self):
        result = self.text
        if self.escape:
            for c in self.escape:
                result.replace(c, f'\\{c}')
        return result

    def cut_text_at_stop(self):
        result = self.text
        if self.stop_at:
            matched_positions = []
            for stop in self.stop_at:
                match = re.search(re.escape(stop),self.text)
                if match:
                    position = match.start()
                    matched_positions.append(position)
            return self.text[:min(matched_positions)] if matched_positions else self.text
        else:
            print('**no stop_at**')
            return self.text

    def count_keyword(self):
        result = {}
        for word in self.keyword:
            occurrence = re.findall(word,self.text)
            if occurrence != 0:
                result[word] = occurrence
        return result

    def refine(self):
        text = self.escape_markdown() | self.cut_text_at_stop
        counts = self.count_keyword()
        return self._RefinedText(text,counts)