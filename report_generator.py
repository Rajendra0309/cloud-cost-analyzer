from fpdf import FPDF
from datetime import datetime
import os
import cost_analyzer
import recommendations as rec_engine

# Colors (RGB)
COLOR_DARK = (15, 17, 23)
COLOR_HEADER = (30, 33, 48)
COLOR_ACCENT = (0, 122, 255)
COLOR_RED = (220, 53, 69)
COLOR_YELLOW = (255, 193, 7)
COLOR_GREEN = (40, 167, 69)
COLOR_WHITE = (255, 255, 255)
COLOR_LIGHT_GRAY = (245, 245, 245)
COLOR_MID_GRAY = (180, 180, 180)
COLOR_TEXT = (33, 37, 41)

# Base PDF Class
class FinOpsReport(FPDF):

    def header(self):
        self.set_fill_color(*COLOR_HEADER)
        self.rect(0, 0, 210, 18, 'F')
        self.set_font('Helvetica', 'B', 11)
        self.set_text_color(*COLOR_WHITE)
        self.set_xy(10, 4)
        self.cell(0, 10, 'Cloud Cost Analyzer - FinOps Report', ln=False)
        self.set_font('Helvetica', '', 8)
        self.set_xy(0, 6)
        self.cell(200, 6, f'Generated: {datetime.now().strftime("%d %b %Y, %H:%M")}', align='R')
        self.ln(14)

    def footer(self):
        self.set_y(-12)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(*COLOR_MID_GRAY)
        self.cell(0, 10, f'Cloud Cost Analyzer v3.0 | Page {self.page_no()}', align='C')

    def section_title(self, title):
        self.ln(4)
        self.set_fill_color(*COLOR_ACCENT)
        self.set_text_color(*COLOR_WHITE)
        self.set_font('Helvetica', 'B', 10)
        self.cell(0, 8, f' {title}', ln=True, fill=True)
        self.ln(2)
        self.set_text_color(*COLOR_TEXT)

    def metric_box(self, label, value, x, y, w=88, h=18,
                   color=COLOR_LIGHT_GRAY):
        self.set_xy(x, y)
        self.set_fill_color(*color)
        self.set_draw_color(*COLOR_MID_GRAY)
        self.rect(x, y, w, h, 'FD')
        self.set_font('Helvetica', '', 8)
        self.set_text_color(*COLOR_MID_GRAY)
        self.set_xy(x + 3, y + 2)
        self.cell(w - 6, 5, label)
        self.set_font('Helvetica', 'B', 13)
        self.set_text_color(*COLOR_TEXT)
        self.set_xy(x + 3, y + 8)
        self.cell(w - 6, 8, value)

    def table_header_row(self, cols, widths):
        self.set_fill_color(*COLOR_HEADER)
        self.set_text_color(*COLOR_WHITE)
        self.set_font('Helvetica', 'B', 8)
        for col, w in zip(cols, widths):
            self.cell(w, 7, col, border=1, fill=True)
        self.ln()

    def table_data_row(self, values, widths, fill=False):
        self.set_fill_color(*COLOR_LIGHT_GRAY)
        self.set_text_color(*COLOR_TEXT)
        self.set_font('Helvetica', '', 8)
        for val, w in zip(values, widths):
            self.cell(w, 6, str(val), border=1, fill=fill)
        self.ln()

# Priority -> color
def _priority_color(priority):
    if 'High' in priority: return COLOR_RED
    if 'Medium' in priority: return COLOR_YELLOW
    return COLOR_GREEN

# Main Report Generator
def generate_report(df, output_path="outputs/finops_report.pdf"):
    os.makedirs("outputs", exist_ok=True)

    total_cost = cost_analyzer.get_total_cost(df)
    service_df = cost_analyzer.get_service_breakdown(df)
    region_df = cost_analyzer.get_region_breakdown(df)
    waste = cost_analyzer.get_idle_waste_summary(df)
    forecast = cost_analyzer.forecast_next_month(df)
    anomaly_summary = cost_analyzer.get_anomaly_summary(df)
    savings = cost_analyzer.get_savings_estimate(df)
    rec_summary = rec_engine.get_recommendations_summary(df)
    rec_df = rec_summary['recommendations']

    pdf = FinOpsReport()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_text_color(*COLOR_TEXT)

    # Executive Summary
    pdf.section_title('1. Executive Summary')

    y = pdf.get_y()
    pdf.metric_box('Total Cloud Spend', 
                   f'${total_cost:,}', 10, y)

    y2 = y + 22
    pdf.metric_box('Idle Resource Waste', 
                   f'${waste["idle_cost"]:,} ({waste["waste_percentage"]}%)', 
                   10, y2, color=(255, 235, 235))
    pdf.metric_box('Potential Monthly Savings', 
                   f'${savings["total_monthly"]:,}', 
                   112, y2, color=(235, 255, 235))
    pdf.set_y(y2 + 24)

    direction = 'Trending UP' \
                if forecast['trend_direction'] == 'up' \
                else 'Trending DOWN'
    pdf.set_font('Helvetica', 'I', 9)
    pdf.set_text_color(*COLOR_MID_GRAY)
    pdf.cell(0,6,
             f'Cost trend: {direction} | '
             f'Avg daily cost: ${forecast["avg_daily_cost"]} | '
             f'Optimistic forecast: ${forecast["optimistic"]} | '
             f'Pessimistic: ${forecast["pessimistic"]}',
             ln=True)
    pdf.set_text_color(*COLOR_TEXT)
    pdf.ln(2)

    # Cost By Service
    pdf.section_title('2. Cost Breakdown by Service')

    cols = ['Service', 'Total Cost (USD)', '% of Spend']
    widths = [65, 65, 60]
    pdf.table_header_row(cols, widths)

    for i, row in service_df.iterrows():
        pdf.table_data_row(
            [row['service'],
             f"${row['total_cost']:,}",
             f"{row['percentage']}%"],
             widths,
             fill=(i % 2 == 0)
        )
    pdf.ln(4)

    # Cost By Region
    pdf.section_title('3. Cost Breakdown by Region')

    cols = ['Region', 'Total Cost (USD)']
    widths = [95, 95]
    pdf.table_header_row(cols, widths)

    for i, row in region_df.iterrows():
        pdf.table_data_row(
            [row['region'],
             f"${row['total_cost']:,}"],
             widths,
             fill=(i % 2 == 0)
        )
    pdf.ln(4)

    # Anamoly Detection
    pdf.section_title('4. Cost Anomaly Detection')

    if anomaly_summary['count'] > 0:
        pdf.set_font('Helvetica', 'I', 9)
        pdf.cell(0, 6,
                 f"Notice: {anomaly_summary['count']} anomaly day(s) detected. "
                 f"Worst spike: {anomaly_summary['worst_spike']}% "
                 f"on {anomaly_summary['worst_day']}",
                 ln=True)
        pdf.set_text_color(*COLOR_TEXT)
        pdf.ln(2)

        anomaly_df = anomaly_summary['anomalies']
        cols = ['Date', 'Daily Cost', 'Rolling Avg', 'Spike %']
        widths = [47, 47, 47, 49]
        pdf.table_header_row(cols, widths)

        for i, row in anomaly_df.iterrows():
            pdf.table_data_row(
                [str(row['date'].date()),
                 f"${row['daily_cost']:,}",
                 f"${row['rolling_avg']:,}",
                 f"{row['spike_pct']}%"],
                 widths,
                 fill=(i % 2 == 0)
            )
    else:
        pdf.set_font('Helvetica', 'I', 9)
        pdf.cell(0, 6, 'No anomaly days detected in the selected period.', ln=True)
    pdf.ln(4)

    # Idle Resources
    pdf.section_title('5. Idle Resource Waste')

    pdf.set_font('Helvetica', '', 9)
    pdf.cell(0,6,
             f"Idle resources found: {waste['idle_cost']} | "
             f"Total wasted: ${waste['idle_cost']:,} | "
             f"Waste as % of spend: {waste['waste_percentage']}%",
             ln=True)
    pdf.ln(2)

    waste_by_svc = waste['by_service']
    cols = ['Service', 'Wasted Cost (USD)']
    widths = [95, 95]
    pdf.table_header_row(cols, widths)

    for i, row in waste_by_svc.iterrows():
        pdf.table_data_row(
            [row['service'], f"${row['wasted_cost']:,}"],
             widths,
             fill=(i % 2 == 0)
        )
    pdf.ln(4)

    # Recommendations
    pdf.section_title('6. Optimization Recommendations')

    pdf.set_font('Helvetica', '', 9)
    pdf.cell(0, 6,
             f"Total recommendations: {rec_summary['total']} | "
             f"High: {rec_summary['high']} | "
             f"Medium: {rec_summary['medium']} | "
             f"Est. monthly savings: ${rec_summary['total_saving']:,}",
             ln=True)
    pdf.ln(2)

    if not rec_df.empty:
        cols = ['Resource ID', 'Service', 'Issue', 
                'Action', 'Priority', 'Monthly Saving']
        widths = [28, 18, 45, 50, 20, 29]
        pdf.table_header_row(cols, widths)

        for i, row in rec_df.iterrows():
            priority_raw = str(row['priority'])
            priority_clean = ''.join(ch for ch in priority_raw if ord(ch) < 128).strip()
            pdf.table_data_row(
                [row['resource_id'],
                 row['service'],
                 row['issue'][:40] + '...'
                 if len(row['issue']) > 40 else row['issue'],
                 row['action'][:48] + '...'
                 if len(row['action']) > 48 else row['action'],
                 priority_clean,
                 f"${row['monthly_saving']:,}"],
                 widths,
                 fill=(i % 2 == 0)
            )
    pdf.ln(4)

    # Savings Summary
    pdf.section_title('7. Potential Savings Summary')

    savings_df = savings['breakdown']
    if not savings_df.empty:
        cols = ['Strategy', 'Monthly Saving', 'Effort', 'Impact']
        widths = [90, 40, 30, 30]
        pdf.table_header_row(cols, widths)

        for i, row in savings_df.iterrows():
            pdf.table_data_row(
                [row['strategy'],
                f"${row['monthly_saving']:,}",
                row['effort'],
                row['impact']],
                widths,
                fill=(i % 2 == 0)
            )

    pdf.ln(4)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_text_color(*COLOR_GREEN)
    pdf.cell(0, 8,
             f" Total Estimated Monthly Savings: "
             f"${savings['total_monthly']:,}",
             ln=True)
    pdf.set_text_color(*COLOR_TEXT)

    # Save
    pdf.output(output_path)
    return output_path

if __name__ == "__main__":
    from data_loader import load_data

    df = load_data("data/sample_data.csv")
    path = generate_report(df)
    print(f"Report generated: {path}")