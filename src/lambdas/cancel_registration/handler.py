import json
import os
from decimal import Decimal

import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super().default(obj)


def _response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, cls=DecimalEncoder),
    }


def lambda_handler(event, context):
    registration_id = (event.get("pathParameters") or {}).get("id", "").strip()

    if not registration_id or "#" not in registration_id:
        return _response(400, {"error": "A valid registration id is required"})

    event_id = registration_id.split("#", 1)[0]
    pk = f"EVENT#{event_id}"
    sk = f"REG#{registration_id}"

    try:
        # Confirm it exists first
        existing = table.get_item(Key={"PK": pk, "SK": sk}).get("Item")
        if not existing:
            return _response(404, {"error": f"Registration {registration_id} not found"})

        table.delete_item(Key={"PK": pk, "SK": sk})
        return _response(200, {"message": "Registration cancelled", "registration_id": registration_id})
    except ClientError as e:
        return _response(500, {"error": "Could not cancel registration", "detail": str(e)})
