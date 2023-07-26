import email
import datetime
import email.utils
from email.header import decode_header

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
        if charset is not None:
            result.append(text.decode(charset))
        else:
            result.append(text)
    return ', '.join(result)

class MyMail:
    charset = 'utf-8'
    file_name = 'DEFAULT'
    subject = 'DEFAULT'
    text = 'DEFAULT'
    from_addr = 'DEFAULT'
    from_name = 'DEFAULT'
    to_addr = 'DEFAULT'
    to_name = 'DEFAULT'
    date = datetime.datetime(2001,10,4) # Just my birthday
    hints = ''

    debug = False

    def __init__(self,path, debug=False):
        self.debug = debug

        def find_plain_part(message):
            if message.is_multipart():
                for part in message.walk():
                    if part.get_content_type() == 'text/plain':
                        return part
            else:
                return message

        with open(path, 'rb') as f:
            if not f.name.endswith('.eml'):
                raise Exception('unexpected file format.')
            self.file_name = f.name
            msg = email.message_from_binary_file(f)

        plain_part = find_plain_part(msg)
        self.charset = plain_part.get_content_charset()
        self.text = plain_part.get_payload(decode=True).decode(self.charset, errors='ignore')
        self.from_name = get_decoded_metadata(email.utils.parseaddr(msg['From'])[0])
        self.from_addr = get_decoded_metadata(email.utils.parseaddr(msg['From'])[1])
        self.to_name = get_decoded_metadata(email.utils.parseaddr(msg['To'])[0])
        self.to_addr = get_decoded_metadata(email.utils.parseaddr(msg['To'])[1])
        self.date = email.utils.parsedate_to_datetime(msg['Date'])
        self.subject = get_decoded_metadata(msg['Subject'])

        if has_attachment(msg):
            self.hints += f'** 这封邮件包含一个及以上的附件，你可以打开“{self.file_name}”检查。 **\n** This E-Mail has an attachment or more. You may want to check it(them) by opening the file {self.file_name} ** \n'

    def __to_string(self):
        result = ''
        result += f"{self.hints}\n" \
                  f"Subject: {self.subject}\n" \
                  f"From: {self.from_name} <{self.from_addr}>\n" \
                  f"To: {self.to_name} <{self.to_addr}>\n" \
                  f"Datetime: {self.date.strftime('%Y-%m-%d %H:%M:%S  %Z')}\n\n" \
                  f"{self.text}\n"
        if self.debug:
            result += f"[DEBUG]Charset: {self.charset}"
        return result

    def __str__(self):
        return self.__to_string()

    def __repr__(self):
        return self.__to_string()