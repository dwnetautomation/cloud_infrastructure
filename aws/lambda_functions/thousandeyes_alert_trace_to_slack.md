# thousandeyes_alert_trace_to_slack

AWS Lambda function that acts on webhook alert from Thousand Eyes via AWS API Gateway.
-Secondary API calls are made to the Thousand Eyes API to get alert detail and trace info.
-Final result of alert trace, the hop where loss is occuring, is formatted and sent to a slack alert channel.
