import gspread

from oauth2client.service_account import ServiceAccountCredentials


class CustomGSpread(object):
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    credentials = None
    client = None

    def __init__(self):
        self.credentials = ServiceAccountCredentials.from_json_keyfile_name('service-key.json', self.scope)
        self.authorize()

    def authorize(self):
        self.client = gspread.authorize(self.credentials)

    def get_worksheet(self, spreadsheet_key, worksheet_id):
        ssheet = self.client.open_by_key(spreadsheet_key)
        wsheets = ssheet.worksheets()
        for ws in wsheets:
            if str(ws.id) == worksheet_id:
                return ws

    def values_to_dicts(self, values):
        header = values[0]
        range_data = []
        for row in values[1:]:
            row_data = {}
            for i, cell in enumerate(row):
                row_data.update({header[i]: cell})

            range_data.append(row_data)

        return range_data

