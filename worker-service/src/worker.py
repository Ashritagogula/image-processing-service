import boto3
import json
import time
import os
from PIL import Image, ImageDraw, ImageFont

AWS_ENDPOINT_URL = os.getenv("AWS_ENDPOINT_URL")

s3 = boto3.client(
    "s3",
    endpoint_url=AWS_ENDPOINT_URL,
    aws_access_key_id="test",
    aws_secret_access_key="test",
    region_name="us-east-1"
)

sqs = boto3.client(
    "sqs",
    endpoint_url=AWS_ENDPOINT_URL,
    aws_access_key_id="test",
    aws_secret_access_key="test",
    region_name="us-east-1"
)

RAW_BUCKET = os.getenv("S3_BUCKET_RAW")
PROCESSED_BUCKET = os.getenv("S3_BUCKET_PROCESSED")
QUEUE_URL = os.getenv("SQS_QUEUE_URL")


def process_image(image_id, s3_key):
    local_file = f"/tmp/{image_id}.png"
    processed_file = f"/tmp/{image_id}_thumb.png"

    # download
    s3.download_file(RAW_BUCKET, s3_key, local_file)

    # resize
    img = Image.open(local_file)
    img.thumbnail((150, 150))

    # watermark
    draw = ImageDraw.Draw(img)
    text = "PropelHQ"
    draw.text((10, 130), text)

    img.save(processed_file)

    # upload processed
    s3.upload_file(
        processed_file,
        PROCESSED_BUCKET,
        f"{image_id}_thumbnail.png"
    )


def poll_queue():
    while True:
        print("Polling SQS...")
        response = sqs.receive_message(
            QueueUrl=QUEUE_URL,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=5
        )

        messages = response.get("Messages", [])

        if not messages:
            continue

        for msg in messages:
            try:
                body = json.loads(msg["Body"])
                image_id = body["image_id"]
                s3_key = body["s3_key_raw"]

                print(f"Processing {image_id}")

                process_image(image_id, s3_key)

                # delete message
                sqs.delete_message(
                    QueueUrl=QUEUE_URL,
                    ReceiptHandle=msg["ReceiptHandle"]
                )

                print("Done")

            except Exception as e:
                print("Error:", e)

        time.sleep(2)


if __name__ == "__main__":
    poll_queue()