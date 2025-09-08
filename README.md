# Ad Campaign Performance Dashboard

A comprehensive dashboard built with Dash and Plotly for analyzing advertising campaign performance data.

## Features

- **Interactive Filters**: Filter by Store Name, Campaign Status, and Folder Name
- **Real-time KPIs**: Total Ad Sales, Ad Spend, Average ROAS, and Total Orders
- **Multiple Visualizations**:
  - Sales trend over time
  - ROAS distribution histogram
  - Campaign status pie chart
  - Performance scatter plot (Spend vs Sales)
- **Alert System**: Set thresholds and conditions to monitor campaign performance
- **Data Table**: Detailed view of all campaigns with sorting and filtering
- **Slack Integration**: Send alerts directly to Slack channels

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Run the dashboard:
```bash
python app.py
```

3. Open your browser and navigate to `http://localhost:8050`

## Slack Webhook Setup

To enable Slack alerts, follow these steps:

### Step 1: Create a Slack App
1. Go to [https://api.slack.com/apps](https://api.slack.com/apps)
2. Click "Create New App"
3. Choose "From scratch"
4. Enter your app name (e.g., "Ad Campaign Alerts")
5. Select your workspace

### Step 2: Enable Incoming Webhooks
1. In your app settings, go to "Incoming Webhooks"
2. Toggle "Activate Incoming Webhooks" to "On"
3. Click "Add New Webhook to Workspace"
4. Choose the channel where you want to receive alerts
5. Click "Allow"

### Step 3: Get Your Webhook URL
1. Copy the webhook URL (it will look like: `https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX`)
2. Open `app.py`
3. Find the commented section in the `send_alert` function:
```python
# Uncomment and replace with your actual Slack webhook URL
# response = requests.post(
#     "YOUR_SLACK_WEBHOOK_URL_HERE",
#     json=slack_message,
#     timeout=10
# )
```
4. Replace `"YOUR_SLACK_WEBHOOK_URL_HERE"` with your actual webhook URL
5. Uncomment the lines by removing the `#` symbols

### Step 4: Test the Integration
1. Run the dashboard
2. Set up an alert with a threshold
3. Click "Send Alert" to test the Slack integration

## Usage

### Filters
- **Store Name**: Filter campaigns by specific store locations
- **Campaign Status**: Filter by ACTIVE, PAUSED, or other statuses
- **Folder Name**: Filter by campaign periods or categories

### Alert System
1. Select a metric to monitor (Ad Sales, ROAS, etc.)
2. Set a threshold value
3. Choose a condition (greater than, less than, equal to)
4. Click "Send Alert" to check current data against your criteria
5. If conditions are met, an alert will be sent to Slack

### Visualizations
- **Sales Trend**: Shows ad sales performance over different time periods
- **ROAS Distribution**: Histogram showing the distribution of Return on Ad Spend
- **Status Pie Chart**: Breakdown of campaign statuses
- **Performance Scatter**: Relationship between ad spend and sales performance

## Data Structure

The dashboard expects a CSV file named `all_ads.csv` with the following columns:
- Campaign UUID
- Campaign Name
- Store name
- Store address
- Status
- Start Date
- End date
- Timezone
- Audience targeted
- Budget
- Budget currency
- Budget unit
- Ad sales (USD)
- Ad spend (USD)
- ROAS
- Average cost per click (USD)
- Average cost per order (USD)
- Impressions
- Clicks
- Orders
- Click through rate
- Click to order rate
- Average order value (USD)
- folder_name

## Customization

You can customize the dashboard by:
- Modifying colors in the `status_colors` dictionary
- Adding new metrics to the alert system
- Creating additional visualizations
- Adjusting the layout and styling

## Troubleshooting

### Common Issues
1. **Port already in use**: Change the port in `app.run_server(port=8051)`
2. **Slack webhook not working**: Verify the webhook URL and ensure the Slack app has proper permissions
3. **Data not loading**: Ensure `all_ads.csv` is in the same directory as `app.py`

### Support
For issues or questions, please check the Dash documentation: [https://dash.plotly.com/](https://dash.plotly.com/)
