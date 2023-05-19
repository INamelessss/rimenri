from django.shortcuts import render, redirect
from . models import Product
from . forms import DateFilterForm
from googleapiclient.discovery import build
from google.oauth2 import service_account
from datetime import datetime

def get_spreadsheet_data():
    # Ruta al archivo JSON de credenciales descargado
    credentials_file = 'chartapp/credentials/key.json'

    # ID de la hoja de cálculo y rango de celdas que deseas obtener
    spreadsheet_id = '1_YR2tae9wNA6zYu7OSq5Kfq-yq4M2QNkOSbjkqXTIg0'
    range_name = 'Datos!A1:Z1000'

    # Cargar las credenciales desde el archivo JSON
    credentials = service_account.Credentials.from_service_account_file(
        credentials_file,
        scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
    )

    # Construir el servicio de Google Sheets
    service = build('sheets', 'v4', credentials=credentials)

    # Realizar la solicitud para obtener los datos de la hoja de cálculo
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()

    # Obtener los valores de las celdas
    values = result.get('values', [])

    return values

def index(request):
    spreadsheet_data = get_spreadsheet_data()

    # Crear un diccionario para almacenar los datos agrupados por área
    data_by_area = {}

    if request.method == 'POST':
        form = DateFilterForm(request.POST)
        if form.is_valid():
            fecha_inicial = form.cleaned_data['fecha_inicial']
            fecha_final = form.cleaned_data['fecha_final']

            # Convertir las fechas a objetos datetime
            fecha_inicial = datetime.combine(fecha_inicial, datetime.min.time())
            fecha_final = datetime.combine(fecha_final, datetime.max.time())

            # Filtrar los datos por fecha
            filtered_data = [row for row in spreadsheet_data[1:] if fecha_inicial <= datetime.strptime(row[4], '%d/%m/%Y %H:%M:%S') <= fecha_final]

            # Iterar sobre los datos filtrados
            for row in filtered_data:
                area = row[7]  # Columna 7: Área
                estado = row[5]  # Columna 5: Estado

                if area not in data_by_area:
                    data_by_area[area] = {'Atendido': 0, 'Pendiente': 0}

                if estado == 'Atendido':
                    data_by_area[area]['Atendido'] += 1
                elif estado == 'Pendiente':
                    data_by_area[area]['Pendiente'] += 1

    else:
        form = DateFilterForm()

        # Iterar sobre los datos de la hoja de cálculo
        for row in spreadsheet_data[1:]:  # Ignorar la primera fila (encabezados)
            area = row[7]  # Columna 7: Área
            estado = row[5]  # Columna 5: Estado

            if area not in data_by_area:
                data_by_area[area] = {'Atendido': 0, 'Pendiente': 0}

            if estado == 'Atendido':
                data_by_area[area]['Atendido'] += 1
            elif estado == 'Pendiente':
                data_by_area[area]['Pendiente'] += 1

    # Obtener las áreas y los datos de atendidos y pendientes correspondientes
    areas = list(data_by_area.keys())
    atendido_data = [data_by_area[area]['Atendido'] for area in areas]
    pendiente_data = [data_by_area[area]['Pendiente'] for area in areas]

    # Obtener los motivos y las cantidades correspondientes
    motivos = set([row[2] for row in spreadsheet_data[1:]])
    registros = []
    filtered_dates = [row[4] for row in filtered_data]
    for motivo in motivos:
        cantidad = sum(1 for row in spreadsheet_data[1:] if row[2] == motivo and row[4] in filtered_dates)
        registros.append((motivo, cantidad))

    # Ordenar la lista de registros de mayor a menor cantidad
    registros = sorted(registros, key=lambda x: x[1], reverse=True)

    context = {
        "atendido_data": atendido_data,
        "pendiente_data": pendiente_data,
        "areas": areas,
        "form": form,
        "registros": registros,
    }

    return render(request, 'chartapp/index.html', context)
