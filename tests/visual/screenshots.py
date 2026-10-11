"""Captureur visuel optionnel ; il reste silencieux si Playwright n'est pas installé."""

import asyncio
from pathlib import Path


async def capture():
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("Playwright n'est pas installé : captures ignorées.")
        return
    output = Path("docs/screenshots/module-3")
    output.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        page = await browser.new_page(viewport={"width": 390, "height": 844}, locale="fr-FR")
        await page.goto("http://127.0.0.1:8000/users/login/")
        await page.screenshot(path=output / "login-mobile.png", full_page=True)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(capture())
