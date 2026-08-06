import json
import os
import sys
import boto3
import pytest
from moto import mock_aws

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src/lambdas/register"))


@pytest.fixture
def dynamodb_table(monkeypatch):
    with mock_aws():
        monkeypatch.setenv("TABLE_NAME", "TestEventRegistrations")
        client = boto3.resource("dynamodb", region_name="us-east-1")
        table = client.create_table(
            TableName="TestEventRegistrations",
            KeySchema=[
                {"AttributeName": "PK", "KeyType": "HASH"},
                {"AttributeName": "SK", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "PK", "AttributeType": "S"},
                {"AttributeName": "SK", "AttributeType": "S"},
                {"AttributeName": "GSI1PK", "AttributeType": "S"},
                {"AttributeName": "GSI1SK", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[{
                "IndexName": "GSI1",
                "KeySchema": [
                    {"AttributeName": "GSI1PK", "KeyType": "HASH"},
                    {"AttributeName": "GSI1SK", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            }],
            BillingMode="PAY_PER_REQUEST",
        )
        table.put_item(Item={
            "PK": "EVENT#101", "SK": "METADATA",
            "name": "Test Event", "capacity": 5,
        })
        yield table


def test_register_success(dynamodb_table):
    import handler
    handler.table = dynamodb_table  # rebind after moto patched the env
    event = {"body": json.dumps({"event_id": "101", "email": "a@b.com", "name": "A"})}
    resp = handler.lambda_handler(event, None)
    assert resp["statusCode"] == 201
    body = json.loads(resp["body"])
    assert body["email"] == "a@b.com"


def test_register_missing_email(dynamodb_table):
    import handler
    handler.table = dynamodb_table
    event = {"body": json.dumps({"event_id": "101", "name": "A"})}
    resp = handler.lambda_handler(event, None)
    assert resp["statusCode"] == 400


def test_register_duplicate(dynamodb_table):
    import handler
    handler.table = dynamodb_table
    event = {"body": json.dumps({"event_id": "101", "email": "a@b.com", "name": "A"})}
    handler.lambda_handler(event, None)
    resp = handler.lambda_handler(event, None)
    assert resp["statusCode"] == 409


def test_register_event_not_found(dynamodb_table):
    import handler
    handler.table = dynamodb_table
    event = {"body": json.dumps({"event_id": "999", "email": "a@b.com", "name": "A"})}
    resp = handler.lambda_handler(event, None)
    assert resp["statusCode"] == 404