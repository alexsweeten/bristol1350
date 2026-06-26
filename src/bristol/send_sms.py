def get_twilio_client(account_sid, auth_token):
    try:
        from twilio.rest import Client
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Twilio is required for SMS mode. Install dependencies or run with --test."
        ) from exc

    return Client(account_sid, auth_token)


def whatsapp_number(phone_number):
    return "whatsapp:+1" + str(phone_number)


def send_message(name, phone_number, plague_statement, account_sid, auth_token):
    sending_number = whatsapp_number(phone_number)
    client = get_twilio_client(account_sid, auth_token)
    message = client.messages.create(
        body=f"You are {name} from the game of Bristol. {plague_statement} ",
        from_="whatsapp:+14155238886",
        to=sending_number,
    )

    print(f"Sent text message to {name}!\n")
    # print(message.sid)


def send_mingle_message(name, phone_number, mingle_statement, account_sid, auth_token):
    sending_number = whatsapp_number(phone_number)
    client = get_twilio_client(account_sid, auth_token)
    message = client.messages.create(
        body=f"{name}, here are your symptoms after mingling: {mingle_statement} ",
        from_="whatsapp:+14155238886",
        to=sending_number,
    )

    print(f"Sent text message to {name}!\n")
    # message.sid


def send_remedy_message(name, phone_number, remedy_statement, account_sid, auth_token):
    sending_number = whatsapp_number(phone_number)
    client = get_twilio_client(account_sid, auth_token)
    message = client.messages.create(
        body=f"{name}, {remedy_statement} ",
        from_="whatsapp:+14155238886",
        to=sending_number,
    )

    print(f"Sent text message to {name}!\n")
    # print(message.sid)


def send_used_remedy_message(
    name, phone_number, remedy_statement, account_sid, auth_token
):
    sending_number = whatsapp_number(phone_number)
    client = get_twilio_client(account_sid, auth_token)
    message = client.messages.create(
        body=f"{name}, {remedy_statement} ",
        from_="whatsapp:+14155238886",
        to=sending_number,
    )

    print(f"Sent text message to {name}!\n")
