from django.core.management.base import BaseCommand
from movies.models import Content
from urllib.parse import quote
import requests

HEADERS = {
    "Referer": "https://kinoua.com/",
    "User-Agent": "Mozilla/5.0"
}

def check_m3u8_exists(base_url):
    try:
        full_url = base_url + "index.m3u8"
        response = requests.get(full_url, headers=HEADERS, timeout=5)
        return response.status_code == 200
    except:
        return False

def generate_base_url(title):
    clean_title = title.lower().replace(" ", "_").replace(":", "").replace("!", "").replace(",", "")
    safe_title = quote(clean_title)
    return f"https://ashdi.vip/video29/1/new/{safe_title}/hls/BKeBlHaJk/tdmwrhBIwj/"

class Command(BaseCommand):
    help = "Автоматично оновлює поле source_stream_url для існуючих об'єктів"

    def handle(self, *args, **kwargs):
        updated = 0

        for content in Content.objects.filter(source_stream_url__isnull=True):
            base_url = generate_base_url(content.title)
            if check_m3u8_exists(base_url):
                content.source_stream_url = base_url
                content.save()
                updated += 1
                self.stdout.write(f"✔ Updated: {content.title}")
            else:
                self.stdout.write(f"✖ Not found: {content.title}")

        self.stdout.write(self.style.SUCCESS(f"\n🎉 Done! Total updated: {updated}"))
