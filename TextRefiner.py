import re
import html


class TextRefiner:
    def __init__(self, escape=(),stop_at=(),filter_string=(),replacement='[OMITTED]'):
        self.escape = escape
        self.stop_at = stop_at
        self.filter_string = filter_string
        self.replacement = replacement

    def update_settings(self,settings):
        self.escape = settings.get('escape').split(',')
        self.stop_at = settings.get('stop_at').split(',')
        self.filter_string = settings.get('filter_string').split(',')
        self.replacement = settings.get('replacement')

    def cut_text_at_stop(self, text):
        result = text
        if self.stop_at:
            matched_positions = []
            for stop in self.stop_at:
                if stop:
                    match = re.search(re.escape(stop), text)
                    if match:
                        position = match.start()
                        matched_positions.append(position)
                return text[:min(matched_positions)] + "\n\n**由于设置，邮件到此截断**\n\n" if matched_positions else text
        else:
            return text

    def escape_markdown(self,text):
        result = text
        for c in self.escape:
            if c:
                result = result.replace(c,f'\\{c}')
        return result

    def filter_text(self,text):
        result = text
        if self.filter_string:
            for s in self.filter_string:
                if s:
                    result = re.sub(s,self.replacement,result)
        return result

    def refine(self, text):
        refined_text = self.filter_text(self.cut_text_at_stop(self.escape_markdown(text)))
        return refined_text
