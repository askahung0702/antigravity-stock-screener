import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
import json

load_dotenv()

# Ensure we use an API Key if provided, otherwise the client might use default credentials
api_key = os.getenv("GEMINI_API_KEY", "")

# Initialize client conditionally
client = None
if api_key:
    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        print(f"Warning: Gemini Client could not be initialized. Error: {e}")
else:
    print("Warning: GEMINI_API_KEY not found in environment. Mocking AI Analysis.")

def analyze_news(news_text: str, stock_name: str) -> dict:
    if not client:
        return {
            "sentiment": "Neutral",
            "summary": ["AI 摘要服務目前無法使用 (未設定 API Key)"]
        }

    # Strict Grounding Prompt to prevent hallucination
    prompt = f"""
    你現在是一位嚴格依賴「已知事實」的專業財經分析師。
    我將提供給你關於「{stock_name}」的最新真實新聞文本。
    
    【你的任務】：
    1. 判斷這篇新聞對該公司的情緒 (Positive, Neutral, Negative)。
    2. 從文本中濃縮出 1 到 3 條最重要的摘要或風險提示。
    
    【絕對嚴格限制 (Anti-Hallucination)】：
    - 你「絕對不可以」使用你原本訓練資料中的知識來腦補或推測該公司的營收、產品或未來股價。
    - 所有的摘要「必須 100%」來自於我提供給你的新聞文本。
    - 如果新聞文本中沒有重點，請直接回答「無重大相關資訊」。
    - 回傳格式必須為嚴格的 JSON 格式。
    
    【新聞文本開始】：
    {news_text}
    【新聞文本結束】
    
    請以這個 JSON 格式回傳，不要有其他的文字：
    {{
        "sentiment": "Positive" | "Neutral" | "Negative",
        "summary": ["重點摘要1", "重點摘要2"]
    }}
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.0, # Use 0.0 to make it as deterministic and grounded as possible
                response_mime_type="application/json",
            )
        )
        # Parse the JSON response
        result = json.loads(response.text)
        return result
    except Exception as e:
        print(f"AI Generation Failed: {e}")
        return {
             "sentiment": "Neutral",
             "summary": ["AI 分析發生錯誤或超時"]
        }
