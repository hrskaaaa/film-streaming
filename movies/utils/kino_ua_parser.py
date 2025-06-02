import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import logging
from typing import List, Dict, Optional
from playwright.async_api import async_playwright
import aiohttp

logger = logging.getLogger(__name__)

class KinoUAParser:
    def __init__(self):
        self.base_url = 'https://uakino.me'

    async def search_content(self, title: str, content_type: str = None) -> List[Dict]:
        try:
            html = await self._get_html_with_playwright(title)
            return self._parse_search_results(html, title)
        except Exception as e:
            logger.error(f"[search_content] Playwright search failed: {e}")
            return []

    async def _get_html_with_playwright(self, title: str) -> str:
        search_url = f"{self.base_url}/index.php?do=search&subaction=search&story={title}"
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            await page.goto(search_url, timeout=20000)
            await page.wait_for_selector('div.movie-item.short-item', timeout=10000)
            html = await page.content()
            await browser.close()
        return html

    def _parse_search_results(self, html_content: str, original_title: str) -> List[Dict]:
        soup = BeautifulSoup(html_content, 'html.parser')
        results = []
        search_results = soup.find_all('div', class_='movie-item short-item')

        for item in search_results:
            title_elem = item.find('a', class_='movie-title')
            item_title = title_elem.get_text(strip=True) if title_elem else 'Невідома назва'
            link = title_elem.get('href') if title_elem else None

            if not link or not link.startswith('http'):
                continue

            results.append({
                'title': item_title,
                'url': link,
                'similarity': self._calculate_similarity(original_title, item_title)
            })

        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results

    async def get_video_links(self, content_url: str) -> Dict:
        try:
            if content_url.endswith('.m3u8'):
                # Не HTML-сторінка, а медіаплейліст
                return {
                    'success': True,
                    'video_sources': [self._build_video_source(content_url)],
                    'total_sources': 1,
                    'quality': '1080p',
                    'source_url': content_url
                }

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                page = await context.new_page()
                await page.goto(content_url, timeout=30000)
                await page.wait_for_load_state('networkidle')
                html = await page.content()
                await browser.close()

            soup = BeautifulSoup(html, 'html.parser')
            video_link_tag = soup.find('link', attrs={'itemprop': 'video'})
            if video_link_tag and video_link_tag.get('value'):
                iframe_url = video_link_tag.get('value')
                if iframe_url.startswith('//'):
                    iframe_url = 'https:' + iframe_url

                real_video_url = await self._resolve_vod_url(iframe_url)
                if real_video_url:
                    return {
                        'success': True,
                        'video_sources': [self._build_video_source(real_video_url)],
                        'total_sources': 1,
                        'source_url': content_url
                    }

            return {
                'success': False,
                'error': 'Жодне відео не знайдено',
                'video_sources': [],
                'total_sources': 0
            }

        except Exception as e:
            logger.error(f"[get_video_links] Помилка: {e}")
            return {
                'success': False,
                'error': str(e),
                'video_sources': [],
                'total_sources': 0
            }

    async def _resolve_vod_url(self, vod_url: str) -> Optional[str]:
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                page = await context.new_page()
                await page.goto(vod_url, timeout=15000)
                await page.wait_for_selector('video[src]', timeout=10000)
                video_src = await page.eval_on_selector('video', 'el => el.getAttribute("src")')
                await browser.close()
            return video_src
        except Exception as e:
            logger.warning(f"[resolve_vod_url] Не вдалося отримати стрім: {e}")
            return None

    def _build_video_source(self, url: str) -> Dict:
        return {
            'url': url,
            'voice_name': 'iframe_vod',
            'quality': self._extract_quality_from_url(url),
            'data_id': '',
            'is_active': True,
            'is_watched': False,
            'text': url,
            'type': 'iframe_vod'
        }

    def _extract_quality_from_url(self, url: str) -> str:
        for pattern in [r'(\d+)p', r'(\d{3,4})x\d{3,4}']:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                return f"{match.group(1)}p"
        if '1080' in url: return '1080p'
        if '720' in url: return '720p'
        if '480' in url: return '480p'
        if '360' in url: return '360p'
        return 'Unknown'
    


    async def extract_quality_from_m3u8(url: str) -> str:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=10) as resp:
                        text = await resp.text()
                if 'RESOLUTION=1920x1080' in text or '1080' in text:
                    return '1080p'
                elif 'RESOLUTION=1280x720' in text or '720' in text:
                    return '720p'
                elif '480' in text:
                    return '480p'
                elif '360' in text:
                    return '360p'
            except Exception as e:
                logger.warning(f"[m3u8 parsing] Failed: {e}")
            return 'Unknown'


    def _calculate_similarity(self, title1: str, title2: str) -> float:
        title1, title2 = title1.lower().strip(), title2.lower().strip()
        if title1 == title2: return 1.0
        words1, words2 = set(title1.split()), set(title2.split())
        if not words1 or not words2: return 0.0
        return len(words1 & words2) / len(words1 | words2)

    async def get_best_video_link(self, content_url: str) -> Optional[str]:
        result = await self.get_video_links(content_url)
        if result['success'] and result['video_sources']:
            return result['video_sources'][0]['url']
        return None
