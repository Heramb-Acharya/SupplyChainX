# Alarm when EC2 CPU utilization remains above 70%
resource "aws_cloudwatch_metric_alarm" "high_cpu" {
  alarm_name          = "SupplyChainX-High-CPU"
  alarm_description   = "CPU utilization exceeds 70% for 10 minutes"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = 300
  statistic           = "Average"
  threshold           = 70

  dimensions = {
    InstanceId = aws_instance.supplychainx.id
  }

  treat_missing_data = "notBreaching"
}

# Alarm when EC2 instance status checks fail
resource "aws_cloudwatch_metric_alarm" "instance_status" {
  alarm_name          = "SupplyChainX-Instance-Status-Failure"
  alarm_description   = "EC2 instance status check has failed"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 2
  metric_name         = "StatusCheckFailed"
  namespace           = "AWS/EC2"
  period              = 300
  statistic           = "Maximum"
  threshold           = 1

  dimensions = {
    InstanceId = aws_instance.supplychainx.id
  }

  treat_missing_data = "notBreaching"
}

# SupplyChainX CloudWatch dashboard
resource "aws_cloudwatch_dashboard" "supplychainx" {
  dashboard_name = "SupplyChainX-Monitoring"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6

        properties = {
          title  = "EC2 CPU Utilization"
          region = var.aws_region
          period = 300
          metrics = [
            ["AWS/EC2", "CPUUtilization", "InstanceId", aws_instance.supplychainx.id]
          ]
          stat = "Average"
          view = "timeSeries"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6

        properties = {
          title  = "EC2 Network Traffic"
          region = var.aws_region
          period = 300
          metrics = [
            ["AWS/EC2", "NetworkIn", "InstanceId", aws_instance.supplychainx.id],
            ["AWS/EC2", "NetworkOut", "InstanceId", aws_instance.supplychainx.id]
          ]
          stat = "Sum"
          view = "timeSeries"
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6

        properties = {
          title  = "EC2 Status Checks"
          region = var.aws_region
          period = 300
          metrics = [
            ["AWS/EC2", "StatusCheckFailed", "InstanceId", aws_instance.supplychainx.id]
          ]
          stat = "Maximum"
          view = "timeSeries"
          yAxis = {
            left = {
              min = 0
              max = 1
            }
          }
        }
      }
    ]
  })
}
