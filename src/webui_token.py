import json
import os
import random
import logging
from asyncio import sleep
from playwright.async_api import Response, async_playwright, TimeoutError
from src.mfa_code import get_mfa_code

token: str | None = None


async def token_handler(response: Response) -> None:
    if response.ok and "https://identity.auth.atb.com/oauth/token" in response.url:
        global token
        token_resp = await response.json()
        token = token_resp.get("access_token")
    pass


async def get_token():
    logging.info("Getting token using browser")
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context(viewport={"width": 2045, "height": 1000})
        await context.tracing.start(screenshots=True, snapshots=True)
        page = await context.new_page()
        await page.goto("https://personal.atb.com/", wait_until="networkidle")

        page.on("response", token_handler)

        username = page.locator("#rbw-login-form-input-username")
        password = page.locator("#rbw-login-form-input-password")
        submit_btn = page.locator("#rbw-login-form-button-submit")

        await username.focus()
        await username.press_sequentially(
            os.getenv("ATB_USERNAME"),
            delay=random.randint(45, 125)
        )
        await password.focus()
        await password.press_sequentially(
            os.getenv("ATB_PASSWORD"),
            delay=random.randint(45, 90)
        )
        await submit_btn.focus()
        await submit_btn.click()

        try:
            code_btn = await page.wait_for_selector("#esSendCode")
            await code_btn.click()
            mfa_text_box = await page.wait_for_selector("#code")
            mfa_code = get_mfa_code()
            await mfa_text_box.fill(mfa_code)
            await page.locator("#submitESCode").click()

        except TimeoutError:
            logging.debug(f"Timed out waiting for MFA Code, maybe no MFA Code\n{page.url}")

        await page.wait_for_selector("#account-overview-detail")
        while token is None:
            await sleep(3)
        if token is not None:
            with open('token.json', 'w', encoding='utf-8') as f:
                json.dump(token, f, ensure_ascii=False, indent=4)
            await context.tracing.stop(path="trace.zip")
            await page.close()
            await context.close()
            await browser.close()
            return token
