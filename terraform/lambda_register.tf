resource "aws_lambda_function" "register" {
  function_name    = "event-register"
  role             = aws_iam_role.lambda_exec.arn
  handler          = "handler.lambda_handler"
  runtime          = "python3.12"
  filename         = "${path.module}/build/register.zip"
  source_code_hash = filebase64sha256("${path.module}/build/register.zip")
  timeout          = 10

  environment {
    variables = {
      TABLE_NAME = aws_dynamodb_table.event_registrations.name
    }
  }
}