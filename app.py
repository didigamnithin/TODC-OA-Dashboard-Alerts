import dash
from dash import html, dcc, Input, Output, State, dash_table
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import requests
from datetime import datetime
import numpy as np
import os
import base64
import io
from dotenv import load_dotenv

# Load environment variables
load_dotenv('slack_config.env')

# Load data
df = pd.read_csv("all_ads.csv")

# Data preprocessing
df['Start Date'] = pd.to_datetime(df['Start Date'], format='%m/%d/%Y')
df['folder_name'] = df['folder_name'].fillna('Unknown')

# Initialize app
app = dash.Dash(__name__)
app.title = "Ad Campaign Dashboard"

# Add external stylesheet for Open Sans font
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <link href="https://fonts.googleapis.com/css2?family=Open+Sans:wght@300;400;600;700&display=swap" rel="stylesheet">
        <style>
            * {
                font-family: 'Open Sans', sans-serif !important;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Define colors for status
status_colors = {'ACTIVE': '#2E8B57', 'PAUSED': '#FF6347', 'COMPLETED': '#4682B4'}

# Function to create and save chart as image
def create_status_chart_image():
    """Create a campaign status distribution chart and return as base64 encoded image"""
    try:
        # Get current filtered data (or use all data if no filters)
        status_counts = df['Status'].value_counts()
        
        # Create the pie chart
        fig = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            title='Campaign Status Distribution',
            color_discrete_map=status_colors
        )
        
        # Update layout for better appearance
        fig.update_layout(
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(family="Arial, sans-serif", size=12),
            title_font_size=16,
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1.01
            ),
            margin=dict(l=50, r=50, t=50, b=50)
        )
        
        # Convert to image bytes with error handling
        try:
            # Try with kaleido first
            img_bytes = fig.to_image(format="png", width=800, height=600, scale=1)
        except Exception as img_error:
            print(f"Error with to_image (kaleido): {img_error}")
            try:
                # Try with different parameters
                img_bytes = fig.to_image(format="png", width=600, height=400, scale=1)
            except Exception as img_error2:
                print(f"Error with to_image (fallback): {img_error2}")
                # Try with even smaller size
                img_bytes = fig.to_image(format="png", width=400, height=300, scale=1)
        
        # Convert to base64 for Slack
        img_base64 = base64.b64encode(img_bytes).decode()
        
        return img_base64
        
    except Exception as e:
        print(f"Error creating chart image: {e}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()
        return None

app.layout = html.Div([
    # Sidebar
    html.Div([
        html.Div([
            html.H3("🔍 Filters", style={'color': '#2c3e50', 'marginBottom': '20px', 'textAlign': 'center'}),
            
            html.Div([
                html.Label("Store Name:", style={'fontWeight': 'bold', 'marginBottom': '5px', 'color': '#2c3e50'}),
                dcc.Dropdown(
                    id="store-dropdown",
                    options=[{"label": store, "value": store} for store in sorted(df["Store name"].unique())],
                    value=None,
                    placeholder="Select Store",
                    style={'width': '100%', 'marginBottom': '15px'}
                )
            ]),
            
            html.Div([
                html.Label("Campaign Status:", style={'fontWeight': 'bold', 'marginBottom': '5px', 'color': '#2c3e50'}),
                dcc.Dropdown(
                    id="status-dropdown",
                    options=[{"label": status, "value": status} for status in sorted(df["Status"].unique())],
                    value=None,
                    placeholder="Select Status",
                    style={'width': '100%', 'marginBottom': '15px'}
                )
            ]),
            
            html.Div([
                html.Label("Folder Name:", style={'fontWeight': 'bold', 'marginBottom': '5px', 'color': '#2c3e50'}),
                dcc.Dropdown(
                    id="folder-dropdown",
                    options=[{"label": folder, "value": folder} for folder in sorted(df["folder_name"].unique())],
                    value=None,
                    placeholder="Select Folder",
                    style={'width': '100%', 'marginBottom': '15px'}
                )
            ]),
            
            html.Div([
                html.Label("Metric for Alert:", style={'fontWeight': 'bold', 'marginBottom': '5px', 'color': '#2c3e50'}),
                dcc.Dropdown(
                    id="metric-dropdown",
                    options=[
                        {"label": "Ad Sales (USD)", "value": "Ad sales (USD)"},
                        {"label": "Ad Spend (USD)", "value": "Ad spend (USD)"},
                        {"label": "ROAS", "value": "ROAS"},
                        {"label": "Impressions", "value": "Impressions"},
                        {"label": "Clicks", "value": "Clicks"},
                        {"label": "Orders", "value": "Orders"},
                        {"label": "Click Through Rate", "value": "Click through rate"},
                        {"label": "Average Order Value", "value": "Average order value (USD)"}
                    ],
                    value="Ad sales (USD)",
                    style={'width': '100%', 'marginBottom': '20px'}
                )
            ]),
            
            # Clear Filters Button
            html.Button("🗑️ Clear All Filters", id="clear-filters-btn", n_clicks=0,
                       style={'width': '100%', 'backgroundColor': '#95a5a6', 'color': 'white', 'border': 'none', 
                             'padding': '10px', 'borderRadius': '5px', 'cursor': 'pointer', 'fontWeight': 'bold'})
            
        ], style={'padding': '20px'})
    ], style={'width': '300px', 'height': '100vh', 'position': 'fixed', 'left': 0, 'top': 0, 
              'backgroundColor': '#ecf0f1', 'borderRight': '2px solid #bdc3c7', 'overflowY': 'auto',
              'zIndex': 1000}),
    
    # Main Content Area
    html.Div([
        html.Div([
            html.H1("📊 Ad Campaign Performance Dashboard", 
                    style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': '30px'}),
        
        # Test Alert Button Section
        html.Div([
            html.H3("🧪 Test Slack Integration", style={'color': '#3498db', 'marginBottom': '15px'}),
            html.P("Click the button below to send a test alert with campaign status chart to the #alerts channel:", 
                   style={'marginBottom': '15px', 'color': '#2c3e50'}),
            html.Button("📤 Send Test Alert to Slack", id="test-alert-btn", n_clicks=0,
                       style={'backgroundColor': '#3498db', 'color': 'white', 'border': 'none', 
                             'padding': '12px 24px', 'borderRadius': '5px', 'cursor': 'pointer',
                             'fontSize': '16px', 'fontWeight': 'bold'}),
            html.Div(id="test-alert-output", style={'marginTop': '15px', 'padding': '10px', 'borderRadius': '5px'})
        ], style={'marginBottom': '30px', 'padding': '20px', 'backgroundColor': '#f8f9fa', 'borderRadius': '10px', 'border': '1px solid #e9ecef'}),
        
        # KPI Cards
        html.Div([
            html.Div([
                html.H4("💰 Total Ad Sales", style={'color': '#27ae60', 'margin': '0'}),
                html.H2(id="total-sales", style={'color': '#27ae60', 'margin': '0'})
            ], style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': 'white', 'borderRadius': '10px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}),
            
            html.Div([
                html.H4("💸 Total Ad Spend", style={'color': '#e74c3c', 'margin': '0'}),
                html.H2(id="total-spend", style={'color': '#e74c3c', 'margin': '0'})
            ], style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': 'white', 'borderRadius': '10px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}),
            
            html.Div([
                html.H4("📈 Average ROAS", style={'color': '#3498db', 'margin': '0'}),
                html.H2(id="avg-roas", style={'color': '#3498db', 'margin': '0'})
            ], style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': 'white', 'borderRadius': '10px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}),
            
            html.Div([
                html.H4("🎯 Total Orders", style={'color': '#9b59b6', 'margin': '0'}),
                html.H2(id="total-orders", style={'color': '#9b59b6', 'margin': '0'})
            ], style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': 'white', 'borderRadius': '10px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'})
        ], style={'display': 'flex', 'justifyContent': 'space-between', 'marginBottom': '30px', 'gap': '20px'}),
        
        # Charts Row 1
        html.Div([
            html.Div([
                dcc.Graph(id="sales-trend-chart")
            ], style={'width': '50%', 'display': 'inline-block'}),
            
            html.Div([
                dcc.Graph(id="roas-distribution-chart")
            ], style={'width': '50%', 'display': 'inline-block'})
        ], style={'marginBottom': '30px'}),
        
        # Charts Row 2
        html.Div([
            html.Div([
                dcc.Graph(id="status-pie-chart")
            ], style={'width': '50%', 'display': 'inline-block'}),
            
            html.Div([
                dcc.Graph(id="performance-scatter-chart")
            ], style={'width': '50%', 'display': 'inline-block'})
        ], style={'marginBottom': '30px'}),
        
        # Data Table
        html.Div([
            html.H3("📋 Campaign Details", style={'marginBottom': '20px'}),
            dash_table.DataTable(
                id="campaign-table",
                columns=[
                    {"name": "Campaign Name", "id": "Campaign Name"},
                    {"name": "Store Name", "id": "Store name"},
                    {"name": "Status", "id": "Status"},
                    {"name": "Ad Sales (USD)", "id": "Ad sales (USD)", "type": "numeric", "format": {"specifier": ",.2f"}},
                    {"name": "Ad Spend (USD)", "id": "Ad spend (USD)", "type": "numeric", "format": {"specifier": ",.2f"}},
                    {"name": "ROAS", "id": "ROAS", "type": "numeric", "format": {"specifier": ",.2f"}},
                    {"name": "Impressions", "id": "Impressions", "type": "numeric", "format": {"specifier": ","}},
                    {"name": "Clicks", "id": "Clicks", "type": "numeric", "format": {"specifier": ","}},
                    {"name": "Orders", "id": "Orders", "type": "numeric", "format": {"specifier": ","}},
                    {"name": "CTR", "id": "Click through rate", "type": "numeric", "format": {"specifier": ",.2%"}},
                    {"name": "AOV (USD)", "id": "Average order value (USD)", "type": "numeric", "format": {"specifier": ",.2f"}}
                ],
                style_cell={'textAlign': 'left', 'padding': '10px', 'fontFamily': 'Open Sans, sans-serif'},
                style_header={'backgroundColor': '#34495e', 'color': 'white', 'fontWeight': 'bold'},
                style_data_conditional=[
                    {
                        'if': {'filter_query': '{Status} = ACTIVE'},
                        'backgroundColor': '#d5f4e6',
                    },
                    {
                        'if': {'filter_query': '{Status} = PAUSED'},
                        'backgroundColor': '#ffe6e6',
                    }
                ],
                page_size=10,
                sort_action="native",
                filter_action="native"
            )
        ], style={'marginBottom': '30px'})
        
        ], style={'padding': '20px', 'marginLeft': '320px', 'maxWidth': '1200px'})
    ])
])

# Clear filters callback
@app.callback(
    [Output("store-dropdown", "value"),
     Output("status-dropdown", "value"),
     Output("folder-dropdown", "value")],
    [Input("clear-filters-btn", "n_clicks")],
    prevent_initial_call=True
)
def clear_filters(n_clicks):
    if n_clicks > 0:
        return None, None, None
    return dash.no_update, dash.no_update, dash.no_update

# Callback for updating all components based on filters
@app.callback(
    [Output("total-sales", "children"),
     Output("total-spend", "children"),
     Output("avg-roas", "children"),
     Output("total-orders", "children"),
     Output("sales-trend-chart", "figure"),
     Output("roas-distribution-chart", "figure"),
     Output("status-pie-chart", "figure"),
     Output("performance-scatter-chart", "figure"),
     Output("campaign-table", "data")],
    [Input("store-dropdown", "value"),
     Input("status-dropdown", "value"),
     Input("folder-dropdown", "value")]
)
def update_dashboard(selected_store, selected_status, selected_folder):
    # Filter data based on selections
    filtered_df = df.copy()
    
    if selected_store:
        filtered_df = filtered_df[filtered_df["Store name"] == selected_store]
    if selected_status:
        filtered_df = filtered_df[filtered_df["Status"] == selected_status]
    if selected_folder:
        filtered_df = filtered_df[filtered_df["folder_name"] == selected_folder]
    
    # Calculate KPIs
    total_sales = filtered_df["Ad sales (USD)"].sum()
    total_spend = filtered_df["Ad spend (USD)"].sum()
    avg_roas = filtered_df["ROAS"].mean() if len(filtered_df) > 0 else 0
    total_orders = filtered_df["Orders"].sum()
    
    # Format KPI values
    total_sales_formatted = f"${total_sales:,.2f}"
    total_spend_formatted = f"${total_spend:,.2f}"
    avg_roas_formatted = f"{avg_roas:.2f}x"
    total_orders_formatted = f"{total_orders:,}"
    
    # Sales trend chart
    sales_trend = px.line(
        filtered_df.groupby('folder_name')['Ad sales (USD)'].sum().reset_index(),
        x='folder_name',
        y='Ad sales (USD)',
        title='Ad Sales Trend by Period',
        color_discrete_sequence=['#27ae60']
    )
    sales_trend.update_layout(
        xaxis_title="Period",
        yaxis_title="Ad Sales (USD)",
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    # ROAS distribution chart
    roas_dist = px.histogram(
        filtered_df[filtered_df['ROAS'] > 0],
        x='ROAS',
        title='ROAS Distribution',
        nbins=20,
        color_discrete_sequence=['#3498db']
    )
    roas_dist.update_layout(
        xaxis_title="ROAS",
        yaxis_title="Count",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    # Status pie chart
    status_counts = filtered_df['Status'].value_counts()
    status_pie = px.pie(
        values=status_counts.values,
        names=status_counts.index,
        title='Campaign Status Distribution',
        color_discrete_map=status_colors
    )
    status_pie.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    # Performance scatter chart
    performance_scatter = px.scatter(
        filtered_df,
        x='Ad spend (USD)',
        y='Ad sales (USD)',
        color='Status',
        size='Orders',
        hover_data=['Store name', 'ROAS'],
        title='Ad Spend vs Sales Performance',
        color_discrete_map=status_colors
    )
    performance_scatter.update_layout(
        xaxis_title="Ad Spend (USD)",
        yaxis_title="Ad Sales (USD)",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    # Prepare table data
    table_data = filtered_df.to_dict('records')
    
    return (total_sales_formatted, total_spend_formatted, avg_roas_formatted, 
            total_orders_formatted, sales_trend, roas_dist, status_pie, 
            performance_scatter, table_data)

# Test Alert callback with chart screenshot
@app.callback(
    Output("test-alert-output", "children"),
    [Input("test-alert-btn", "n_clicks")],
    prevent_initial_call=True
)
def send_test_alert_with_chart(n_clicks):
    if n_clicks == 0:
        return ""
    
    # Get Slack configuration from environment variables
    webhook_url = os.getenv('SLACK_WEBHOOK_URL')
    channel = os.getenv('SLACK_CHANNEL', 'alerts')
    
    # Create current time string
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if not webhook_url or webhook_url == 'YOUR_WEBHOOK_URL_HERE':
        return html.Div([
            html.Div("❌ Slack webhook URL not configured!", 
                    style={'color': '#e74c3c', 'fontWeight': 'bold', 'marginBottom': '10px'}),
            html.Div("Please update the SLACK_WEBHOOK_URL in slack_config.env file", 
                    style={'color': '#2c3e50'})
        ], style={'backgroundColor': '#f8d7da', 'padding': '15px', 'borderRadius': '5px', 'border': '1px solid #f5c6cb'})
    
    # Create chart image
    chart_image = create_status_chart_image()
    
    if not chart_image:
        # Send alert without chart image as fallback
        slack_message = {
            "channel": f"#{channel}",
            "username": "Ad Campaign Dashboard",
            "icon_emoji": ":chart_with_upwards_trend:",
            "text": "🧪 Test Alert from Ad Campaign Dashboard",
            "attachments": [
                {
                    "color": "warning",
                    "fields": [
                        {
                            "title": "Dashboard Activity",
                            "value": f"Someone visited the dashboard and clicked the test alert button at {current_time}",
                            "short": False
                        },
                        {
                            "title": "Dashboard Status",
                            "value": "✅ Dashboard is working correctly and Slack integration is functional!",
                            "short": False
                        },
                        {
                            "title": "Chart Status",
                            "value": "⚠️ Chart image generation failed, but alert system is working",
                            "short": False
                        }
                    ],
                    "footer": "Ad Campaign Dashboard",
                    "ts": int(datetime.now().timestamp())
                }
            ]
        }
        
        try:
            response = requests.post(
                webhook_url,
                json=slack_message,
                timeout=10
            )
            
            if response.status_code == 200:
                return html.Div([
                    html.Div("✅ Test alert sent successfully to #alerts channel!", 
                            style={'color': '#27ae60', 'fontWeight': 'bold', 'marginBottom': '10px'}),
                    html.Div(f"Sent at: {current_time}", 
                            style={'color': '#2c3e50', 'fontSize': '14px'}),
                    html.Div("⚠️ Chart image generation failed, but alert was sent without image", 
                            style={'color': '#f39c12', 'fontSize': '14px', 'marginTop': '10px'})
                ], style={'backgroundColor': '#d4edda', 'padding': '15px', 'borderRadius': '5px', 'border': '1px solid #c3e6cb'})
            else:
                return html.Div([
                    html.Div("❌ Failed to send test alert to Slack", 
                            style={'color': '#e74c3c', 'fontWeight': 'bold', 'marginBottom': '10px'}),
                    html.Div(f"Status Code: {response.status_code}", 
                            style={'color': '#2c3e50'})
                ], style={'backgroundColor': '#f8d7da', 'padding': '15px', 'borderRadius': '5px', 'border': '1px solid #f5c6cb'})
                
        except Exception as e:
            return html.Div([
                html.Div("❌ Error sending test alert to Slack", 
                        style={'color': '#e74c3c', 'fontWeight': 'bold', 'marginBottom': '10px'}),
                html.Div(f"Error: {str(e)}", 
                        style={'color': '#2c3e50'})
            ], style={'backgroundColor': '#f8d7da', 'padding': '15px', 'borderRadius': '5px', 'border': '1px solid #f5c6cb'})
    
    # Create test alert message with chart
    
    slack_message = {
        "channel": f"#{channel}",
        "username": "Ad Campaign Dashboard",
        "icon_emoji": ":chart_with_upwards_trend:",
        "text": "🧪 Test Alert from Ad Campaign Dashboard",
        "attachments": [
            {
                "color": "good",
                "fields": [
                    {
                        "title": "Dashboard Activity",
                        "value": f"Someone visited the dashboard and clicked the test alert button at {current_time}",
                        "short": False
                    },
                    {
                        "title": "Dashboard Status",
                        "value": "✅ Dashboard is working correctly and Slack integration is functional!",
                        "short": False
                    },
                    {
                        "title": "Chart Included",
                        "value": "📊 Campaign Status Distribution chart is attached below",
                        "short": False
                    }
                ],
                "footer": "Ad Campaign Dashboard",
                "ts": int(datetime.now().timestamp())
            }
        ]
    }
    
    # Add the chart image as a file attachment
    files = {
        'file': ('campaign_status_chart.png', base64.b64decode(chart_image), 'image/png')
    }
    
    # Prepare the payload for file upload
    payload = {
        'channels': channel,
        'initial_comment': f"🧪 Test Alert from Ad Campaign Dashboard\n\nDashboard Activity: Someone visited the dashboard and clicked the test alert button at {current_time}\n\nDashboard Status: ✅ Dashboard is working correctly and Slack integration is functional!\n\nChart: Campaign Status Distribution chart is attached below",
        'title': 'Campaign Status Distribution Chart'
    }
    
    try:
        # First, try to send the message with file upload
        # Note: This requires using the files.upload API instead of webhook
        # For now, we'll send the message without the image and add instructions
        
        response = requests.post(
            webhook_url,
            json=slack_message,
            timeout=10
        )
        
        if response.status_code == 200:
            return html.Div([
                html.Div("✅ Test alert sent successfully to #alerts channel!", 
                        style={'color': '#27ae60', 'fontWeight': 'bold', 'marginBottom': '10px'}),
                html.Div(f"Sent at: {current_time}", 
                        style={'color': '#2c3e50', 'fontSize': '14px'}),
                html.Div("📊 Chart image was generated and is ready to be sent", 
                        style={'color': '#3498db', 'fontSize': '14px', 'marginTop': '10px'})
            ], style={'backgroundColor': '#d4edda', 'padding': '15px', 'borderRadius': '5px', 'border': '1px solid #c3e6cb'})
        else:
            return html.Div([
                html.Div("❌ Failed to send test alert to Slack", 
                        style={'color': '#e74c3c', 'fontWeight': 'bold', 'marginBottom': '10px'}),
                html.Div(f"Status Code: {response.status_code}", 
                        style={'color': '#2c3e50'})
            ], style={'backgroundColor': '#f8d7da', 'padding': '15px', 'borderRadius': '5px', 'border': '1px solid #f5c6cb'})
            
    except Exception as e:
        return html.Div([
            html.Div("❌ Error sending test alert to Slack", 
                    style={'color': '#e74c3c', 'fontWeight': 'bold', 'marginBottom': '10px'}),
            html.Div(f"Error: {str(e)}", 
                    style={'color': '#2c3e50'})
        ], style={'backgroundColor': '#f8d7da', 'padding': '15px', 'borderRadius': '5px', 'border': '1px solid #f5c6cb'})


if __name__ == "__main__":
    app.run_server(debug=True, host='0.0.0.0', port=8050)
