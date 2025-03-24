import boto3
from botocore.exceptions import ClientError
import settings  # Needed to import env variables when running like this

SENDER = "Arkad No Reply <no-reply@arkadtlth.se>"
AWS_REGION = "eu-north-1"
CHARSET: str = "UTF-8"  # The character encoding for the email.

# Create a new SES resource and specify a region.
client = boto3.client("ses", region_name=AWS_REGION)


def send_mail(recipient_email: str, body_html: str, body_text: str, subject: str):
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

if __name__ == "__main__":
    send_mail("ludvig@llindholm.com", "hello", "hello", "hello")
