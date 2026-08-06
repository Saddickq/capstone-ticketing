import json
import os
import re
import uuid
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def lambda_handler(event, context):
    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return _response(400, {"error": "Invalid JSON body"})

    event_id = body.get("event_id", "").strip()
    email = body.get("email", "").strip().lower()
    name = body.get("name", "").strip()

    # --- Input validation ---
    if not event_id:
        return _response(400, {"error": "event_id is required"})
    if not email or not EMAIL_RE.match(email):
        return _response(400, {"error": "A valid email is required"})
    if not name:
        return _response(400, {"error": "name is required"})

    # --- Confirm event exists and has capacity ---
    try:
        event_item = table.get_item(
            Key={"PK": f"EVENT#{event_id}", "SK": "METADATA"}
        ).get("Item")
    except ClientError as e:
        return _response(500, {"error": "Could not look up event", "detail": str(e)})

    if not event_item:
        return _response(404, {"error": f"Event {event_id} not found"})

    capacity = event_item.get("capacity")
    if capacity is not None:
        current_count = table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key("PK").eq(f"EVENT#{event_id}")
            & boto3.dynamodb.conditions.Key("SK").begins_with("REG#"),
            Select="COUNT",
        )["Count"]
        if current_count >= capacity:
            return _response(409, {"error": "Event is at full capacity"})

    # --- Prevent duplicate registration (same email, same event) ---
    existing = table.query(
        IndexName="GSI1",
        KeyConditionExpression=boto3.dynamodb.conditions.Key("GSI1PK").eq(f"EMAIL#{email}"),
    )["Items"]
    if any(item["event_id"] == event_id for item in existing):
        return _response(409, {"error": "This email is already registered for this event"})

    # --- Write the registration ---
    registration_id = f"{event_id}#{uuid.uuid4().hex[:8]}"
    now = datetime.now(timezone.utc).isoformat()

    item = {
        "PK": f"EVENT#{event_id}",
        "SK": f"REG#{registration_id}",
        "GSI1PK": f"EMAIL#{email}",
        "GSI1SK": f"REG#{registration_id}",
        "event_id": event_id,
        "registration_id": registration_id,
        "email": email,
        "name": name,
        "status": "confirmed",
        "registered_at": now,
    }

    try:
        table.put_item(Item=item)
    except ClientError as e:
        return _response(500, {"error": "Could not save registration", "detail": str(e)})

    return _response(201, {
        "message": "Registration successful",
        "registration_id": registration_id,
        "event_id": event_id,
        "email": email,
    })
