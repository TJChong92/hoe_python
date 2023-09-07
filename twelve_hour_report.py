import mysql.connector as mariadb
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
import datetime
import subprocess
import os
import re # Import the 're' module for regular expressions

def fetch_data_from_database():
    try:
        # Connect to MariaDB using username and password
        db = mariadb.connect(user='root', password='syswelliot', host='127.0.0.1', database='myhoepharma', port='3306')
        
        # Calculate the timestamp for 12 hours ago
        twelve_hours_ago = datetime.datetime.now() - datetime.timedelta(hours=12)
        
        # SQL statement to get data from the last 2 days
        sql_statement = "SELECT flow_rate, temp1, temp2, temp3, velocity, resistivity, conductivity, created_at " \
                        f"FROM pharma_table WHERE created_at >= '{twelve_hours_ago}' ORDER BY created_at DESC"

        cursor = db.cursor()
        cursor.execute(sql_statement)
        data = cursor.fetchall()

        cursor.close()
        db.close()

        return data
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB: {e}")
        return []

def generate_pdf_report(data):
    if not data:
        print("No data found. Report not generated.")
        return

    report_filename = f'/home/sed23pi001/Desktop/hoepharmawork/daily_report/report{datetime.datetime.now().strftime("%H%M")}.pdf'
    doc = SimpleDocTemplate(report_filename, pagesize=letter)

    # Define custom paragraph styles
    title_style = ParagraphStyle('Title', fontSize=12, leading=14, alignment=0, textColor='black', spaceAfter=5)# f want to add spaceAfter=10
    variable_style = ParagraphStyle('Variable', fontSize=11, leading=14, textColor='black', spaceBefore=10)
    data_style = ParagraphStyle('Data', fontSize=11, leading=13, textColor='black')

    

    # Dictionary to map each variable to its SI unit
    variable_units = {
        'Flow Rate': 'L/min',
        'Temp 1': '°C',
        'Temp 2': '°C',
        'Temp 3': '°C',
        'Velocity': 'm/s',
        'Resistivity': 'Ohm/cm',
        'Conductivity': 'mS/cm'
    }

    report_elements = []

    # Calculate the timestamp for 12 hours ago
    twelve_hours_ago = datetime.datetime.now() - datetime.timedelta(hours=12)

    # Add the report title
    report_title = f"Daily Analysis for  {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} till {twelve_hours_ago.strftime('%Y-%m-%d %H:%M:%S')}"
    report_elements.append(Paragraph(report_title, title_style))
    # Add a horizontal line under the title
    report_elements.append(HRFlowable(width="100%", thickness=1, lineCap='round', color='black', spaceBefore=5, spaceAfter=10))


    # Add a spacer
    report_elements.append(Spacer(1, 20))

    # Process data for each variable separately
    variables = ['Flow Rate', 'Temp 1', 'Temp 2', 'Temp 3', 'Velocity', 'Resistivity', 'Conductivity']

    for variable in variables:
        # Initialize values for each variable
        min_val = max_val = avg_val = None
        min_timestamp = max_timestamp = None

        for row in data:
            flow_rate, temp1, temp2, temp3, velocity, resistivity, conductivity, timestamp = row

            # Determine the correct value based on the current variable
            if variable == 'Flow Rate':
                val = flow_rate
            elif variable == 'Temp 1':
                val = temp1
            elif variable == 'Temp 2':
                val = temp2
            elif variable == 'Temp 3':
                val = temp3
            elif variable == 'Velocity':
                val = velocity
            elif variable == 'Resistivity':
                val = resistivity
            elif variable == 'Conductivity':
                val = conductivity

            # Update min, max, average, and the timestamps for min and max values
            if min_val is None or val < min_val:
                min_val = val
                min_timestamp = timestamp
            if max_val is None or val > max_val:
                max_val = val
                max_timestamp = timestamp
            if avg_val is None:
                avg_val = val
            else:
                avg_val = (avg_val + val) / 2

            # Calculate the average value and format it to have 2 decimal points
        if avg_val is not None:
            avg_val = round(avg_val, 2)  # Round to 2 decimal points

            
        unit = variable_units.get(variable, '')
        
        #spacing for data
        total_width = 80  # Total width of the fixed-width space (adjust as needed)
        value_width = len(str(min_val)) + len(unit)
        spaces_count = (total_width - value_width) // 2
        doted_width = 10 // 2
        tab_count = 10

        # Create the centered space
        centered_space = '&nbsp;' * spaces_count 
        tab_space = ' ' * tab_count
        doted_space = '&nbsp' * doted_width

        # Add the processed data for this variable to the report using the data_style
        report_elements.append(Paragraph(variable + f" ({unit})", variable_style))
        # Add the line with centered minimum value
        report_elements.append(Paragraph(f"Minimum {doted_space}: {centered_space} {min_val} {unit}{centered_space}{min_timestamp}", data_style))
        report_elements.append(Paragraph(f"Maximum {doted_space}:{centered_space} {max_val} {unit}{centered_space}{max_timestamp}", data_style))  # Use the formatted text here
        report_elements.append(Paragraph(f"Average {doted_space}: {centered_space} {avg_val} {unit}", data_style))

        # Add a spacer
        report_elements.append(Spacer(1, 20))

    # Build the PDF report
    doc.build(report_elements)

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

    #get the generate report filename 
    report_filename = f'/home/sed23pi001/Desktop/hoepharmawork/daily_report/report{datetime.datetime.now().strftime("%H%M")}.pdf'
    #printer name 
    printer_name = 'hp477_printer'

    print_report_to_printer(report_filename,printer_name)

# def main():
#     data = fetch_data_from_database()
#     generate_pdf_report(data)



if __name__ == "__main__":
    main()


