resource "aws_cloudwatch_metric_alarm" "register_error_rate" {
  alarm_name          = "capstone-register-error-rate-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  threshold           = 5  # percent
  metric_query {
    id          = "error_rate"
    expression  = "(errors / invocations) * 100"
    label       = "Error rate (%)"
    return_data = true
  }
  metric_query {
    id = "errors"
    metric {
      metric_name = "Errors"
      namespace   = "AWS/Lambda"
      period      = 300
      stat        = "Sum"
      dimensions = {
        FunctionName = aws_lambda_function.register.function_name
      }
    }
  }
  metric_query {
    id = "invocations"
    metric {
      metric_name = "Invocations"
      namespace   = "AWS/Lambda"
      period      = 300
      stat        = "Sum"
      dimensions = {
        FunctionName = aws_lambda_function.register.function_name
      }
    }
  }
  alarm_description  = "Triggers when register Lambda error rate exceeds 5% over 5 minutes"
  treat_missing_data = "notBreaching"
}