import requests
import email
import csv
import pandas as pd
import datetime
from email.header import decode_header
from email.utils import parsedate_to_datetime
from imapclient import IMAPClient

class EmailService:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        print("Inside EmailService initialization:", self.email, self.password)
        self.TARGET_SUBJECT = "Opsgenie Alert"
    
    def fetch_emails(self, start_date, end_date):
        formatted_start_date = start_date.strftime("%d-%b-%Y")
        formatted_end_date = end_date.strftime("%d-%b-%Y")
        print("Formatted start date:", formatted_start_date)
        print("Formatted end date:", formatted_end_date)

        
        
        with IMAPClient("imap.gmail.com", use_uid=True, ssl=True) as client:
            print(f"Attempting to login with email: {self.email} and password: {self.password}") 
            client.login(self.email, self.password)
            client.select_folder("[Gmail]/All Mail")
            #search_query =  f'SUBJECT "{self.TARGET_SUBJECT}" SINCE {formatted_start_date} BEFORE {formatted_end_date}'
            print(self.TARGET_SUBJECT)
            search_query = f'SUBJECT "{self.TARGET_SUBJECT}" SINCE {formatted_start_date} BEFORE {formatted_end_date}'


            msgnums = client.search(search_query, charset="UTF-8")
            
            output_data = []
            if msgnums:
                response = client.fetch(msgnums, ('RFC822',))
                for msgnum, msg_data in response.items():
                  
                    msg = email.message_from_bytes(msg_data[b"RFC822"])
                    print("this is msg:",msg)
                   
                    if msg.is_multipart():
                        for part in msg.walk():
                            print("this is part:",part)
                            payload = part.get_payload(decode=True)
                            if payload:
                                content = payload.decode("utf-8")
                    else:
                        payload = msg.get_payload(decode=True)
                        print(payload)
                        if payload:
                            content = payload.decode("utf-8")
                        else:
                            content = ""

                    alertname = self.extract_field(content, 'alertname')
                    priority = self.extract_field(content, 'priority')
                    zone = self.extract_field(content, 'zone')
                    description = self.extract_field(content, 'description')
                    show_alert_link = self.extract_field(content, 'Show Alert')
                    alert_details = self.get_alert_details(show_alert_link.split('/')[-1])
                    if alert_details:
                        cluster = alert_details.get('details', {}).get('label_olympus_cluster', '')
                        namespace = alert_details.get('details', {}).get('namespace', '')
                        tiny_id = alert_details.get('tinyId', '')
                        created_at = alert_details.get('createdAt', '')
                        updated_at = alert_details.get('updatedAt', '')
                        runbook_url = alert_details.get('details', {}).get('runbook_url', '')
                        count = alert_details.get('count', '')
                        status = alert_details.get('status','')
                        output_data.append([formatted_start_date, alertname, priority, zone, status, show_alert_link, None, description, cluster, namespace, tiny_id, created_at, updated_at, runbook_url, count])

            if output_data:
                output_file = f'alerts_{formatted_start_date}_to_{formatted_end_date}.csv'
                header = ['Date','Alert Name', 'Priority', 'Zone', 'Status', 'Alert Link', 'Email or Call', 'Description','Cluster','Namespace','TinyID','Created_at','Updated_at','Runbook_URL','Count']
                with open(output_file, 'w', newline='') as csvfile:
                    csv_writer = csv.writer(csvfile)
                    csv_writer.writerow(header)
                    csv_writer.writerows(output_data)
                df = pd.read_csv(output_file)
                df.loc[(df['Priority'] == 'P1') | (df['Priority'] == 'P2'), 'Email or Call'] = 'Call'
                df.loc[(df['Priority'] != 'P1') & (df['Priority'] != 'P2'), 'Email or Call'] = 'Email'
                df = df.drop_duplicates()
                df.to_csv(output_file, index=False)
                return output_file
            return None

    def get_alert_details(self, alert_id):
        headers = {
            "Authorization": "GenieKey 7694f565-ab49-4c96-9c4b-9774a1d949f9"
        }
        url = f"https://api.opsgenie.com/v2/alerts/{alert_id}"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json().get("data")
        return None

    def extract_field(self, content, field_name):
        if field_name == 'description':
            return content.split('description:')[1].split(' message:')[0]
        elif field_name == 'Show Alert':
            return content.split('Show Alert (')[1].split(')')[0]
        else:
            return content.split(field_name + ':')[1].split()[0]
