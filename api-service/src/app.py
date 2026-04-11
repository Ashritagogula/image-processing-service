from flask import Flask, request, jsonify
import uuid
import boto3
import json

app = Flask(__name__)

# AWS LocalStack config
s3 = boto3.client(
    "s3",
    endpoint_url="http://localstack:4566",
    aws_access_key_id="test",
    aws_secret_access_key="test",
    region_name="us-east-1"
)

sqs = boto3.client(
    "sqs",
    endpoint_url="http://localstack:4566",
    aws_access_key_id="test",
    aws_secret_access_key="test",
    region_name="us-east-1"
)

SQS_QUEUE_URL = "http://localstack:4566/000000000000/image-queue"
BUCKET_NAME = "raw-images"

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def home():
    return "API is running 🚀"


@app.route("/images/upload", methods=["POST"])
def upload_image():
    if "image" not in request.files:
        return jsonify({"error": "No image provided"}), 400

    file = request.files["image"]

    if not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type"}), 400

    image_id = str(uuid.uuid4())
    ext = file.filename.split(".")[-1]
    s3_key = f"original/{image_id}.{ext}"

    try:
        # Upload to S3
        s3.upload_fileobj(file, BUCKET_NAME, s3_key)

        # Send message to SQS
        message = {
            "image_id": image_id,
            "s3_key_raw": s3_key
        }

        sqs.send_message(
            QueueUrl=SQS_QUEUE_URL,
            MessageBody=json.dumps(message)
        )

        return jsonify({
            "image_id": image_id,
            "status": "uploaded and queued"
        }), 202

    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route('/images/processed/<image_id>', methods=['GET'])
def get_processed(image_id):
    key = f"{image_id}_thumbnail.png"

    try:
        s3.head_object(Bucket=S3_BUCKET_PROCESSED, Key=key)

        url = s3.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': S3_BUCKET_PROCESSED,
                'Key': key
            },
            ExpiresIn=3600
        )

        return jsonify({"url": url})

    except Exception:
        return jsonify({"error": "Image not found"}), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)