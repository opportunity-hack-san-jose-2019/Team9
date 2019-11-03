from twilio.rest import Client

def send_text(url , phone_number = "6692746841",start_time = None ,end_time = None,name = None):
    """
    Send a text message to user with event timings, RSVP url
    Input :
        RSVP url, User's phone number, start and end time, user's name. 
    Output :
        Text message is sent.
    """
    account_sid = 'ACa715401b07e6334a5a9c3a9ea11f0f38'
    auth_token = '667c1de2f6dc94d5a43159ebc28e9f23'
    client = Client(account_sid, auth_token)
    URL = url
    body = "Hi"
    if name is not None:                    # Add user name
        body += " "+name
    if start_time is not None:               # add event time
        body += " The interview event is scheduled from "+start_time
        if end_time is not None : 
            body += "till " + end_time
    else :
        body += "Your interview is scheduled."
    body += "Please click on the following URL to RSVP: "+ URL

    if phone_number[:1] != '+':           # add +1 
        phone_number = "+1"+phone_number

    message = client.messages.create(
                                body=body,
                                from_='+13058423258',
                                to=phone_number
                            )

    print(message.sid)


#send_text("6692746841",'https://www.google.com/',"10:30","12:15")
