import mysql.connector as mariadb
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas
import datetime
import subprocess
import os
import re # Import the 're' module for regular expressions


def fetch_data_from_database():
    try:
        # Connect to MariaDB using username and password
        db = mariadb.connect(user='root', password='syswelliot', host='127.0.0.1', database='myhoepharma', port='3306')
        
        # Calculate the timestamp for 12 hours ago
        twentyfour_hours_ago = datetime.datetime.now() - datetime.timedelta(hours=24)
        
        # SQL statement to get data from the last 2 days
        sql_statement = "SELECT  velocity, temp1, temp2, temp3, resistivity, conductivity,toc_meter, created_at " \
                        f"FROM pharma_table_new WHERE created_at >= '{twentyfour_hours_ago}' ORDER BY created_at DESC"

        cursor = db.cursor()
        cursor.execute(sql_statement)
        data = cursor.fetchall()

        cursor.close()
        db.close()

        return data
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB: {e}")
        return []

def format_value(value, decimal_points):
    try:
        formatted_value = "{:.{}f}".format(float(value), decimal_points)
        return formatted_value
    except ValueError:
        return value

def generate_pdf_report(data):
    if not data:
        print("No data found. Report not generated.")
        return

    report_filename = f'/home/sed23pi001/Desktop/hoepharmawork/daily_report/report{datetime.datetime.now().strftime("%H%M")}.pdf'

    # Create a PDF document using canvas
    c = canvas.Canvas(report_filename, pagesize=letter)

    # Define custom paragraph styles
    top_style = "Helvetica-Bold", 24
    title_style = "Helvetica", 12
    variable_style = "Helvetica", 11
    data_style = "Helvetica", 11
    page_style = "Helvetica", 9
    doneby_style = "Helvetica", 9
    checkby_style = "Helvetica", 9
    pagewidth,_ = letter

    # Dictionary to map each variable to its SI unit
    variable_units = {
        'Velocity': 'm/s',
        'Temp 1': '°C',
        'Temp 2': '°C',
        'Temp 3': '°C',
        'Resistivity': 'Ohm/cm',
        'Conductivity': 'mS/cm',
        'TOC' : 'ppb'
    }

    # Calculate the timestamp for 12 hours ago
    twentyfour_hours_ago = datetime.datetime.now() - datetime.timedelta(hours=24)

    #add Hoe Pharma
    hoe_pharma = f"HOE PHARMACEUTICALS SDN. BHD."
    c.setFont(*top_style)
    c.drawString(75, 750, hoe_pharma)

    # Add the report title
    report_title = f"Daily Analysis for  {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} till {twentyfour_hours_ago.strftime('%Y-%m-%d %H:%M:%S')}"
    c.setFont(*title_style)
    c.drawString(50, 700, report_title)

    # Add a horizontal line under the title
    c.setStrokeColor(colors.black)
    c.setLineWidth(1)
    c.line(50, 690, 550, 690)

    # Add a spacer
    c.setFont(*variable_style)
    c.drawString(50, 670, " ")

    # Process data for each variable separately
    variables = [ 'Velocity', 'Temp 1', 'Temp 2', 'Temp 3', 'Resistivity', 'Conductivity', 'TOC']

    vertical_position = 650  # Initial vertical position

    for variable in variables:
        # Initialize values for each variable
        min_val = max_val = avg_val = None
        min_timestamp = max_timestamp = None

        for row in data:
            velocity, temp1, temp2, temp3, resistivity, conductivity, toc_meter, timestamp = row

            # Determine the correct value based on the current variable
            if variable == 'Velocity':
                val = format_value(velocity, 2)  # Format to 2 decimal points
            elif variable == 'Temp 1':
                val = format_value(temp1, 1)  # Format to 1 decimal point
            elif variable == 'Temp 2':
                val = format_value(temp2, 1)  # Format to 1 decimal point
            elif variable == 'Temp 3':
                val = format_value(temp3, 1)  # Format to 1 decimal point
            elif variable == 'Resistivity':
                val = format_value(resistivity, 1)  # Format to 1 decimal point
            elif variable == 'Conductivity':
                val = format_value(conductivity, 1)  # Format to 1 decimal point
            elif variable == 'TOC':
                val = format_value(toc_meter, 1)  # Format to 1 decimal point

            # Update min, max, average, and the timestamps for min and max values
            if min_val is None or float(val) < float(min_val):
                min_val = val
                min_timestamp = timestamp
            if max_val is None or float(val) > float(max_val):
                max_val = val
                max_timestamp = timestamp
            if avg_val is None:
                avg_val = float(val)
            else:
                avg_val = (avg_val + float(val)) / 2

        # Calculate the average value and format it to have the desired decimal points
        if avg_val is not None:
            avg_val = format_value(avg_val, 1)  # Format to 1 decimal point

        unit = variable_units.get(variable, '')

        # Add variable name and unit
        c.setFont(*variable_style)
        c.drawString(50, vertical_position, f"{variable} ({unit})")
        
        # Add minimum value and timestamp
        c.setFont(*data_style)
        c.drawString(50, vertical_position - 15, f"Minimum: ")
        c.drawString(250, vertical_position - 15, f"{min_val} {unit}")
        c.drawString(450, vertical_position - 15, f" {min_timestamp}")

        # Add maximum value and timestamp
        c.drawString(50, vertical_position - 30, f"Maximum: ")
        c.drawString(250, vertical_position - 30, f"{max_val} {unit}")
        c.drawString(450, vertical_position - 30, f"{max_timestamp}")

        # Add average value
        c.drawString(50, vertical_position - 45, f"Average: ")
        c.drawString(250, vertical_position - 45, f"{min_val} {unit}")
        
        # Add a spacer
        vertical_position -= 70  # Move down 60 points

    # Add page number
    c.setFont(*page_style)
    c.drawString(250, 50, "Page 1 of 1")

    # Add done by and checked by
    done_by = f"Done by:_________________________"
    checked_by = f"Checked by:_________________________"
    c.setFont(*doneby_style)
    c.drawString(50, 90, done_by)
    c.setFont(*checkby_style)
    c.drawString(pagewidth -230, 90, checked_by)

    signature_date_text = "(Signature & Date)"
    c.drawString(105, 75, signature_date_text)  # Adjust vertical position
    c.drawString(pagewidth - 160, 75, signature_date_text)

    # Save the PDF
    c.save()

    print(f"PDF report '{report_filename}' generated successfully.")

def print_report_to_printer(report_filename, printer_name):
    try:
        lp_command = ['lp', '-d', printer_name, report_filename]
        subprocess.run(lp_command, check=True)
        print(f"PDF report '{report_filename}' sent to the printer '{printer_name}' successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error printing the report: {e}")
        
def main():
    data = fetch_data_from_database()
    generate_pdf_report(data)

    # # #get the generate report filename 
    report_filename = f'/home/sed23pi001/Desktop/hoepharmawork/daily_report/report{datetime.datetime.now().strftime("%H%M")}.pdf'
    #printer name 
    printer_name = 'hoe_pharma_printer'

    print_report_to_printer(report_filename,printer_name)


if __name__ == "__main__":
    main()

