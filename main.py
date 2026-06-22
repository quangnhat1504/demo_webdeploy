from fastapi import FastAPI, HTTPException
from bs4 import BeautifulSoup
import httpx
import os
import yfinance as yf

app = FastAPI(title="Gold Price API")

@app.get("/api/gold/vn")
async def get_vn_gold():
    url = "https://webgia.com/gia-vang/sjc/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            table = soup.find('table', class_='table table-radius table-hover')
            if not table:
                raise ValueError("Không tìm thấy bảng dữ liệu.")
                
            gold_data = []
            
            # Trỏ thẳng vào phần <tbody> để bỏ qua phần tiêu đề <thead>
            tbody = table.find('tbody')
            if not tbody:
                raise ValueError("Không tìm thấy phần tbody của bảng.")
                
            rows = tbody.find_all('tr')
            
            current_location = ""
            
            for row in rows:
                th = row.find('th')
                if th:
                    current_location = th.text.strip()
                
                cols = row.find_all('td')
                
                if len(cols) >= 3:
                    loai_vang = cols[0].text.strip()
                    mua_vao = cols[1].text.strip()
                    ban_ra = cols[2].text.strip()
                    
                    # DATA CLEANING: Loại bỏ các chuỗi watermark chống scraping
                    # Xóa dấu chấm phân cách hàng nghìn và kiểm tra phần còn lại có phải là số (digit) hay không
                    is_valid_mua = mua_vao.replace('.', '').isdigit()
                    is_valid_ban = ban_ra.replace('.', '').isdigit()
                    
                    # Chỉ thêm vào kết quả nếu cả giá mua và giá bán đều là con số hợp lệ
                    if is_valid_mua and is_valid_ban:
                        gold_data.append({
                            "khu_vuc": current_location,
                            "loai_vang": loai_vang,
                            "mua_vao": mua_vao,
                            "ban_ra": ban_ra
                        })
                    
            return {
                "source": "webgia.com",
                "data": gold_data
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi thu thập dữ liệu: {str(e)}")
    
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