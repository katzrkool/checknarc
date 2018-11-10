import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from csv import DictReader, DictWriter
from time import sleep
from os.path import join

class Scraper:
    def __init__(self, patients, username: str, password: str, writeFolder: str):
        self.patients = self.csvParse(patients)
        self.username = username
        self.password = password
        self.writeFolder = writeFolder
        today = datetime.today().date()
        self.enddate = today.strftime("%m/%d/%Y")
        self.startdate = (today - timedelta(days=100)).strftime('%m/%d/%Y"')
        self.session = requests.session()
        self.auth_token = ''
        self.pdfLinks = []

        self.initSession(self.username, self.password)

    def bulk(self):
        data = []
        for i in self.patients:
            data.append(self.patientLookup(i['first'], i['last'], i['dob']))
        self.pdfFetch(self.pdfLinks)
        self.csvExport(data)

    def csvParse(self, file: str):
        with open(file, 'r')  as f:
            reader = DictReader(f)
            patients = [{'first': row['Patient First Name'],
                         'last': row['Patient Last Name'],
                         'dob': row['Patient DOB']} for row in reader]
        return patients

    def csvExport(self, data: list):
        fieldnames = ['First Name', 'Last Name', 'DOB', 'Response']
        with open(join(self.writeFolder, 'patients.csv'), 'w') as f:
            writer = DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

    def pdfFetch(self, links: list):
        if len(links) < 2:
            sleep(4/len(links))

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Accept': '*/*;q=0.5, text/javascript, application/javascript, application/ecmascript, application/x-ecmascript',
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRF-Token': self.auth_token,
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0'}

        for i in links:
            # Each link object is a dict with the keys url, id, and fileName
            pdf = self.session.get(i['url'])
            with open(f'{join(self.writeFolder, i["fileName"])}.pdf', 'wb') as f:
                f.write(pdf.content)

            #Once we have the pdf, remove the document so the user doesn't have a ton of docs waiting for them.
            self.request('GET', f'https://arkansas.pmpaware.net/background_documents/{i["id"]}/cancel', headers=headers)

    def request(self, type: str, url: str, headers: dict = None, data: dict= None, params = None, attempts: int = 2) -> requests.Response:
        for i in range(0, attempts):
            try:
                r = self.session.request(type, url, headers=headers, data=data, params=params)
                return r
            except requests.ConnectionError as err:
                if i == attempts - 1:
                    raise err

    def extract_auth(self, data: str):
        soup = BeautifulSoup(data, 'html.parser')
        return soup.find('meta', {'name': 'csrf-token'})['content']

    def initSession(self, username: str, password: str):
        loginPage = self.request('GET', 'https://arkansas.pmpaware.net/', attempts=1).text
        self.auth_token = self.extract_auth(loginPage)
        payload = {'auth_key': username, 'authenticity_token': self.auth_token, 'commit': 'Log+In', 'password': password, 'utf8': '✓', }
        r = self.request('POST', 'https://arkansas.pmpaware.net/auth/identity/callback', data=payload)
        self.auth_token = self.extract_auth(r.text)


    def patientLookup(self, first: str, last: str, dob: str):
        payload = {'authenticity_token': self.auth_token, 'rx_search_request[first_name]': first,
                   'rx_search_request[last_name]': last, 'rx_search_request[birthdate]': dob, 'utf8': '✓',
                   'rx_search_request[filled_at_begin]': self.startdate, 'rx_search_request[filled_at_end]': self.enddate,
                   'rx_search_request[search_type]': 'interconnect'}

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Accept': '*/*;q=0.5, text/javascript, application/javascript, application/ecmascript, application/x-ecmascript',
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRF-Token': self.auth_token,
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0'}

        r = self.request('POST', 'https://arkansas.pmpaware.net/rx_search_requests', headers=headers, data=payload).text
        return {'First Name': first, 'Last Name': last, 'DOB': dob, 'Response': self.formatResponse(r, f"{first}{last}")}


    def formatResponse(self, response: str, fileName: str) -> str:
        if "  $('#patients_found_but_no_results_modal').modal('toggle');" in response:
            return 'Valid Patient, No Results'
        elif 'div_string += "No matching patient identified."' in response:
            return 'No Patient Found'
        elif 'top.location' in response:
            id = response.split('rx_search_requests/')[1].split('"\n')[0]
            return self.genPDF(id, fileName)
        else:
            return response

    def genPDF(self, id: str, fileName) -> str:
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRF-Token': self.auth_token,
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0'}

        r = self.request('GET', f'https://arkansas.pmpaware.net/rx_search_requests/{id}', headers = headers).text

        headers['X-CSRF-Token'] = self.extract_auth(r)

        url = 'https://arkansas.pmpaware.net/background_documents/new'
        params = {'request_id': id, 'request_type': 'RxSearchRequest',
                  'sort': 'Prescriptions/filled_at/desc|Prescribers/prescriber_last_name/asc|Dispensers/dispensary_name/desc'}

        r = self.request('GET', url, params=params, headers=headers).text
        pdfID = r.split('"id":')[1].split(',"user_id"')[0]

        pdfUrl = f'https://arkansas.pmpaware.net/background_documents/{pdfID}/download'

        self.pdfLinks.append({'url': pdfUrl, 'id': id, 'fileName': fileName})

        return f'See {fileName}.pdf'
