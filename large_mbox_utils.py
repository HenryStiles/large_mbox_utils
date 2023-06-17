import email
import re
import sys


# A custom "Mbox" iterator for large Mailboxes.  The Python iterator builds a
# table of contents before processing the box which can be much slower.
class MboxIterator:
    def __init__(self, file_path):
        self.file_path = file_path

    def __iter__(self):
        self.file = open(self.file_path, 'rb')
        self.last_pos = self.file.tell()
        return self
    
    def __next__(self):
        self.file.seek(self.last_pos)
        # performance improvement, a simple string and concatenation is
        # significantly slower than a bytearray
        chunk = bytearray()
        for line in self.file:
            if line.startswith(b'From ') and chunk:
                self.last_pos = self.file.tell() - len(line)
                return email.message_from_bytes(chunk)
            chunk.extend(line)
        if chunk:
            self.last_pos = self.file.tell()
            return email.message_from_bytes(chunk)
        else:
            self.file.close()
            raise StopIteration

# search mbox file for a pattern.
def search_mbox(mbox_path, search_pattern, ignore_case=True):

    pattern = re.compile(search_pattern, re.IGNORECASE if ignore_case else 0)

    for msg in MboxIterator(mbox_path):
        match_found = False
        # check pattern in headers
        for header, value in msg.items():
            if pattern.search(str(value)):
                match_found = True
                print(f'Found match in header: {header}: {value}')

        if not match_found:
            # handling multipart messages
            if msg.is_multipart():
                for part in msg.get_payload():
                    # if the part is text/plain, we search for the pattern
                    if part.get_content_type() == 'text/plain':
                        if pattern.search(part.get_payload()):
                            match_found = True
                            print(f'Found match in message:\n{part.get_payload()}')
            else:
                # if it is not multipart, directly search in the payload.
                if pattern.search(msg.get_payload()):
                    match_found = True
                    print(f'Found match in message:\n{msg.get_payload()}')

        # if a match was found, print the entire header and message
        if match_found:
            print(f'\nEntire header and message for matched email:\n{"-"*50}')
            print(f'Subject: {msg["subject"]}')
            print(f'From: {msg["from"]}')
            print(f'Date: {msg["date"]}')
            if msg.is_multipart():
                for part in msg.get_payload():
                    if part.get_content_type() == 'text/plain':
                        print(part.get_payload())
            else:
                print(msg.get_payload())
            print("-"*50)

# one line summary for all emails
def extract_one_line_summary(mbox_path):   
    for message in MboxIterator(mbox_path):
        print("%s\t%s\t%s" % (message['From'], message['Subject'], message['Date']))

# extract email addresses from mbox file.        
def extract_addresses(mbox_filename):
    for message in MboxIterator(mbox_filename):
        # Extract addresses from 'From', 'To', 'Cc' and 'Bcc' fields.
        for header in ['from', 'to', 'cc', 'bcc']:
            if message[header]:
                for display_name, addr in email.utils.getaddresses([message[header]]):
                    print(f"{display_name} <{addr}>")
