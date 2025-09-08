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

# Load data from Excel file
print("📊 Loading data from BearFamilyRestaurants.xlsx...")

# Load Marketing data
df_marketing = pd.read_excel("BearFamilyRestaurants.xlsx", sheet_name="Marketing_promo")
print(f"✅ Loaded Marketing data: {df_marketing.shape[0]} rows, {df_marketing.shape[1]} columns")

# Load Financials data  
df_financials = pd.read_excel("BearFamilyRestaurants.xlsx", sheet_name="Financials")
print(f"✅ Loaded Financials data: {df_financials.shape[0]} rows, {df_financials.shape[1]} columns")

# Data preprocessing for Marketing data
df_marketing['Date'] = pd.to_datetime(df_marketing['Date'])
df_marketing['Campaign start date'] = pd.to_datetime(df_marketing['Campaign start date'])
df_marketing['Campaign end date'] = pd.to_datetime(df_marketing['Campaign end date'])

# Data preprocessing for Financials data
df_financials['Timestamp UTC date'] = pd.to_datetime(df_financials['Timestamp UTC date'])
df_financials['Payout date'] = pd.to_datetime(df_financials['Payout date'])

# Create combined dataset for dashboard
df = df_marketing.copy()  # Use marketing data as primary dataset

# Initialize app
app = dash.Dash(__name__)
app.title = "Bear Family Restaurants - Marketing & Financial Dashboard"

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

# Function to get campaign status summary
def get_campaign_status_summary():
    """Get a text summary of campaign performance"""
    try:
        total_sales = df_marketing['Sales'].sum()
        total_orders = df_marketing['Orders'].sum()
        avg_roas = df_marketing['ROAS'].mean()
        campaign_counts = df_marketing['Campaign'].value_counts()
        
        summary = f"📊 Marketing Campaign Summary:\n"
        summary += f"Total Sales: ${total_sales:,.2f}\n"
        summary += f"Total Orders: {total_orders:,}\n"
        summary += f"Average ROAS: {avg_roas:.2f}x\n\n"
        summary += f"Campaign Distribution:\n"
        
        for campaign, count in campaign_counts.items():
            percentage = (count / len(df_marketing)) * 100
            summary += f"• {campaign}: {count} records ({percentage:.1f}%)\n"
        
        return summary
        
    except Exception as e:
        print(f"Error creating status summary: {e}")
        return "📊 Marketing Campaign Summary: Unable to generate summary"

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
                html.Label("Campaign Type:", style={'fontWeight': 'bold', 'marginBottom': '5px', 'color': '#2c3e50'}),
                dcc.Dropdown(
                    id="campaign-type-dropdown",
                    options=[{"label": campaign_type, "value": campaign_type} for campaign_type in sorted(df["Campaign"].unique())],
                    value=None,
                    placeholder="Select Campaign Type",
                    style={'width': '100%', 'marginBottom': '15px'}
                )
            ]),
            
            html.Div([
                html.Label("Promotion Type:", style={'fontWeight': 'bold', 'marginBottom': '5px', 'color': '#2c3e50'}),
                dcc.Dropdown(
                    id="promotion-type-dropdown",
                    options=[{"label": promo_type, "value": promo_type} for promo_type in sorted(df["Type of promotion"].unique())],
                    value=None,
                    placeholder="Select Promotion Type",
                    style={'width': '100%', 'marginBottom': '15px'}
                )
            ]),
            
            html.Div([
                html.Label("Metric for Alert:", style={'fontWeight': 'bold', 'marginBottom': '5px', 'color': '#2c3e50'}),
                dcc.Dropdown(
                    id="metric-dropdown",
                    options=[
                        {"label": "Sales", "value": "Sales"},
                        {"label": "Orders", "value": "Orders"},
                        {"label": "ROAS", "value": "ROAS"},
                        {"label": "Average Order Value", "value": "Average order value"},
                        {"label": "Marketing Fees", "value": "Marketing fees | (including any applicable taxes)"},
                        {"label": "Blended Marketing", "value": "Blended Marketing"},
                        {"label": "Total Customers Acquired", "value": "Total customers acquired"}
                    ],
                    value="Sales",
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
            html.H1("🍔 Bear Family Restaurants - Marketing & Financial Dashboard", 
                    style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': '30px'}),
        
        # Test Alert Button Section
        html.Div([
            html.H3("🧪 Test Slack Integration", style={'color': '#3498db', 'marginBottom': '15px'}),
            html.P("Click the button below to send a test alert with campaign status summary to the #alerts channel:", 
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
                html.H4("💰 Total Sales", style={'color': '#27ae60', 'margin': '0'}),
                html.H2(id="total-sales", style={'color': '#27ae60', 'margin': '0'})
            ], style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': 'white', 'borderRadius': '10px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}),
            
            html.Div([
                html.H4("📊 Marketing Campaign Performance", style={'color': '#3498db', 'margin': '0'}),
                html.H2(id="marketing-performance", style={'color': '#3498db', 'margin': '0'})
            ], style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': 'white', 'borderRadius': '10px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}),
            
            html.Div([
                html.H4("💵 Payout Profitability", style={'color': '#e74c3c', 'margin': '0'}),
                html.H2(id="payout-profitability", style={'color': '#e74c3c', 'margin': '0'})
            ], style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': 'white', 'borderRadius': '10px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}),
            
            html.Div([
                html.H4("📈 WoW Sales Growth", style={'color': '#9b59b6', 'margin': '0'}),
                html.H2(id="wow-growth", style={'color': '#9b59b6', 'margin': '0'})
            ], style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': 'white', 'borderRadius': '10px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'})
        ], style={'display': 'flex', 'justifyContent': 'space-between', 'marginBottom': '30px', 'gap': '20px'}),
        
        # Additional Growth Metrics
        html.Div([
            html.Div([
                html.H4("📅 MoM Sales Growth", style={'color': '#f39c12', 'margin': '0'}),
                html.H2(id="mom-growth", style={'color': '#f39c12', 'margin': '0'})
            ], style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': 'white', 'borderRadius': '10px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}),
            
            html.Div([
                html.H4("🗓️ YoY Sales Growth", style={'color': '#8e44ad', 'margin': '0'}),
                html.H2(id="yoy-growth", style={'color': '#8e44ad', 'margin': '0'})
            ], style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': 'white', 'borderRadius': '10px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'})
        ], style={'display': 'flex', 'justifyContent': 'center', 'marginBottom': '30px', 'gap': '20px', 'maxWidth': '600px', 'margin': '0 auto 30px auto'}),
        
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
            html.H3("📋 Marketing Campaign Details", style={'marginBottom': '20px'}),
            dash_table.DataTable(
                id="campaign-table",
                columns=[
                    {"name": "Date", "id": "Date", "type": "datetime"},
                    {"name": "Store Name", "id": "Store name"},
                    {"name": "Campaign", "id": "Campaign"},
                    {"name": "Promotion Type", "id": "Type of promotion"},
                    {"name": "Orders", "id": "Orders", "type": "numeric", "format": {"specifier": ","}},
                    {"name": "Sales ($)", "id": "Sales", "type": "numeric", "format": {"specifier": ",.2f"}},
                    {"name": "ROAS", "id": "ROAS", "type": "numeric", "format": {"specifier": ",.2f"}},
                    {"name": "AOV ($)", "id": "Average order value", "type": "numeric", "format": {"specifier": ",.2f"}},
                    {"name": "Marketing Fees ($)", "id": "Marketing fees | (including any applicable taxes)", "type": "numeric", "format": {"specifier": ",.2f"}}
                ],
                style_cell={'textAlign': 'left', 'padding': '10px', 'fontFamily': 'Open Sans, sans-serif'},
                style_header={'backgroundColor': '#34495e', 'color': 'white', 'fontWeight': 'bold'},
                style_data_conditional=[
                    {
                        'if': {'filter_query': '{Campaign} = Corporate'},
                        'backgroundColor': '#d5f4e6',
                    },
                    {
                        'if': {'filter_query': '{Campaign} = Self Serve'},
                        'backgroundColor': '#e6f3ff',
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
     Output("campaign-type-dropdown", "value"),
     Output("promotion-type-dropdown", "value")],
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
     Output("marketing-performance", "children"),
     Output("payout-profitability", "children"),
     Output("wow-growth", "children"),
     Output("mom-growth", "children"),
     Output("yoy-growth", "children"),
     Output("sales-trend-chart", "figure"),
     Output("roas-distribution-chart", "figure"),
     Output("status-pie-chart", "figure"),
     Output("performance-scatter-chart", "figure"),
     Output("campaign-table", "data")],
    [Input("store-dropdown", "value"),
     Input("campaign-type-dropdown", "value"),
     Input("promotion-type-dropdown", "value")]
)
def update_dashboard(selected_store, selected_campaign_type, selected_promotion_type):
    # Filter marketing data based on selections
    filtered_marketing = df_marketing.copy()
    
    if selected_store:
        filtered_marketing = filtered_marketing[filtered_marketing["Store name"] == selected_store]
    if selected_campaign_type:
        filtered_marketing = filtered_marketing[filtered_marketing["Campaign"] == selected_campaign_type]
    if selected_promotion_type:
        filtered_marketing = filtered_marketing[filtered_marketing["Type of promotion"] == selected_promotion_type]
    
    # Filter financials data based on store selection
    filtered_financials = df_financials.copy()
    if selected_store:
        filtered_financials = filtered_financials[filtered_financials["Store name"] == selected_store]
    
    # Calculate KPIs
    total_sales = filtered_marketing["Sales"].sum()
    total_orders = filtered_marketing["Orders"].sum()
    avg_roas = filtered_marketing["ROAS"].mean() if len(filtered_marketing) > 0 else 0
    total_marketing_fees = filtered_marketing["Marketing fees | (including any applicable taxes)"].sum()
    
    # Marketing Campaign Performance (ROAS)
    marketing_performance = f"{avg_roas:.2f}x ROAS"
    
    # Payout Profitability (from financials data)
    total_payout = filtered_financials["Net total"].sum() if len(filtered_financials) > 0 else 0
    payout_profitability = f"${total_payout:,.2f}"
    
    # Growth calculations
    current_date = pd.Timestamp.now()
    
    # Week over Week Growth
    current_week = filtered_marketing[filtered_marketing['Date'] >= current_date - pd.Timedelta(days=7)]['Sales'].sum()
    previous_week = filtered_marketing[(filtered_marketing['Date'] >= current_date - pd.Timedelta(days=14)) & 
                                     (filtered_marketing['Date'] < current_date - pd.Timedelta(days=7))]['Sales'].sum()
    wow_growth = ((current_week - previous_week) / previous_week * 100) if previous_week > 0 else 0
    
    # Month over Month Growth
    current_month = filtered_marketing[filtered_marketing['Date'] >= current_date - pd.Timedelta(days=30)]['Sales'].sum()
    previous_month = filtered_marketing[(filtered_marketing['Date'] >= current_date - pd.Timedelta(days=60)) & 
                                      (filtered_marketing['Date'] < current_date - pd.Timedelta(days=30))]['Sales'].sum()
    mom_growth = ((current_month - previous_month) / previous_month * 100) if previous_month > 0 else 0
    
    # Year over Year Growth
    current_year = filtered_marketing[filtered_marketing['Date'] >= current_date - pd.Timedelta(days=365)]['Sales'].sum()
    previous_year = filtered_marketing[(filtered_marketing['Date'] >= current_date - pd.Timedelta(days=730)) & 
                                     (filtered_marketing['Date'] < current_date - pd.Timedelta(days=365))]['Sales'].sum()
    yoy_growth = ((current_year - previous_year) / previous_year * 100) if previous_year > 0 else 0
    
    # Format KPI values
    total_sales_formatted = f"${total_sales:,.2f}"
    wow_growth_formatted = f"{wow_growth:+.1f}%"
    mom_growth_formatted = f"{mom_growth:+.1f}%"
    yoy_growth_formatted = f"{yoy_growth:+.1f}%"
    
    # Sales trend chart by date
    daily_sales = filtered_marketing.groupby('Date')['Sales'].sum().reset_index()
    sales_trend = px.line(
        daily_sales,
        x='Date',
        y='Sales',
        title='Sales Trend Over Time',
        color_discrete_sequence=['#27ae60']
    )
    sales_trend.update_layout(
        xaxis_title="Date",
        yaxis_title="Sales ($)",
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    # ROAS distribution chart
    roas_dist = px.histogram(
        filtered_marketing[filtered_marketing['ROAS'] > 0],
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
    
    # Campaign type pie chart
    campaign_counts = filtered_marketing['Campaign'].value_counts()
    status_pie = px.pie(
        values=campaign_counts.values,
        names=campaign_counts.index,
        title='Campaign Type Distribution',
        color_discrete_sequence=['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6']
    )
    status_pie.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    # Performance scatter chart
    performance_scatter = px.scatter(
        filtered_marketing,
        x='Marketing fees | (including any applicable taxes)',
        y='Sales',
        color='Campaign',
        size='Orders',
        hover_data=['Store name', 'ROAS'],
        title='Marketing Spend vs Sales Performance',
        color_discrete_sequence=['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6']
    )
    performance_scatter.update_layout(
        xaxis_title="Marketing Fees ($)",
        yaxis_title="Sales ($)",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    # Prepare table data with relevant columns
    table_columns = ['Date', 'Store name', 'Campaign', 'Type of promotion', 'Orders', 'Sales', 
                    'ROAS', 'Average order value', 'Marketing fees | (including any applicable taxes)']
    table_data = filtered_marketing[table_columns].to_dict('records')
    
    return (total_sales_formatted, marketing_performance, payout_profitability, 
            wow_growth_formatted, mom_growth_formatted, yoy_growth_formatted,
            sales_trend, roas_dist, status_pie, performance_scatter, table_data)

# Test Alert callback with text message only
@app.callback(
    Output("test-alert-output", "children"),
    [Input("test-alert-btn", "n_clicks")],
    prevent_initial_call=True
)
def send_test_alert(n_clicks):
    if n_clicks == 0:
        return ""
    
    print("🚀 Starting webhook test alert process...")
    
    # Get Slack configuration from environment variables
    webhook_url = os.getenv('SLACK_WEBHOOK_URL')
    channel = os.getenv('SLACK_CHANNEL', 'alerts')
    
    print(f"📋 Webhook URL configured: {'Yes' if webhook_url and webhook_url != 'YOUR_WEBHOOK_URL_HERE' else 'No'}")
    print(f"📋 Target channel: #{channel}")
    
    # Create current time string
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"📋 Alert timestamp: {current_time}")
    
    if not webhook_url or webhook_url == 'YOUR_WEBHOOK_URL_HERE':
        print("❌ Webhook URL not configured properly")
        return html.Div([
            html.Div("❌ Slack webhook URL not configured!", 
                    style={'color': '#e74c3c', 'fontWeight': 'bold', 'marginBottom': '10px'}),
            html.Div("Please update the SLACK_WEBHOOK_URL in slack_config.env file", 
                    style={'color': '#2c3e50'})
        ], style={'backgroundColor': '#f8d7da', 'padding': '15px', 'borderRadius': '5px', 'border': '1px solid #f5c6cb'})
    
    # Get campaign status summary
    status_summary = get_campaign_status_summary()
    print("📊 Generated campaign status summary")
    
    # Create test alert message with text only
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
                        "title": "Campaign Summary",
                        "value": status_summary,
                        "short": False
                    }
                ],
                "footer": "Ad Campaign Dashboard",
                "ts": int(datetime.now().timestamp())
            }
        ]
    }
    
    print("📤 Preparing to send webhook request...")
    print(f"📤 Webhook URL: {webhook_url[:50]}...")
    print(f"📤 Message payload prepared")
    
    try:
        print("🌐 Sending HTTP POST request to Slack webhook...")
        response = requests.post(
            webhook_url,
            json=slack_message,
            timeout=10
        )
        
        print(f"📡 HTTP Response received:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Response Headers: {dict(response.headers)}")
        print(f"   Response Text: {response.text}")
        
        if response.status_code == 200:
            print("✅ Webhook sent successfully!")
            return html.Div([
                html.Div("✅ Test alert sent successfully to #alerts channel!", 
                        style={'color': '#27ae60', 'fontWeight': 'bold', 'marginBottom': '10px'}),
                html.Div(f"Sent at: {current_time}", 
                        style={'color': '#2c3e50', 'fontSize': '14px'}),
                html.Div(f"Status Code: {response.status_code}", 
                        style={'color': '#27ae60', 'fontSize': '14px', 'marginTop': '5px'}),
                html.Div("📊 Campaign status summary included in message", 
                        style={'color': '#3498db', 'fontSize': '14px', 'marginTop': '10px'})
            ], style={'backgroundColor': '#d4edda', 'padding': '15px', 'borderRadius': '5px', 'border': '1px solid #c3e6cb'})
        else:
            print(f"❌ Webhook failed with status code: {response.status_code}")
            print(f"❌ Response: {response.text}")
            return html.Div([
                html.Div("❌ Failed to send test alert to Slack", 
                        style={'color': '#e74c3c', 'fontWeight': 'bold', 'marginBottom': '10px'}),
                html.Div(f"Status Code: {response.status_code}", 
                        style={'color': '#2c3e50', 'marginBottom': '5px'}),
                html.Div(f"Response: {response.text}", 
                        style={'color': '#2c3e50', 'fontSize': '12px'})
            ], style={'backgroundColor': '#f8d7da', 'padding': '15px', 'borderRadius': '5px', 'border': '1px solid #f5c6cb'})
            
    except requests.exceptions.Timeout:
        print("❌ Webhook request timed out")
        return html.Div([
            html.Div("❌ Webhook request timed out", 
                    style={'color': '#e74c3c', 'fontWeight': 'bold', 'marginBottom': '10px'}),
            html.Div("The request took longer than 10 seconds to complete", 
                    style={'color': '#2c3e50'})
        ], style={'backgroundColor': '#f8d7da', 'padding': '15px', 'borderRadius': '5px', 'border': '1px solid #f5c6cb'})
        
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: {e}")
        return html.Div([
            html.Div("❌ Connection error when sending webhook", 
                    style={'color': '#e74c3c', 'fontWeight': 'bold', 'marginBottom': '10px'}),
            html.Div(f"Error: {str(e)}", 
                    style={'color': '#2c3e50'})
        ], style={'backgroundColor': '#f8d7da', 'padding': '15px', 'borderRadius': '5px', 'border': '1px solid #f5c6cb'})
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print(f"❌ Error type: {type(e)}")
        import traceback
        traceback.print_exc()
        return html.Div([
            html.Div("❌ Error sending test alert to Slack", 
                    style={'color': '#e74c3c', 'fontWeight': 'bold', 'marginBottom': '10px'}),
            html.Div(f"Error: {str(e)}", 
                    style={'color': '#2c3e50'})
        ], style={'backgroundColor': '#f8d7da', 'padding': '15px', 'borderRadius': '5px', 'border': '1px solid #f5c6cb'})


if __name__ == "__main__":
    app.run_server(debug=True, host='0.0.0.0', port=8050)
