# Slack Integration Setup Guide

## Your Slack App Details
- **App ID**: A09EU16AU1W
- **Client ID**: 1090020357526.9504040368064
- **Client Secret**: 0da48958dbe8108477abe0ad1eb4944b
- **Signing Secret**: 8e79a03a653d07f1962fcb6add56284d
- **Verification Token**: WWCvMwgN0Yt3buEQRJaM5U0Z
- **Target Channel**: #alerts

## Step-by-Step Setup

### 1. Get Your Webhook URL

1. Go to [https://api.slack.com/apps](https://api.slack.com/apps)
2. Find your app "A09EU16AU1W" and click on it
3. In the left sidebar, click on **"Incoming Webhooks"**
4. Toggle **"Activate Incoming Webhooks"** to **"On"**
5. Click **"Add New Webhook to Workspace"**
6. Select the **#alerts** channel
7. Click **"Allow"**
8. Copy the webhook URL (it will look like: `https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX`)

### 2. Update Configuration

1. Open the `slack_config.env` file
2. Replace `YOUR_WEBHOOK_URL_HERE` with your actual webhook URL:
   ```
   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR_ACTUAL_WEBHOOK_URL
   ```

### 3. Test the Integration

1. Install the updated requirements:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the dashboard:
   ```bash
   python app.py
   ```

3. Open your browser to `http://localhost:8050`

4. Scroll down to the "Test Slack Integration" section

5. Click the **"📤 Send Test Alert to Slack"** button

6. Check your #alerts channel in Slack - you should see a test message!

## What the Test Alert Does

When you click the test alert button, it will send a message to your #alerts channel that says:

> 🧪 Test Alert from Ad Campaign Dashboard
> 
> **Dashboard Activity**: Someone visited the dashboard and clicked the test alert button at [timestamp]
> 
> **Dashboard Status**: ✅ Dashboard is working correctly and Slack integration is functional!
> 
> **Next Steps**: You can now set up real alerts using the threshold-based alert system above.

## Troubleshooting

### If the test alert fails:

1. **Check the webhook URL**: Make sure it's correctly copied and pasted in `slack_config.env`
2. **Verify channel permissions**: Ensure your Slack app has permission to post to #alerts
3. **Check the channel exists**: Make sure the #alerts channel exists in your workspace
4. **Restart the dashboard**: After updating the config file, restart the Python app

### Common Error Messages:

- **"Slack webhook URL not configured"**: Update the SLACK_WEBHOOK_URL in slack_config.env
- **"Failed to send alert to Slack"**: Check your webhook URL and channel permissions
- **"Error sending to Slack"**: Network or permission issue - verify your Slack app settings

## Security Notes

- Keep your `slack_config.env` file secure and don't commit it to version control
- The webhook URL is sensitive - treat it like a password
- Consider using environment variables in production instead of the .env file

## Next Steps

Once the test alert works:

1. You can use the threshold-based alert system above to set up real monitoring
2. Set thresholds for metrics like Ad Sales, ROAS, etc.
3. Get notified when campaigns exceed or fall below your defined criteria
4. All alerts will be sent to your #alerts channel with detailed campaign information
