from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import mimetypes
import re
import smtplib
import sys
from time import localtime, strftime
import yaml

def get_config(config_path):
    try:
        with open(config_path, 'r') as config_file:
            config = yaml.load(config_file.read())
    except:
        print("Error: Check config file")
        exit()
    return config

def get_lines(path):
    with open(path) as input:
        content = input.readlines()

    sentences = []
    for line in content:
        sentence = line.split('>', 2)
        if len(sentence) == 3:
            sentences.append(sentence)

    return sentences

def search_lines(obj, label, sentences):
    collection = []

    for sentence in sentences:
        try:
            if obj in sentence[2]:
                uri = re.search('<(.*)', sentence[0])
                for statement in sentences:
                    if (sentence[0] in statement[0]) and (label in statement[1]):
                        name = re.search('"(.*)"', statement[2])
                        collection.append([uri.group(1), name.group(1)])
        except IndexError as e:
            print(sentence)
            exit()

    return collection

def create_message(pubs, publishers, journals, authors):
    message = ''
    message += 'New publications: \n'
    for pub in pubs:
        message += (pub[1] + '    --    ' + pub[0] + '\n')
    message += '\n\nNew publishers: \n'
    for publisher in publishers:
        message += (publisher[1] + '    --    ' + publisher[0] + '\n')
    message += '\n\nNew journals: \n'
    for journal in journals:
        message += (journal[1] + '    --    ' + journal[0] + '\n')
    message += '\n\nNew people: \n'
    for author in authors:
        message += (author[1] + '    --    ' + author[0] + '\n')

    with open('test.txt', 'w') as msg:
        msg.write(message)
    return message

def create_email(message, config, pub_num):
    body = '''
Hello UF VIVO Community,

{} publications have been added to VIVO. The publications are from the most recent import of data from Clarivate's Web of Science. The titles of the new publications are attached, along with new publishers, journals, and people.

Regards,
The CTSIT VIVO Team
\n\n
'''.format(pub_num)
    #message = preamble + message
    #message = preamble
    with open('uploads.txt', 'w') as upload_log:
        upload_log.write(message)
    fileToSend = 'uploads.txt'

    msg = MIMEMultipart()
    msg['From'] = config.get('from_email')
    msg['Subject'] = config.get('subject')

    to_list = config.get('to_emails')
    to_string = ",".join(to_list)
    msg['To'] = to_string

    msg.attach(MIMEText(body, 'plain'))

    ctype, encoding = mimetypes.guess_type(fileToSend)
    if ctype is None or encoding is not None:
        ctype = "application/octet-stream"

    maintype, subtype = ctype.split("/", 1)

    if maintype == "text":
        fp = open(fileToSend)
        attachment = MIMEText(fp.read(), _subtype=subtype)
        fp.close()

    attachment.add_header("Content-Disposition", "attachment", filename=fileToSend)
    msg.attach(attachment)

    return msg

def connect_to_smtp(host, port):
    try:
        connection = smtplib.SMTP(host=host,
                                  port=port,)
        connection.starttls()
        login = raw_input("Enter your gatorlink: ")
        password = raw_input("Enter your password: ")
        connection.login(login, password)
    except smtplib.SMTPConnectError as e:
        print(e)
        connection = None

    return connection

def send_message(msg, connection, config):
    connection.sendmail(config.get('from_email'), config.get('to_emails'), msg.as_string())
    connection.quit()

def main(vivo_path):
    config = get_config('config.yaml')
    pub = 'http://purl.org/ontology/bibo/AcademicArticle'
    publisher = 'http://vivoweb.org/ontology/core#Publisher'
    journal = 'http://purl.org/ontology/bibo/Journal'
    person = 'http://xmlns.com/foaf/0.1/Person'
    label = 'http://www.w3.org/2000/01/rdf-schema#label'

    #pubs
    pb_path = vivo_path + 'pub_add.rdf'
    pb_sentences = get_lines(pb_path)
    pubs = search_lines(pub, label, pb_sentences)

    #publishers
    pl_path = vivo_path + 'publisher_add.rdf'
    pl_sentences = get_lines(pl_path)
    publishers = search_lines(publisher, label, pl_sentences)

    #journals
    j_path = vivo_path + 'journal_add.rdf'
    j_sentences = get_lines(j_path)
    journals = search_lines(journal, label, j_sentences)

    #authors
    au_path = vivo_path + 'author_add.rdf'
    au_sentences = get_lines(au_path)
    authors = search_lines(person, label, au_sentences)

    #logging
    timestamp = strftime("%Y-%m-%d_%H-%M-%S", localtime())
    log_file = 'logs/' + timestamp + '.txt'
    message = create_message(pubs, publishers, journals, authors)
    with open(log_file, 'w') as output:
        output.write(message)

    #send message
    connection = connect_to_smtp(config.get('host'), config.get('port'))
    msg = create_email(message, config, len(pubs))
    send_message(msg, connection, config)


if __name__ == '__main__':
    main(sys.argv[1])


