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
    'toc': 'toc_meter',
    'SL': 'SL',
    'LL': 'LL',
    'Air_Pressure_fail': 'Pressure_fail',
    'Ser_San': 'Ser_San'
}

#SI unit 
variable_to_si_unit = {
    'flow_rate': 'L/min',
    'temp1': '°C',
    'temp2': '°C',
    'temp3': '°C',
    'velocity': 'm/s',
    'conductivity': 'µS/cm',
    'resistivity': 'MΩ.cm',
    'toc': 'ppb',
    'SL': 'litres',
    'LL': 'litres',
    'Air_Pressure_fail': 'bar',
    'Ser_San': '°C'
}

def fetch_data_from_database(column_name,variable):# Function to fetch data from database
    try:
        # Connect to MariaDB using username and password
        db = mariadb.connect(user='root', password='syswelliot', host='127.0.0.1', database='myhoepharma', port='3306')#password=syswelliot

        # Calculate the timestamp for 10 minutes ago
        sixty_minutes_ago = datetime.datetime.now() - datetime.timedelta(minutes=60)

        # SQL statement to get data for all variables in the last 10 minutes
        sql_statement = f"SELECT created_at, {column_name} FROM pharma_table_new WHERE created_at >= %s ORDER BY created_at ASC"

        cursor = db.cursor()
        cursor.execute(sql_statement, (sixty_minutes_ago,))
        data = cursor.fetchall()

        cursor.close()
        db.close()

        if variable in ['SL', 'LL', 'Ser_San', 'Air_Pressure_fail']:
            # Apply value mapping to digital variables
            value_mapping = {
                'SL': {0: 1500, 1: 600},
                'LL': {0: 3000, 1: 1500},
                'Ser_San': {0: 75, 1: 80},
                'Air_Pressure_fail': {0: 7.0, 1: 4.0}
            }
            data = [(row[0], value_mapping[variable].get(row[1], row[1])) for row in data]

        return data
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB: {e}")
        return []

def generate_pdf_report(variable, variable_values, timestamp,data,variable_type, trigger_value = None):# Function to generate pdf
    report_filename = f'/home/sed23pi001/Desktop/hoepharmawork/pdf_history/{variable}_report.pdf'#f'/home/sed23pi001/Desktop/hoepharmawork/pdf_history/{variable}_report.pdf'
    doc = SimpleDocTemplate(report_filename, pagesize=letter)

    # Define custom paragraph styles
    top_style = ParagraphStyle('Title', fontSize=24, leading=20, alignment=1, textColor='black')
    title_style = ParagraphStyle('Title', fontSize=16, leading=20, alignment=1, textColor='navy')
    data_style = ParagraphStyle('Data', fontSize=11, leading=13, textColor='black')

    report_elements = []
    #add Hoe Pharma
    hoe_pharma = f"HOE PHARMACEUTICALS SDN. BHD."
    report_elements.append(Paragraph(hoe_pharma, top_style))
    report_elements.append(Spacer(1, 10))

    # Convert the entire variable to uppercase
    if variable == 'Ser_San':
        variable_display = 'SANITIZATION'
    else:
        variable_display = variable.upper()

    # Add the report title
    # report_title = f"{variable.capitalize()} Alarm Report - {timestamp}"
    report_title = f"{variable_display} Alarm Report - {timestamp}"
    report_elements.append(Paragraph(report_title, title_style))

    # Add a spacer
    report_elements.append(Spacer(1, 20))

    # Add variable-specific title
    # report_elements.append(Paragraph(f"--- {variable.capitalize()} Data for the past 60 minute ---", title_style))
    report_elements.append(Paragraph(f"--- {variable_display} Data for the past 60 minutes ---", title_style))
    report_elements.append(Spacer(1, 10))

    # Generate a plot graph for variable values
    timestamps = [row[0] for row in data]
    plt.figure(figsize=(8, 4))
    
    if variable_type == 1:
        plt.plot(timestamps, variable_values, marker='.', markersize=2, linestyle='-')
        plt.ylabel(f"{variable_display} SI Value ({variable_to_si_unit.get(variable)})") #SI UNIT Value

        if variable == 'SL':
            new_y_min, new_y_max = 0, 1700  # Customize the desired range for 'SL'
            plt.ylim(new_y_min, new_y_max)
        elif variable == 'LL':
            new_y_min, new_y_max = 0, 4000  # Customize the desired range for 'LL'
            plt.ylim(new_y_min, new_y_max)
        elif variable == 'Air_Pressure_fail':
            new_y_min, new_y_max = 0, 9  # Customize the desired range for 'AIR PRESSURE'
            plt.ylim(new_y_min, new_y_max)
        elif variable == 'Ser_San':
            new_y_min, new_y_max = 60, 90  # Customize the desired range for 'SANITIZATION'
            plt.ylim(new_y_min, new_y_max)


    else:
        plt.plot(timestamps, variable_values, marker='.',markersize=2, linestyle='-')# set marker size to dotted smaller
        plt.ylabel(f"{variable_display} Value ({variable_to_si_unit.get(variable)})")# include SI unit
   
    plt.xlabel("Timestamp")
    plt.title(f"{variable_display} Value Plot for the Last 60 Minutes")
    plt.xticks(rotation=45)
    plt.grid(False)

    if trigger_value is not None:
        if variable_type == 2:
            plt.axhline(y=trigger_value, color='r', linestyle='--', label=f'Trigger Value: {trigger_value}')

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
        report_elements.append(Paragraph(f"Triggered Values: {trigger_value} {variable_to_si_unit.get(variable)}", data_style))
        report_elements.append(Paragraph(f"Last Values: {variable_values[-1]} {variable_to_si_unit.get(variable)}", data_style))

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
        data = fetch_data_from_database(column_name,variable)

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
        data = fetch_data_from_database(column_name,variable)

        if data:
            variable_values = [row[1] for row in data]
            timestamp = data[-1][0] if data else "N/A"

            # Generate the PDF report for digital variables
            generate_pdf_report(variable, variable_values, timestamp, data, variable_type,trigger_value)
    else:
        print("Invalid variable type chosen.")

if __name__ == '__main__':
    main()
