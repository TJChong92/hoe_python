import argparse
import mysql.connector as mariadb
import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import ParagraphStyle
import matplotlib.pyplot as plt
import io

#dictonary to map

#define variable 
variable_to_column = {
    'flow_rate': 'flow_rate',
    'temp1': 'temp1',
    'temp2': 'temp2',
    'temp3': 'temp3',
    'velocity': 'velocity',
    'conductivity': 'conductivity',
    'resistivity': 'resistivity',
    'toc_meter': 'toc_meter',
    'SL': 'SL',
    'LL': 'LL',
    'Pressure_fail': 'Pressure_fail',
    'Ser_San': 'Ser_San'
}

#SI unit 
variable_to_si_unit = {
    'flow_rate': 'L/min',
    'temp1': '°C',
    'temp2': '°C',
    'temp3': '°C',
    'velocity': 'm/s',
    'conductivity': 'S/m',
    'resistivity': 'Ω/m',
    'toc_meter': 'ppm'
}

def fetch_data_from_database(column_name):# Function to fetch data from database
    try:
        # Connect to MariaDB using username and password
        db = mariadb.connect(user='root', password='syswelliot', host='127.0.0.1', database='myhoepharma', port='3306')

        # Calculate the timestamp for 10 minutes ago
        ten_minutes_ago = datetime.datetime.now() - datetime.timedelta(minutes=10)

        # SQL statement to get data for all variables in the last 10 minutes
        sql_statement = f"SELECT created_at, {column_name} FROM pharma_table WHERE created_at >= %s ORDER BY created_at ASC"

        cursor = db.cursor()
        cursor.execute(sql_statement, (ten_minutes_ago,))
        data = cursor.fetchall()

        cursor.close()
        db.close()

        return data
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB: {e}")
        return []

def generate_pdf_report(variable, variable_values, timestamp,data,variable_type, trigger_value = None):# Function to generate pdf
    report_filename = f'/home/sed23pi001/Desktop/hoepharmawork/pdf_history/{variable}_report.pdf'
    doc = SimpleDocTemplate(report_filename, pagesize=letter)

    # Define custom paragraph styles
    title_style = ParagraphStyle('Title', fontSize=16, leading=20, alignment=1, textColor='navy')
    data_style = ParagraphStyle('Data', fontSize=11, leading=13, textColor='black')

    report_elements = []

    # Add the report title
    report_title = f"{variable.capitalize()} Alarm Report - {timestamp}"
    report_elements.append(Paragraph(report_title, title_style))

    # Add a spacer
    report_elements.append(Spacer(1, 20))

    # Add variable-specific title
    report_elements.append(Paragraph(f"--- {variable.capitalize()} Data for the past 10 minute ---", title_style))
    report_elements.append(Spacer(1, 10))

    # Generate a plot graph for variable values
    timestamps = [row[0] for row in data]
    plt.figure(figsize=(8, 4))
    plt.plot(timestamps, variable_values, marker='o',markersize=2, linestyle='-')# set marker size to dotted smaller
    plt.xlabel("Timestamp")
    plt.ylabel(f"{variable.capitalize()} Value ({variable_to_si_unit.get(variable)})") # include SI unit
    plt.title(f"{variable.capitalize()} Value Plot for the Last 10 Minutes")
    plt.xticks(rotation=45)
    plt.grid()

    if trigger_value is not None:
        plt.axhline(y=trigger_value, color='r', linestyle='-', label=f'Trigger Value: {trigger_value}')

    # plt.legend(fontsize='small', loc='center right', labels=[
    # f'{variable.capitalize()} {variable_values[-1]} ({variable_to_si_unit.get(variable)})',
    # f'Trigger_value: {trigger_value} {variable_to_si_unit.get(variable)}'
    # ])


    # Save the plot graph as an image
    plot_image = io.BytesIO()
    plt.savefig(plot_image, format='png')
    plt.close()

    # Add the plot graph to the report
    plot_image.seek(0)
    img = Image(plot_image, width=500, height=250)
    report_elements.append(img)

    report_elements.append(Spacer(1, 20))
    report_elements.append(Paragraph("Alarm Triggered:", data_style))
    report_elements.append(Paragraph(f"Trigger Time: {timestamp}", data_style))

    if variable_type == 2 and trigger_value is not None:  # Analog variable with provided range
        report_elements.append(Paragraph(f"Triggered Values: {trigger_value} {variable_to_si_unit.get(variable)}", data_style))
        report_elements.append(Paragraph(f"Last Values: {variable_values[-1]} {variable_to_si_unit.get(variable)}", data_style))

    elif variable_type == 1:  # Digital variable
        report_elements.append(Paragraph(f"Triggered Values: 1", data_style))
        report_elements.append(Paragraph(f"Last Values: {variable_values[-1]}", data_style))

    report_elements.append(Spacer(1, 20))


    # Build the PDF report
    doc.build(report_elements)

    print(f"PDF report '{report_filename}' generated successfully.")

def main():
    parser = argparse.ArgumentParser(description='Generate PDF report for a specific variable.')
    parser.add_argument('variable', choices=variable_to_column.keys(), help='Specify the variable to generate the report for')
    parser.add_argument('variable_type', type=int, choices=[1, 2], help='Type of value: 1 for digital, 2 for analog')
    parser.add_argument('--trigger_value', type=float, help= 'Triggered value for the analog variable')

    args = parser.parse_args()

    #create a variables for the argument
    variable = args.variable
    variable_type = args.variable_type


    if variable_type == 2:
        trigger_value = args.trigger_value

    # Map chosen variable to corresponding database column name
        column_name = variable_to_column.get(variable)

        if column_name is None:
            print("Invalid variable chosen.")
            return

    # Fetch data from the database
        data = fetch_data_from_database(column_name)

        if data:
            variable_values = [row[1] for row in data]
            timestamp = data[-1][0] if data else "N/A"

        # Generate the PDF report
            generate_pdf_report(variable, variable_values, timestamp, data, variable_type, trigger_value)
            print (variable)
            print (variable_values)
            print (variable_type)
            print (trigger_value)

    elif variable_type == 1:  # Digital variable
        # Map chosen variable to corresponding database column name
        column_name = variable_to_column.get(variable)

        if column_name is None:
            print("Invalid variable chosen.")
            return

        # Fetch data from the database
        data = fetch_data_from_database(column_name)

        if data:
            variable_values = [row[1] for row in data]
            timestamp = data[-1][0] if data else "N/A"

            # Generate the PDF report for digital variables
            generate_pdf_report(variable, variable_values, timestamp, data, variable_type)
    else:
        print("Invalid variable type chosen.")

if __name__ == '__main__':
    main()
