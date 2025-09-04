# app/main.py
import os
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from app.extract import fetch_html, extract_from_html
from app.llm import call_openai_enhance
from app.pdf_gen import build_pdf
from fastapi.responses import JSONResponse, StreamingResponse
from dotenv import load_dotenv
import time

# load .env in dev
load_dotenv()

app = FastAPI(title="AI Content-to-PDF Enhancer (Python)")

class EnhanceRequest(BaseModel):
    url: str
    mode: str = "both"       # 'summarize'|'expand'|'both'
    level: str = "detailed"  # 'brief'|'detailed'
    validate: bool = True

@app.post("/api/enhance")
async def enhance(req: EnhanceRequest):
    try:
        html = fetch_html(req.url)
        title, text = extract_from_html(html, req.url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error fetching/extracting URL: {e}")
    try:
        llm_out = call_openai_enhance(text, req.url, mode=req.mode, level=req.level, validate=req.validate)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM error: {e}")
    meta = {"url": req.url, "title": title, "timestamp": int(time.time()*1000)}
    return JSONResponse({"meta": meta, "output": llm_out})

@app.post("/api/pdf")
async def generate_pdf(payload: dict):
    # payload expected: {"meta": {...}, "output": {...}}
    meta = payload.get("meta", {})
    output = payload.get("output", {})
    try:
        pdf_bytes = build_pdf(meta, output)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")
    return StreamingResponse(iter([pdf_bytes]), media_type="application/pdf", headers={
        "Content-Disposition": f'attachment; filename="{(meta.get("title") or "enhanced").replace("/","_")}.pdf"'
    })
