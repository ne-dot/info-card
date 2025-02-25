from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import uvicorn
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.chat import search_and_respond, init_services
from models.search_result import SearchResult

app = FastAPI(title="搜索服务 API")

class SearchQuery(BaseModel):
    query: str

class SearchResponse(BaseModel):
    gpt_summary: dict
    google_results: List[dict]

@app.on_event("startup")
async def startup_event():
    init_services()

@app.post("/api/search", response_model=SearchResponse)
async def search(query: SearchQuery):
    try:
        results = search_and_respond(query.query)
        
        # 分离 GPT 和 Google 结果
        gpt_result = next(r for r in results if r.content is not None)
        google_results = [r for r in results if r.content is None]
        
        return SearchResponse(
            gpt_summary={
                "title": gpt_result.title,
                "content": gpt_result.content,
                "date": gpt_result.date
            },
            google_results=[{
                "title": r.title,
                "snippet": r.snippet,
                "link": r.link,
                "date": r.date
            } for r in google_results]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)