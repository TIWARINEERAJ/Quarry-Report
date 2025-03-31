from flask import Flask, render_template, request, redirect, url_for
import psycopg2
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime

app = Flask(__name__)

def get_db_connection():
    return psycopg2.connect(
        dbname="quarry_management",
        user="postgres",
        password="Green2025",
        host="localhost",
        port="5432"
    )

def safe_float(value, default=0.0):
    try:
        return float(value) if value else default
    except (ValueError, TypeError):
        return default

def get_chart_image(fig):
    img = io.BytesIO()
    fig.savefig(img, format='png')
    img.seek(0)
    img_url = base64.b64encode(img.getvalue()).decode()
    plt.close(fig)
    return f"data:image/png;base64,{img_url}"

@app.route('/', methods=['GET', 'POST'])
def index():
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        print("POST request received!")
        try:
            # Extract form data
            report_date = request.form.get('report_date')
            day_number = int(request.form.get('day_number'))

            # Extract pump details
            pump_details = []
            for i in range(1, 6):
                pump_name = request.form.get(f'pump_name_{i}', '')
                run_hrs = safe_float(request.form.get(f'run_hrs_{i}'))
                amp = safe_float(request.form.get(f'amp_{i}'))
                pr_ksc = safe_float(request.form.get(f'pr_ksc_{i}'))
                power_drawn_kw = safe_float(request.form.get(f'power_drawn_kw_{i}'))
                flow_m3hr = safe_float(request.form.get(f'flow_m3hr_{i}'))
                volume = safe_float(request.form.get(f'volume_{i}'))
                pump_details.append((pump_name, run_hrs, amp, pr_ksc, power_drawn_kw, flow_m3hr, volume))

            # Extract other fields
            quarry_lvl_previous = safe_float(request.form.get('quarry_lvl_previous'))
            quarry_lvl_today = safe_float(request.form.get('quarry_lvl_today'))
            quarry_lvl_change = safe_float(request.form.get('quarry_lvl_change'))
            series2f_inflow = safe_float(request.form.get('series2f_inflow'))
            series2a_inflow = safe_float(request.form.get('series2a_inflow'))
            drain_inflow = safe_float(request.form.get('drain_inflow'))
            total_inflow = safe_float(request.form.get('total_inflow'))
            net_flow = safe_float(request.form.get('net_flow'))
            rainfall_mm = safe_float(request.form.get('rainfall_mm'))
            rainfall_start = request.form.get('rainfall_start') or None
            rainfall_stop = request.form.get('rainfall_stop') or None
            rainfall_diff = safe_float(request.form.get('rainfall_diff'))
            power_cut_on = request.form.get('power_cut_on') or None
            power_cut_off = request.form.get('power_cut_off') or None
            power_cut_diff = safe_float(request.form.get('power_cut_diff'))
            power_cut_total_hrs = safe_float(request.form.get('power_cut_total_hrs'))
            power_cut_cum_hrs = safe_float(request.form.get('power_cut_cum_hrs'))

            # Insert into database
            cursor.execute("""
                INSERT INTO quarry_report (
                    report_date, day_number,
                    pump_name_1, run_hrs_1, amp_1, pr_ksc_1, power_drawn_kw_1, flow_m3hr_1, volume_1,
                    pump_name_2, run_hrs_2, amp_2, pr_ksc_2, power_drawn_kw_2, flow_m3hr_2, volume_2,
                    pump_name_3, run_hrs_3, amp_3, pr_ksc_3, power_drawn_kw_3, flow_m3hr_3, volume_3,
                    pump_name_4, run_hrs_4, amp_4, pr_ksc_4, power_drawn_kw_4, flow_m3hr_4, volume_4,
                    pump_name_5, run_hrs_5, amp_5, pr_ksc_5, power_drawn_kw_5, flow_m3hr_5, volume_5,
                    quarry_lvl_previous, quarry_lvl_today, quarry_lvl_change,
                    series2f_inflow, series2a_inflow, drain_inflow, total_inflow, net_flow,
                    rainfall_mm, rainfall_start, rainfall_stop, rainfall_diff,
                    power_cut_on, power_cut_off, power_cut_diff, power_cut_total_hrs, power_cut_cum_hrs
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                report_date, day_number,
                *pump_details[0], *pump_details[1], *pump_details[2], *pump_details[3], *pump_details[4],
                quarry_lvl_previous, quarry_lvl_today, quarry_lvl_change,
                series2f_inflow, series2a_inflow, drain_inflow, total_inflow, net_flow,
                rainfall_mm, rainfall_start, rainfall_stop, rainfall_diff,
                power_cut_on, power_cut_off, power_cut_diff, power_cut_total_hrs, power_cut_cum_hrs
            ))
            conn.commit()
            print("Data inserted successfully!")
        except Exception as e:
            print(f"Error: {e}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
        return redirect(url_for('index'))

    # Fetch and display reports
    cursor.execute("SELECT * FROM quarry_report ORDER BY report_date DESC LIMIT 7")
    reports = cursor.fetchall()

    dates = [str(row[1]) for row in reports]
    quarry_levels = [row[39] or 0 for row in reports]
    quarry_changes = [row[40] or 0 for row in reports]
    rainfall = [row[46] or 0 for row in reports]
    power_cut = [row[53] or 0 for row in reports]

    charts = {}
    if reports:
        fig1, ax1 = plt.subplots()
        ax1.plot(dates, quarry_levels, marker='o', label='Quarry Level (m)')
        ax1.set_title('Quarry Level Trend')
        charts['quarry_level'] = get_chart_image(fig1)

        fig2, ax2 = plt.subplots()
        ax2.bar(dates, quarry_changes, color='orange', label='Quarry Level Change (m)')
        charts['quarry_change'] = get_chart_image(fig2)

        fig3, ax3 = plt.subplots()
        ax3.plot(dates, rainfall, marker='x', color='blue')
        charts['rainfall'] = get_chart_image(fig3)

        fig4, ax4 = plt.subplots()
        ax4.bar(dates, power_cut, color='red')
        charts['power_cut'] = get_chart_image(fig4)

    cursor.close()
    conn.close()

    return render_template('index.html', reports=reports, charts=charts)

if __name__ == '__main__':
    app.run(debug=True)