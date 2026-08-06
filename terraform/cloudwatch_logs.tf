resource "aws_cloudwatch_log_group" "register" {
  name              = "/aws/lambda/${aws_lambda_function.register.function_name}"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "list_events" {
  name              = "/aws/lambda/${aws_lambda_function.list_events.function_name}"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "get_registrations" {
  name              = "/aws/lambda/${aws_lambda_function.get_registrations.function_name}"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "cancel_registration" {
  name              = "/aws/lambda/${aws_lambda_function.cancel_registration.function_name}"
  retention_in_days = 14
}