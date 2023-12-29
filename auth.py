import requests
from requests.auth import HTTPBasicAuth

confluence_url = 'https://confluence.smartosc.com/pages/viewpage.action?pageId=216402368'
username = 'tuanlt'
password = 'G4f5!q=NrU'

# Make a request with HTTP Basic Authentication
response = requests.get(confluence_url, auth=HTTPBasicAuth(username, password))

# Check the response
if response.status_code == 200:
    print("Request successful")
    # Process the response content as needed
    print(response.text)
else:
    print(f"Request failed with status code {response.status_code}")
    print(response.text)
