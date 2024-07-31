import os
import re
import colorama
from colorama import Fore, Style
from twilio.rest import Client as TwilioClient
from twilio.base.exceptions import TwilioException
import vonage
import messagebird

colorama.init()

def print_header():
    """Print the header and initial information."""
    header = """
MPS-SENDER - SMS Sender with Twilio, Nexmo, and MessageBird API

- EMAIL: your-email@example.com
- TELE: @yourTelegramHandle
- CONTACT: your-contact-number
    """
    print(Fore.RED + header + Style.RESET_ALL)

def load_file(file_path):
    """Load contents from a file."""
    with open(file_path, 'r') as file:
        return file.read().strip().splitlines()

def save_file(file_path, data):
    """Save data to a file."""
    with open(file_path, 'w') as file:
        file.write(data)

def get_api_credentials(provider):
    """Load API credentials from a file."""
    credentials_path = f'api_credentials/{provider}_credentials.txt'
    if not os.path.exists(credentials_path):
        return {}
    credentials = load_file(credentials_path)
    if provider == 'twilio' and len(credentials) != 3:
        print("Error: Invalid Twilio credentials file.")
        return {}
    elif provider == 'nexmo' and len(credentials) != 2:
        print("Error: Invalid Nexmo credentials file.")
        return {}
    elif provider == 'messagebird' and len(credentials) != 2:
        print("Error: Invalid MessageBird credentials file.")
        return {}
    return {line.split('=')[0]: line.split('=')[1] for line in credentials}

def set_api_credentials(provider):
    """Prompt user to input API credentials and save them."""
    if provider == 'twilio':
        print("[INFO]: Enter your Twilio API credentials.")
        account_sid = input("Account SID: ")
        auth_token = input("Auth Token: ")
        from_phone_number = input("Twilio Phone Number: ")

        credentials = f"ACCOUNT_SID={account_sid}\nAUTH_TOKEN={auth_token}\nFROM_PHONE_NUMBER={from_phone_number}"
        save_file('api_credentials/twilio_credentials.txt', credentials)
        
        # Verify credentials
        try:
            client = TwilioClient(account_sid, auth_token)
            account = client.api.v2010.accounts(account_sid).fetch()
            if account:
                print(f"{Fore.GREEN}[SUKSES]{Style.RESET_ALL}: API credentials are valid.")
                return True
        except TwilioException as e:
            print(f"{Fore.RED}[GAGAL]{Style.RESET_ALL}: Failed to authenticate with Twilio API: {e}")
            return False
    
    elif provider == 'nexmo':
        print("[INFO]: Enter your Nexmo API credentials.")
        api_key = input("API Key: ")
        api_secret = input("API Secret: ")

        credentials = f"API_KEY={api_key}\nAPI_SECRET={api_secret}"
        save_file('api_credentials/nexmo_credentials.txt', credentials)
        
        # Verify credentials
        client = vonage.Client(key=api_key, secret=api_secret)
        try:
            response = client.account.get_balance()
            if response:
                print(f"{Fore.GREEN}[SUKSES]{Style.RESET_ALL}: API credentials are valid.")
                return True
        except vonage.errors.AuthenticationError:
            print(f"{Fore.RED}[GAGAL]{Style.RESET_ALL}: Failed to authenticate with Nexmo API.")
            return False

    elif provider == 'messagebird':
        print("[INFO]: Enter your MessageBird API credentials.")
        api_key = input("API Key: ")
        originator = input("Originator: ")

        credentials = f"API_KEY={api_key}\nORIGINATOR={originator}"
        save_file('api_credentials/messagebird_credentials.txt', credentials)
        
        # Verify credentials
        client = messagebird.Client(api_key)
        try:
            balance = client.balance()
            if balance:
                print(f"{Fore.GREEN}[SUKSES]{Style.RESET_ALL}: API credentials are valid.")
                return True
        except messagebird.client.ErrorException:
            print(f"{Fore.RED}[GAGAL]{Style.RESET_ALL}: Failed to authenticate with MessageBird API.")
            return False

def get_message():
    """Load the SMS message from a file."""
    message_path = 'messages/message.txt'
    if not os.path.exists(message_path):
        return ""
    return load_file(message_path)[0]

def set_message():
    """Prompt user to input the SMS message and save it."""
    print("[INFO]: Enter the SMS message:")
    message = input("Message: ")
    
    save_file('messages/message.txt', message)
    print(f"{Fore.GREEN}[SUKSES]{Style.RESET_ALL}: Message saved.")

def validate_number(number):
    """Validate if the phone number matches Indonesian format."""
    return re.match(r'^628\d{10}$', number) is not None

def send_sms_twilio(client, from_number, to_number, message):
    """Send an SMS message using Twilio API."""
    try:
        message_response = client.messages.create(
            body=message,
            from_=from_number,
            to=to_number
        )
        return True
    except TwilioException as e:
        return str(e)

def send_sms_nexmo(client, from_number, to_number, message):
    """Send an SMS message using Nexmo API."""
    try:
        response = client.sms.send_message({
            'from': from_number,
            'to': to_number,
            'text': message,
        })
        if response["messages"][0]["status"] == "0":
            return True
        else:
            return response["messages"][0]["error-text"]
    except vonage.errors.ClientError as e:
        return str(e)

def send_sms_messagebird(client, from_number, to_number, message):
    """Send an SMS message using MessageBird API."""
    try:
        message_response = client.message_create(
            originator=from_number,
            recipients=[to_number],
            body=message
        )
        return True
    except messagebird.client.ErrorException as e:
        return str(e)

def print_output(number, valid_status, info_status, ket_status, balance=None):
    """Print the output in a formatted manner."""
    print("____________________________________________________")
    print(f"[NOMOR]: {number} {valid_status}")
    print(f"[INFO]: {info_status}")
    if balance is not None:
        print(f"[KET]: {ket_status}, SISA SALDO: {balance}")
    else:
        print(f"[KET]: {ket_status}")
    print("____________________________________________________")

def validate_api_credentials(provider, client):
    """Validate the API credentials before sending SMS."""
    if provider == 'twilio':
        try:
            account_sid = get_api_credentials(provider)['ACCOUNT_SID']
            account = client.api.v2010.accounts(account_sid).fetch()
            return account is not None
        except TwilioException:
            return False
    elif provider == 'nexmo':
        try:
            response = client.account.get_balance()
            return response is not None
        except vonage.errors.AuthenticationError:
            return False
    elif provider == 'messagebird':
        try:
            balance = client.balance()
            return balance is not None
        except messagebird.client.ErrorException:
            return False

def main():
    """Main function to run the SMS sending script."""
    print_header()
    
    provider = None
    client = None
    
    while True:
        print("\n[1] SET API")
        print("[2] SET PESAN")
        print("[3] MULAI")
        print("[4] EXIT")
        choice = input("Pilih opsi: ")

        if choice == '1':
            print("\nPilih provider:")
            print("[1] TWILIO")
            print("[2] NEXMO")
            print("[3] MESSAGEBIRD")
            provider_choice = input("Pilih provider: ")

            if provider_choice == '1':
                provider = 'twilio'
                if not get_api_credentials(provider):
                    if set_api_credentials(provider):
                        client = TwilioClient(get_api_credentials(provider)['ACCOUNT_SID'], get_api_credentials(provider)['AUTH_TOKEN'])
            elif provider_choice == '2':
                provider = 'nexmo'
                if not get_api_credentials(provider):
                    if set_api_credentials(provider):
                        client = vonage.Client(key=get_api_credentials(provider)['API_KEY'], secret=get_api_credentials(provider)['API_SECRET'])
            elif provider_choice == '3':
                provider = 'messagebird'
                if not get_api_credentials(provider):
                    if set_api_credentials(provider):
                        client = messagebird.Client(get_api_credentials(provider)['API_KEY'])
        elif choice == '2':
            set_message()
        elif choice == '3':
            if provider is None:
                print(f"{Fore.RED}[ERROR]{Style.RESET_ALL}: Please set the API credentials first.")
                continue

            print("\nPILIH PROVIDER YANG AKAN DI GUNAKAN UNTUK MEMULAI SMS:")
            print("[1] TWILIO")
            print("[2] NEXMO")
            print("[3] MESSAGEBIRD")
            provider_choice = input("Pilih provider: ")

            if provider_choice == '1':
                provider = 'twilio'
                client = TwilioClient(get_api_credentials(provider)['ACCOUNT_SID'], get_api_credentials(provider)['AUTH_TOKEN'])
                print(f"\n{Fore.GREEN}MEMULAI SENDING SMS MENGGUNAKAN PROVIDER TWILIO{Style.RESET_ALL}")
            elif provider_choice == '2':
                provider = 'nexmo'
                client = vonage.Client(key=get_api_credentials(provider)['API_KEY'], secret=get_api_credentials(provider)['API_SECRET'])
                print(f"\n{Fore.GREEN}MEMULAI SENDING SMS MENGGUNAKAN PROVIDER NEXMO{Style.RESET_ALL}")
            elif provider_choice == '3':
                provider = 'messagebird'
                client = messagebird.Client(get_api_credentials(provider)['API_KEY'])
                print(f"\n{Fore.GREEN}MEMULAI SENDING SMS MENGGUNAKAN PROVIDER MESSAGEBIRD{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}[ERROR]{Style.RESET_ALL}: Invalid provider choice.")
                continue

            # Validate API credentials
            if not validate_api_credentials(provider, client):
                print(f"{Fore.RED}[ERROR]{Style.RESET_ALL}: SILAHKAN SET API DENGAN BENAR DAN VALID")
                continue

            # Load message
            message = get_message()
            if not message:
                print(f"{Fore.RED}[ERROR]{Style.RESET_ALL}: No message found. Please set a message first.")
                continue

            # Load target numbers from file
            numbers_path = 'target_numbers/numbers.txt'
            if not os.path.exists(numbers_path):
                print(f"{Fore.RED}[ERROR]{Style.RESET_ALL}: Target numbers file not found. Please set target numbers first.")
                continue

            target_numbers = load_file(numbers_path)
            if not target_numbers:
                print(f"{Fore.RED}[ERROR]{Style.RESET_ALL}: No target numbers found in file.")
                continue

            for number in target_numbers:
                is_valid = validate_number(number)
                valid_status = f"{Fore.GREEN}VALID{Style.RESET_ALL}" if is_valid else f"{Fore.RED}TIDAK VALID{Style.RESET_ALL}"

                if is_valid:
                    if provider == 'twilio':
                        send_result = send_sms_twilio(client, get_api_credentials(provider)['FROM_PHONE_NUMBER'], number, message)
                    elif provider == 'nexmo':
                        send_result = send_sms_nexmo(client, get_api_credentials(provider)['FROM_PHONE_NUMBER'], number, message)
                    elif provider == 'messagebird':
                        send_result = send_sms_messagebird(client, get_api_credentials(provider)['ORIGINATOR'], number, message)

                    if send_result == True:
                        info_status = f"{Fore.GREEN}BERHASIL KIRIM !!{Style.RESET_ALL}"
                        ket_status = "SALDO CUKUP"
                    else:
                        info_status = f"{Fore.RED}GAGAL KIRIM !!{Style.RESET_ALL}"
                        ket_status = send_result
                else:
                    info_status = f"{Fore.RED}GAGAL KIRIM !!{Style.RESET_ALL}"
                    ket_status = "NOMOR TIDAK VALID"

                print_output(number, valid_status, info_status, ket_status)

        elif choice == '4':
            print("[INFO]: Exiting program.")
            break
        else:
            print(f"{Fore.RED}[ERROR]{Style.RESET_ALL}: Invalid option. Please select a valid option.")

if __name__ == "__main__":
    main()
