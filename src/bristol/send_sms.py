from twilio.rest import Client


def send_message(name, phone_number, plague_statement, account_sid, auth_token):
    sending_number = "whatsapp:+1" + phone_number
    client = Client(account_sid, auth_token)
    message = client.messages.create(
        body=f"You are {name} from the game of Bristol. {plague_statement} ",
        from_="whatsapp:+14155238886",
        to=sending_number,
    )

    print(f"Sent text message to {name}!\n")
    # print(message.sid)


def send_mingle_message(name, phone_number, mingle_statement, account_sid, auth_token):
    sending_number = "whatsapp:+1" + phone_number
    client = Client(account_sid, auth_token)
    message = client.messages.create(
        body=f"{name}, here are your symptoms after mingling: {mingle_statement} ",
        from_="whatsapp:+14155238886",
        to=sending_number,
    )

    print(f"Sent text message to {name}!\n")
    # message.sid


def send_remedy_message(name, phone_number, remedy_statement, account_sid, auth_token):
    sending_number = "whatsapp:+1" + phone_number
    client = Client(account_sid, auth_token)
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
    sending_number = "whatsapp:+1" + phone_number
    client = Client(account_sid, auth_token)
    message = client.messages.create(
        body=f"{name}, {remedy_statement} ",
        from_="whatsapp:+14155238886",
        to=sending_number,
    )

    print(f"Sent text message to {name}!\n")
