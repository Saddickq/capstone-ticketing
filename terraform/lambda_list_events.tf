resource "aws_lambda_function" "list_events" {
  function_name    = "capstone-list-events"
  role             = aws_iam_role.lambda_exec.arn
  handler          = "handler.lambda_handler"
  runtime          = "python3.12"
  filename         = "${path.module}/build/list_events.zip"
  source_code_hash = filebase64sha256("${path.module}/build/list_events.zip")
  timeout          = 10

  environment {
    variables = {
      TABLE_NAME = aws_dynamodb_table.event_registrations.name
    }
  }
}

resource "aws_apigatewayv2_integration" "list_events" {
  api_id                 = aws_apigatewayv2_api.api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.list_events.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "list_events" {
  api_id    = aws_apigatewayv2_api.api.id
  route_key = "GET /events"
  target    = "integrations/${aws_apigatewayv2_integration.list_events.id}"
}

resource "aws_lambda_permission" "list_events_apigw" {
  statement_id  = "AllowAPIGatewayInvokeListEvents"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.list_events.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.api.execution_arn}/*/*"
}