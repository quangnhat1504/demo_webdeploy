from fastapi import FastAPI, HTTPException
import httpx
import xmltodict
import yfinance as yf
import os

app = FastAPI(title="Gold Price API")

@app.get("/")
def read_root():
    return {"message": "Hệ thống API Giá Vàng đang hoạt động!"}

# 1. API lấy giá vàng SJC Việt Nam mới nhất
@app.get("/api/gold/sjc")
async def get_sjc_gold():
    url = "https://sjc.com.vn/xml/tygiavang.xml"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            
            # Chuyển đổi dữ liệu XML từ SJC sang định dạng JSON dễ đọc hơn
            data_dict = xmltodict.parse(response.text)
            
            # Trích xuất phần danh sách giá vàng
            gold_list = data_dict.get('root', {}).get('ratelist', {}).get('city', [])
            updated_time = data_dict.get('root', {}).get('ratelist', {}).get('@updated', '')
            
            return {
                "updated_time": updated_time,
                "data": gold_list
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi lấy dữ liệu SJC: {str(e)}")

# 2. API lấy lịch sử giá vàng thế giới (theo số ngày)
@app.get("/api/gold/history")
def get_gold_history(days: int = 7):
    if days > 365:
        raise HTTPException(status_code=400, detail="Chỉ hỗ trợ lấy tối đa 365 ngày để tối ưu hiệu suất.")
        
    try:
        # GC=F là mã giao dịch của Vàng trên Yahoo Finance
        gold = yf.Ticker("GC=F")
        hist = gold.history(period=f"{days}d")
        
        # Chuyển đổi dataframe của pandas thành dictionary (Ngày: Giá đóng cửa)
        history_data = {
            index.strftime('%Y-%m-%d'): round(row['Close'], 2)
            for index, row in hist.iterrows()
        }
        
        return {
            "symbol": "GC=F (Gold Futures)",
            "currency": "USD",
            "history": history_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi lấy dữ liệu lịch sử: {str(e)}")

if __name__ == "__main__":
    port_number = int(os.environ.get("PORT", 8000))
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port_number)