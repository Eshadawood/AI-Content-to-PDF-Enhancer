# app/extract.py
import requests
from readability import Document
from bs4 import BeautifulSoup
from typing import Tuple

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ContentEnhancer/1.0)"}

def fetch_html(url: str, timeout: int = 12) -> str:
    r = requests.get(url, headers=HEADERS, timeout=timeout)
    r.raise_for_status()
    return r.text

def extract_from_html(html: str, url: str = "") -> Tuple[str, str]:
    """
    Returns (title, text_content)
    """
    doc = Document(html)
    title = doc.short_title() or ""
    summary_html = doc.summary()
    # Convert to text using BeautifulSoup (keeps paragraphs)
    soup = BeautifulSoup(summary_html, "html.parser")
    # Replace multiple newlines, preserve paragraph breaks
    paragraphs = [p.get_text(separator=" ", strip=True) for p in soup.find_all(["p", "li", "h1","h2","h3"])]
    text_content = "\n\n".join([p for p in paragraphs if p])
    if not text_content:
        # Fallback: use entire page's visible text
        soup2 = BeautifulSoup(html, "html.parser")
        text_content = soup2.get_text(separator="\n").strip()
    return title.strip() or (BeautifulSoup(html, "html.parser").title.string if BeautifulSoup(html,"html.parser").title else "Untitled"), text_content
