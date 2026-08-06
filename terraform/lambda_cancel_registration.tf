resource "aws_lambda_function" "cancel_registration" {
  function_name    = "capstone-cancel-registration"
  role             = aws_iam_role.lambda_exec.arn
  handler          = "handler.lambda_handler"
  runtime          = "python3.12"
  filename         = "${path.module}/build/cancel_registration.zip"
  source_code_hash = filebase64sha256("${path.module}/build/cancel_registration.zip")
  timeout          = 10

  environment {
    variables = {
      TABLE_NAME = aws_dynamodb_table.event_registrations.name
    }
  }
}

resource "aws_apigatewayv2_integration" "cancel_registration" {
  api_id                 = aws_apigatewayv2_api.api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.cancel_registration.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "cancel_registration" {
  api_id    = aws_apigatewayv2_api.api.id
  route_key = "DELETE /registration/{id}"
  target    = "integrations/${aws_apigatewayv2_integration.cancel_registration.id}"
}

resource "aws_lambda_permission" "cancel_registration_apigw" {
  statement_id  = "AllowAPIGatewayInvokeCancelRegistration"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.cancel_registration.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.api.execution_arn}/*/*"
}