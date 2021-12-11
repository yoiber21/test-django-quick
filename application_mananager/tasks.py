""" coding=utf-8 """
import csv
from datetime import datetime
import io

# Send mail
import smtplib

# Email body
import email, smtplib, ssl

from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from django.db import connection, transaction, IntegrityError, ProgrammingError
from celery import shared_task
import pandas as pd

from contextlib import closing
from .models import Client


@shared_task
def clients_upload(client_data):
    """
        Carga de clientes
    """
    subject = "Report"
    body = "Client report"
    sender_email = "yoiberbeitar@gmail.com"
    receiver_email = "yoiberrenteria@gmail.com"
    password = "1001032661"

    # Create a multipart message and set headers
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject
    message["Bcc"] = receiver_email  # Recommended for mass emails

    # Add body to email
    message.attach(MIMEText(body))

    encoding = 'utf-8'
    list_data_success = []
    list_data_arch = []
    list_data_exists = []
    writer_file = io.StringIO()
    writer_file_invalid = io.StringIO()

    data_row_invalid = {"descripcion": "No se creo el cliente"}

    client_data = pd.read_json(client_data)
    for data in client_data.itertuples():
        with transaction.atomic():
            with closing(connection.cursor()) as cursor:
                try:
                    cursor.execute("""INSERT INTO client (document, first_name, last_name, email ) VALUES 
                    (%s,%s,%s,%s) ON CONFLICT (document) DO NOTHING RETURNING document""",
                                   (str(data.document), str(data.first_name), str(data.last_name), str(data.email)))
                except IntegrityError as err:
                    print('Error')
                try:
                    row = cursor.fetchone()
                    list_data_success.append(str(row))
                    list_data_arch.append(str(data.document))
                except ProgrammingError as err:
                    pass

    total_not_success = list(set(list_data_arch).difference(set(list_data_success)))
    print(list_data_success)
    print(f'created {list_data_success}'.center(50, '-'))
    total_created = len(list_data_success)
    total_not_created = len(total_not_success)
    header = ["document"]
    filename = f"{datetime.now()}.csv"  # In same directory as script
    print(f'Not created {total_not_success}'.center(50, '-'))

    # if total_not_created:
    #     with open(f'{filename}', 'w', encoding='UTF8') as f:
    #         # writer = csv.DictWriter(writer_file_invalid, fieldnames=['document'])
    #         # writer.writeheader()
    #         # for i in total_not_success:
    #
    #         writer = csv.writer(f)
    #         # data_row_invalid['document'] = i
    #         # writer.writerow(data_row_invalid)
    #         writer.writerow(header)
    #         writer.writerow(total_not_success)
    #         # content = writer_file_invalid.getvalue()
    #         # content = content.encode(encoding)
    #
    # # pd.to_csv("archv_test.csv")
    #
    # # Open CSV file in binary mode
    # with open(filename, "rb") as attachment:
    #     # Add file as application/octet-stream
    #     # Email client can usually download this automatically as attachment
    #     part = MIMEBase("application", "octet-stream")
    #     part.set_payload(attachment.read())
    #
    # # Encode file in ASCII characters to send by email
    # encoders.encode_base64(part)
    #
    # # Add header as key/value pair to attachment part
    # part.add_header(
    #     "Content-Disposition",
    #     f"attachment; filename= {filename}",
    # )
    #
    # # Add attachment to message and convert message to string
    # message.attach(part)
    # text = message.as_string()
    #
    # # Log in to server using secure context and send email
    # context = ssl.create_default_context()
    # with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
    #     server.login(sender_email, password)
    #     server.sendmail(sender_email, receiver_email, text)

    return True
