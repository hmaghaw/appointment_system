# Email Agent
Whenever the N8N server starts, it can loog credentials or flows in this case, do the following:
- Reload the workflows 
- Get the webhook URL and update it in AWS Secrets Manager
- Reastart the API sever to catch the change