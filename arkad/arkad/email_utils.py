import logging

import boto3  # type: ignore[import-untyped]
from botocore.exceptions import ClientError  # type: ignore[import-untyped]

from arkad.settings import DEBUG

SENDER = "Arkad No Reply <no-reply@arkadtlth.se>"
AWS_REGION = "us-west-2"
CHARSET: str = "UTF-8"  # The character encoding for the email.

# Create a new SES resource and specify a region.
client = boto3.client("ses", region_name=AWS_REGION)


def send_mail(
    recipient_email: str, body_html: str, body_text: str, subject: str
) -> None:
    try:
        client.send_email(
            Destination={
                "ToAddresses": [
                    recipient_email,
                ],
            },
            Message={
                "Body": {
                    "Html": {
                        "Charset": CHARSET,
                        "Data": body_html,
                    },
                    "Text": {
                        "Charset": CHARSET,
                        "Data": body_text,
                    },
                },
                "Subject": {
                    "Charset": CHARSET,
                    "Data": subject,
                },
            },
            Source=SENDER,
        )
    except ClientError as e:
        print(e.response["Error"]["Message"])
        raise e
    except Exception as e:
        if DEBUG:
            logging.error(e)
        else:
            logging.error("An error occurred while sending the email.")
            raise e


if __name__ == "__main__":
    send_mail("ludvig@llindholm.com", "hello", "hello", "hello")
