#!/usr/bin/env python3

import pandas as pd
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from googleapiclient.discovery import build
from google_auth import authenticate
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

# The ID and range of a sample spreadsheet.
JOB_TIMES_ID = "1aDYAz8_-z6qZYORinrGXjEDe_To6GmlIth7bZjCkAOM"
#'1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms'
JOB_TIMES_RANGE = '2019!B1:H100'
SHOPPING_ID = "10bY8qgDNLyhDjHjbCIJMqSjiRqDvaVYe-HYoyQYzJKA"
SHOPPING_RANGES = ('Aldi!G:K', 'REWE!A:E', 'Andere!A:F')

def get_job_time_data():
    creds = authenticate()
    service = build('sheets', 'v4', credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=JOB_TIMES_ID, range=JOB_TIMES_RANGE, majorDimension='ROWS').execute()
    values = result.get('values', [])

    #request = service.spreadsheets().values().batchGet(spreadsheetId=spreadsheet_id, ranges=ranges, valueRenderOption=value_render_option, dateTimeRenderOption=date_time_render_option)
    #response = request.execute()

    df = pd.DataFrame(values[1:], columns=values[0])
    df.Arbeitszeit = df.Arbeitszeit.fillna(0)
    df.Tag = pd.to_datetime(df.Tag, dayfirst=True, errors='raise')
    df.Gleitzeit = df.Gleitzeit.str.replace(',','.').astype(float)
    df.Arbeitszeit = pd.to_datetime(df.Arbeitszeit).dt.time

val=[]
for line in values[1:]:
    if line[0] and line[1]:
        if new_item:
            values_dict.append(new_item)
        new_item={'date':datetime.strptime(line[0], '%d.%m.%Y'),'price':line[1], 'items':[{'item':line[2], 'price':line[3], 'note':line[4] if len(line)==5 else ''}]}
    else:
        new_item['items'].append({'item':line[2], 'price':line[3], 'note':line[4] if len(line)==5 else ''})



def get_shopping_data():
    creds = authenticate()
    service = build('sheets', 'v4', credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()
    result = sheet.values().batchGet(spreadsheetId=SHOPPING_ID, ranges=SHOPPING_RANGES, majorDimension='ROWS').execute()
    values = result.get('values', [])

    #request = service.spreadsheets().values().batchGet(spreadsheetId=spreadsheet_id, ranges=ranges, valueRenderOption=value_render_option, dateTimeRenderOption=date_time_render_option)
    #response = request.execute()


def main():
    """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """
    

    df = df.sort_values(by='Tag')

    """plt.plot(df.Tag, df.Gleitzeit)
    plt.savefig('gleitzeit.png')

    plt.clf()
    plt.plot(df.Tag[:-1], df.Arbeitszeit[:-1])
    plt.savefig('arbeitszeit.png')"""

    plot_time_series(df.Tag, df.Gleitzeit)

    #df = df[pd.notnull(df.Arbeitszeit)]
    plot_time_series(df.Tag, df.Arbeitszeit)


def plot_time_series(xData, yData):
    plt.clf()
    months = mdates.MonthLocator()  # every month
    months_fmt = mdates.DateFormatter('%B')
    fig, ax = plt.subplots()
    ax.plot(xData, yData)
    ax.xaxis.set_major_locator(months)
    ax.xaxis.set_major_formatter(months_fmt)
    ax.grid(True)
    fig.autofmt_xdate()
    plt.savefig(f"{yData.name}.png")




if __name__ == '__main__':
    main()