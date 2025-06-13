import asyncio
from typing import Dict, List
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/dl", tags=["download"])
templates = Jinja2Templates(directory="templates")


class Config:
    MAX_PAGES = 5


def scrape_sukebei(url: str, params: dict | None = None) -> pd.DataFrame:
    """
    Sukebei.nyaa.si の検索結果ページから
    Name, Link(magnet 優先), Size, Date, Seeders, Leechers を取得して
    pandas.DataFrame を返します。
    """
    headers = {"User-Agent": "Mozilla/5.0"}  # 簡易的な UA
    res = requests.get(url, params=params, headers=headers, timeout=30)
    res.raise_for_status()

    soup = BeautifulSoup(res.text, "html.parser")
    rows = soup.select("table tbody tr")

    records = []
    for r in rows:
        tds = r.find_all("td")
        if len(tds) < 7:  # 列不足行をスキップ
            continue

        # --- Name ---
        name = tds[1].get_text(strip=True)

        # --- Magnet / Torrent link ---
        magnet_tag = tds[2].find("a", title="Magnet link")
        if magnet_tag:
            link = magnet_tag["href"]
        else:
            torrent_tag = tds[2].find("a", href=True)
            link = urljoin(url, torrent_tag["href"]) if torrent_tag else ""

        # --- Size ---
        size = tds[3].get_text(strip=True)

        # --- Date ---
        date = tds[4].get_text(strip=True)

        # --- Seeders & Leechers ---
        seeders = int(tds[5].get_text(strip=True))
        leechers = int(tds[6].get_text(strip=True))

        records.append(
            {
                "Name": name,
                "Link": link,
                "Size": size,
                "Date": date,
                "Seeders": seeders,
                "Leechers": leechers,
            }
        )

    return pd.DataFrame(records)


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
        dfs = []
        for page_id in range(1, Config.MAX_PAGES + 1):
            base_url = "https://sukebei.nyaa.si"
            params = "?f=2&c=2_2&q=-FC2"
            target_url = f"{base_url}/{params}&p={page_id}"
            df = scrape_sukebei(target_url)
            dfs.append(df)
            await manager.send_progress(page_id, Config.MAX_PAGES)
            await asyncio.sleep(0.1)  # 進捗を見やすくするための遅延

        df = pd.concat(dfs, ignore_index=True)
        await manager.send_complete(df.to_dict("records"))
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})
        manager.disconnect(websocket)
