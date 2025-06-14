import asyncio
from typing import Dict, List
from urllib.parse import urljoin

import aiohttp
from bs4 import BeautifulSoup
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/dl", tags=["download"])
templates = Jinja2Templates(directory="templates")


class Config:
    MAX_PAGES = 1
    CHUNK_SIZE = 10  # 一度に処理するデータ量を制限


async def scrape_sukebei(
    session: aiohttp.ClientSession, url: str, params: dict | None = None
) -> List[Dict]:
    """
    Sukebei.nyaa.si の検索結果ページからデータを取得します。
    メモリ効率を考慮して、pandasの代わりにリストを使用します。
    """
    headers = {"User-Agent": "Mozilla/5.0"}
    async with session.get(url, params=params, headers=headers, timeout=30) as res:
        res.raise_for_status()
        html = await res.text()

    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select("table tbody tr")

    records = []
    for r in rows:
        tds = r.find_all("td")
        if len(tds) < 7:
            continue

        name = tds[1].get_text(strip=True)
        magnet_tag = tds[2].find("a", title="Magnet link")
        link = (
            magnet_tag["href"]
            if magnet_tag
            else (
                urljoin(url, tds[2].find("a", href=True)["href"])
                if tds[2].find("a", href=True)
                else ""
            )
        )

        record = {
            "Name": name,
            "Link": link,
            "Size": tds[3].get_text(strip=True),
            "Date": tds[4].get_text(strip=True),
            "Seeders": int(tds[5].get_text(strip=True)),
            "Leechers": int(tds[6].get_text(strip=True)),
            "Google_Search_URL": f"https://www.google.com/search?q={name}",
        }
        records.append(record)

    return records


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_progress(self, current: int, total: int):
        for connection in self.active_connections:
            await connection.send_json(
                {"type": "progress", "current": current, "total": total}
            )

    async def send_complete(self, data: List[Dict]):
        for connection in self.active_connections:
            await connection.send_json({"type": "complete", "data": data})


manager = ConnectionManager()


@router.get("/", response_class=HTMLResponse)
async def get_dl_page(request: Request):
    return templates.TemplateResponse("dl.html", {"request": request})


@router.websocket("/ws/dl")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        async with aiohttp.ClientSession() as session:
            all_records = []
            for page_id in range(1, Config.MAX_PAGES + 1):
                base_url = "https://sukebei.nyaa.si"
                params = "?f=2&c=2_2&q=-FC2"
                target_url = f"{base_url}/{params}&p={page_id}"

                records = await scrape_sukebei(session, target_url)
                all_records.extend(records)

                await manager.send_progress(page_id, Config.MAX_PAGES)
                await asyncio.sleep(0.1)

            # データを分割して送信
            for i in range(0, len(all_records), Config.CHUNK_SIZE):
                chunk = all_records[i : i + Config.CHUNK_SIZE]
                await manager.send_complete(chunk)
                await asyncio.sleep(0.1)  # クライアントの処理を待つ

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})
        manager.disconnect(websocket)
