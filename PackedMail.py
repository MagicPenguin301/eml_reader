import copy
import datetime
import email
import email.utils
from email.header import decode_header
import pytz
import os

from TextAnalyzer import TextAnalyzer
from TextRefiner import TextRefiner

def get_error_message(code):
    with open('ErrorMessage.txt','r',encoding='utf-8') as f:
        for line in f.readlines():
            err_code, err_msg = line.split('|')
            if err_code == code:
                return err_msg
        return f'Unknown error code {code}'


def has_attachment(msg):
    has = False
    for part in msg.walk():
        if part.get('Content-Disposition') and 'attachment' in part['Content-Disposition']:
            has = True
            break
    return has


def get_decoded_metadata(encoded):
    decoded = decode_header(encoded)
    result = []
    for text, charset in decoded:
        try:
            if charset is not None:
                result.append(text.decode(charset))
            else:
                result.append(text)
        except UnicodeDecodeError:
            result.append(text)
    return ', '.join(result)


class PackedMail:
    charset = 'utf-8'
    file_name = 'DEFAULT'
    subject = 'DEFAULT'
    text = 'DEFAULT'
    from_addr = 'DEFAULT'
    from_name = 'DEFAULT'
    to_addr = 'DEFAULT'
    to_name = 'DEFAULT'
    date = pytz.utc.localize(datetime.datetime(1970,1,1, 12, 0, 0) ) # Just my birthday
    hints = {}
    error = 0
    debug = False

    def __init__(self, path, debug=False):
        self.debug = debug
        self.hints = {}
        def find_plain_part(message):
            if message.is_multipart():
                for part in message.walk():
                    if part.get_content_type() == 'text/plain':
                        return part
            else:
                return message

        with open(path, 'rb') as f:
            if not f.name.endswith('.eml'):
                raise Exception(f"unexpected file format \"{f.name.split('.')[1]}\" in the zip file.")
            self.file_name = os.path.split(f.name)[-1]
            # self.file_name = f.name.split('\/')[-1] if '\/' in f.name else f.name
            msg = email.message_from_binary_file(f)
        plain_part = find_plain_part(msg)
        try:
            self.charset = plain_part.get_content_charset()
            self.text = plain_part.get_payload(decode=True).decode(self.charset, errors='ignore')
            self.from_name = get_decoded_metadata(email.utils.parseaddr(msg['From'])[0])
            self.from_addr = get_decoded_metadata(email.utils.parseaddr(msg['From'])[1])
            self.to_name = get_decoded_metadata(email.utils.parseaddr(msg['To'])[0])
            self.to_addr = get_decoded_metadata(email.utils.parseaddr(msg['To'])[1])
            self.date = email.utils.parsedate_to_datetime(msg['Date'])
            self.subject = get_decoded_metadata(msg['Subject'])
        except (AttributeError, TypeError):
            self.error = '001'
        if not self.error and has_attachment(msg):
            self.hints['Attachment Warning'] = f'{self.file_name} 含有附件'


    def use_refiner(self, refiner: TextRefiner):
        if not self.error:
            self.text = refiner.refine(self.text)

    def use_analyzer(self, analyzer: TextAnalyzer):
        if not self.error:
            self.hints['Keyword Count'] = analyzer.count_keyword(self.text)

    def __to_string(self):
        if not self.error:
            result = ''
            for key in self.hints:
                if self.hints[key]:
                    result += f"**{key}: {self.hints[key]}**\n\n"
            result += f"Subject: {self.subject}\n\n" \
                      f"From: {self.from_name} <{self.from_addr}>\n\n" \
                      f"To: {self.to_name} <{self.to_addr}>\n\n" \
                      f"Datetime: {self.date.strftime('%Y-%m-%d %H:%M:%S  %Z')}\n\n\n\n" \
                      f"{self.text}\n\n"
            if self.debug:
                result += f"[DEBUG]Charset: {self.charset}"
        else:
            result = f"<p style='font-weight: bold; color: red;'>解析失败：{self.file_name}</p>" + get_error_message(self.error)
        return result


    def __str__(self):
        return self.__to_string()

    def __repr__(self):
        return self.__to_string()
