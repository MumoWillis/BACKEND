import requests
import base64
from requests.auth import HTTPBasicAuth
from datetime import datetime
from config import Config

def generate_token():
    response = requests.get(
        'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials',
        auth=HTTPBasicAuth(Config.MPESA_CONSUMER_KEY, Config.MPESA_CONSUMER_SECRET)
    )
    
    if response.status_code == 200:
        try:
            json_response = response.json()
            return json_response['access_token']
        except requests.exceptions.JSONDecodeError:
            print("Error decoding JSON response: ", response.text)
            return None
    else:
        print(f"Request failed with status code {response.status_code}: {response.text}")
        return None

def lipa_na_mpesa_online(amount, phone_number, account_reference, transaction_desc):
    token = generate_token()
    if not token:
        print("Failed to obtain access token")
        return None

    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    password = base64.b64encode(
        f'{Config.MPESA_SHORTCODE}{Config.MPESA_PASSKEY}{timestamp}'.encode()
    ).decode('utf-8')

    payload = {
        'BusinessShortCode': Config.MPESA_SHORTCODE,
        'Password': password,
        'Timestamp': timestamp,
        'TransactionType': 'CustomerPayBillOnline',
        'Amount': amount,
        'PartyA': phone_number,
        'PartyB': Config.MPESA_SHORTCODE,
        'PhoneNumber': phone_number,
        'CallBackURL': 'https://b4ee-41-212-50-215.ngrok-free.app/callback',
        'AccountReference': account_reference,
        'TransactionDesc': transaction_desc,
    }

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }

    print("Payload:", payload)
    print("Headers:", headers)

    response = requests.post(
        'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest',
        json=payload,
        headers=headers
    )

    if response.status_code == 200:
        return response.json()
    else:
        print(f"STK Push request failed with status code {response.status_code}: {response.text}")
        return None
