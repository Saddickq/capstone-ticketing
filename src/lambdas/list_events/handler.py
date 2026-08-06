import json
import os
from decimal import Decimal
import boto3
from boto3.dynamodb.conditions import Attr

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
    try:
        items = []
        scan_kwargs = {"FilterExpression": Attr("SK").eq("METADATA")}
        while True:
            resp = table.scan(**scan_kwargs)
            items.extend(resp.get("Items", []))
            if "LastEvaluatedKey" not in resp:
                break
            scan_kwargs["ExclusiveStartKey"] = resp["LastEvaluatedKey"]

        events = [
            {
                "event_id": item["PK"].replace("EVENT#", ""),
                "name": item.get("name"),
                "date": item.get("date"),
                "location": item.get("location"),
                "capacity": item.get("capacity"),
            }
            for item in items
        ]
        return _response(200, {"events": events, "count": len(events)})
    except Exception as e:
        return _response(500, {"error": "Could not list events", "detail": str(e)})
