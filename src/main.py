import asyncio
import json
import logging
from os import path
from httpx import AsyncClient
from datetime import datetime
from .webui_token import get_token

client = AsyncClient()

BASE_URL = "https://personal.atb.com/api/atb-rebank-api-accounts-ts"
ACCOUNTS_URL = f"{BASE_URL}/accounts?quickActions=true&totals=true"
PENDING_ACCOUNTS_URL = f"{BASE_URL}/creditcards/[[]]/transactions?status=Pending"

logging.basicConfig(level=logging.INFO)


async def main():
    if not path.isfile('token.json'):
        logging.info("Token file not found. Creating, using playwright")
        token = await get_token()
    else:
        logging.info("Found token file")
        with open('token.json', 'r', encoding='utf-8') as token_file:
            token = json.load(token_file)
    while True:
        logging.info("Getting accounts")
        accounts = await client.get(ACCOUNTS_URL, headers={"Authorization": f"Bearer {token}"})
        logging.info(f"Accounts API response status: {accounts.status_code}")
        if accounts.status_code == 200:
            logging.info("Status is OK breaking Loop")
            break
        else:
            logging.info("Status code is error, getting token using playwright")
            token = await get_token()

    cc_account = list(filter(lambda x: (x['type'] == 'CreditCard'), accounts.json()['accounts'])).pop()['id']

    pending_transactions = await client.get(PENDING_ACCOUNTS_URL.replace('[[]]', cc_account), headers={"Authorization": f"Bearer {token}"})
    logging.info(f"Pending transactions API response status: {pending_transactions.status_code}")
    for transaction in pending_transactions.json()['transactions']:
        date = datetime.fromisoformat(transaction['transactionDate']).strftime("%B %d, %Y")
        print(f"{transaction['description']} -> ${transaction['netAmount']['value']} - {date}")


asyncio.run(main())
