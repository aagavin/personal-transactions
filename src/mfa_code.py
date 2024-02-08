import os
from jmapc import Client, MailboxQueryFilterCondition, Ref, EmailQueryFilterCondition
from jmapc.methods import MailboxGet, MailboxQuery, EmailQuery, EmailGet
from datetime import datetime, timedelta, timezone

jmapc_client = Client.create_with_api_token(
    host="api.fastmail.com",
    api_token=os.getenv("JAMP_API_TOKEN")
)


def get_mfa_code():
    methods = [
        MailboxQuery(filter=MailboxQueryFilterCondition(name="Inbox")),
        MailboxGet(ids=Ref("/ids")),
    ]

    results = jmapc_client.request(methods)
    inbox_id = results[1].response.data[0].id

    mail_result = jmapc_client.request([
        EmailQuery(
            collapse_threads=True,
            filter=EmailQueryFilterCondition(
                in_mailbox=inbox_id,
                mail_from=os.getenv("ATB_MFA_EMAIL"),
                after=datetime.now(tz=timezone.utc) - timedelta(days=1)
            ),
            limit=1,
        ),
        EmailGet(ids=Ref("/ids"), fetch_text_body_values=True, fetch_html_body_values=False)
    ])

    email_text = mail_result[1].response.data[0].body_values['1.1'].value
    return email_text.split("Your one-time passcode is: ")[1].split(' </td>')[0]
