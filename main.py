from fastapi import FastAPI, HTTPException
from bs4 import BeautifulSoup
import httpx
import os

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
            
            # Biến lưu trữ khu vực hiện tại để xử lý rowspan
            current_location = ""
            
            for row in rows:
                # 1. Kiểm tra xem dòng này có chứa thẻ <th> (chứa tên khu vực) không
                th = row.find('th')
                if th:
                    # Cập nhật khu vực mới
                    current_location = th.text.strip()
                
                # 2. Lấy các cột dữ liệu <td>
                cols = row.find_all('td')
                
                # [Inference] Theo cấu trúc HTML trong ảnh, các dòng dữ liệu hợp lệ sẽ luôn có ít nhất 3 thẻ <td> 
                # (Loại vàng, Mua vào, Bán ra), bất kể có thẻ <th> đi kèm hay không.
                if len(cols) >= 3:
                    gold_data.append({
                        "khu_vuc": current_location,
                        "loai_vang": cols[0].text.strip(),
                        "mua_vao": cols[1].text.strip(),
                        "ban_ra": cols[2].text.strip()
                    })
                    
            return {
                "source": "webgia.com",
                "data": gold_data
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi thu thập dữ liệu: {str(e)}")