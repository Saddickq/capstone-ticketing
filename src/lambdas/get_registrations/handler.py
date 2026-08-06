import json
import os
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key

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
    email = (event.get("pathParameters") or {}).get("email", "").strip().lower()

    if not email:
        return _response(400, {"error": "email path parameter is required"})

    try:
        resp = table.query(
            IndexName="GSI1",
            KeyConditionExpression=Key("GSI1PK").eq(f"EMAIL#{email}"),
        )
        items = resp.get("Items", [])

        registrations = [
            {
                "registration_id": item["registration_id"],
                "event_id": item["event_id"],
                "status": item.get("status"),
                "registered_at": item.get("registered_at"),
            }
            for item in items
        ]
        return _response(200, {"email": email, "registrations": registrations, "count": len(registrations)})
    except Exception as e:
        return _response(500, {"error": "Could not fetch registrations", "detail": str(e)})
