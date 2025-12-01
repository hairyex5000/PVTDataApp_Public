import pandas as pd
from google.oauth2.service_account import Credentials
import gspread
import streamlit as st

SHEET_ID = st.secrets.sheet_id
SUB_SHEET_ID = st.secrets.sub_sheet_id
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

class SheetsDataHandler:
    def get_pvt_data(self, spreadsheet_id: str = SHEET_ID, sheet_name: str = SUB_SHEET_ID):
        spreadsheet = self.client.open_by_url(f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
        # Select a worksheet by name
        worksheet = spreadsheet.worksheet(sheet_name)

        # Read all values
        data = worksheet.get_all_values()
        data = pd.DataFrame(columns=data[0], data=data[1:])
        return data

    def __init__(self):
        self.creds = Credentials.from_service_account_info(
            st.secrets.gsheets, scopes=SCOPES
        )
        self.client = gspread.authorize(self.creds)

if __name__ == "__main__":
    print(SheetsDataHandler().get_pvt_data(SHEET_ID, SUB_SHEET_ID))