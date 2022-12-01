import datetime
import os
from config import base_url,team_xls
import pandas as pd


def str_to_datetime(s, fmt=None):
    if fmt is None:
        fmt = '%Y-%m-%d %X'
    return datetime.datetime.strptime(s, fmt)


def get_urls(date_list):
    urls = []
    for day in date_list:
        urls.append(base_url.format(day))
    return urls

def read_team_excel():
    file_excel = "excel"
    xls_path = get_excel_path(file_excel, team_xls)
    sheet = pd.read_excel(xls_path)
    # head_list = list(sheet.columns)
    excel_list = []
    for data in sheet.values:
        team_id = str(data[0]).strip()
        country_id = str(data[2]).strip()
        team_name = str(data[3]).strip()
        sheet_info = {"team_id": team_id, "country_id": country_id, "team_name": team_name}
        excel_list.append(sheet_info)
    return excel_list


def get_file_path(file_name):
    file_path = ""
    excel_path = os.getcwd()
    for root, dirs, files in os.walk(excel_path):
        if root.endswith(file_name):
            file_path = root
    return  file_path


def get_excel_path(file_excel,file_name):
    xlsx_name = ""
    excel_path = os.getcwd()
    for root, dirs, files in os.walk(excel_path):
        if root.endswith(file_excel):
            file_list = os.listdir(root)
            for excel_name in file_list:
                if excel_name == file_name:
                    xlsx_name = os.path.join(root, excel_name)
                    # print("---xlsx_name---:", xlsx_name)
        else:
            continue
    return xlsx_name

if __name__ == '__main__':
    file_name= "player"
    get_file_path(file_name)