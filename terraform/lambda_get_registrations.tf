resource "aws_lambda_function" "get_registrations" {
  function_name    = "capstone-get-registrations"
  role             = aws_iam_role.lambda_exec.arn
  handler          = "handler.lambda_handler"
  runtime          = "python3.12"
  filename         = "${path.module}/build/get_registrations.zip"
  source_code_hash = filebase64sha256("${path.module}/build/get_registrations.zip")
  timeout          = 10

  environment {
    variables = {
      TABLE_NAME = aws_dynamodb_table.event_registrations.name
    }
  }
}

resource "aws_apigatewayv2_integration" "get_registrations" {
  api_id                 = aws_apigatewayv2_api.api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.get_registrations.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "get_registrations" {
  api_id    = aws_apigatewayv2_api.api.id
  route_key = "GET /registrations/{email}"
  target    = "integrations/${aws_apigatewayv2_integration.get_registrations.id}"
}

resource "aws_lambda_permission" "get_registrations_apigw" {
  statement_id  = "AllowAPIGatewayInvokeGetRegistrations"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.get_registrations.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.api.execution_arn}/*/*"
}