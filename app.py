from flask import Flask, jsonify, request, render_template_string
import requests
import time

app = Flask(__name__)

# 手機優化版的前端 HTML 介面
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>手機台股即時看盤</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background-color: #f5f6fa; padding: 15px; }
        .container { max-width: 500px; margin: 0 auto; background: white; padding: 15px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
        h1 { text-align: center; font-size: 20px; color: #2f3640; margin-bottom: 15px; }
        
        /* 輸入區域 */
        .input-group { display: flex; gap: 8px; margin-bottom: 15px; }
        input { flex: 1; padding: 12px; font-size: 16px; border: 1px solid #dcdde1; border-radius: 8px; outline: none; -webkit-appearance: none; }
        button { padding: 12px 18px; font-size: 16px; background-color: #0097e6; color: white; border: none; border-radius: 8px; font-weight: bold; }
        
        /* 股票標籤 */
        .tag-container { margin-bottom: 15px; display: flex; flex-wrap: wrap; gap: 6px; }
        .stock-tag { background: #718093; color: white; padding: 6px 12px; border-radius: 20px; font-size: 14px; display: flex; align-items: center; }
        .stock-tag span { margin-left: 8px; font-size: 16px; font-weight: bold; cursor: pointer; }
        
        .status { font-size: 12px; color: #7f8c8d; text-align: center; margin-bottom: 15px; }
        
        /* 手機卡片式佈局（取代傳統大表格） */
        .stock-card { background: #f8f9fa; border: 1px solid #edf2f7; border-radius: 8px; padding: 12px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }
        .stock-info { display: flex; flex-direction: column; }
        .stock-name { font-size: 16px; font-weight: bold; color: #2f3640; }
        .stock-code { font-size: 12px; color: #7f8c8d; }
        .stock-time { font-size: 11px; color: #a5b1c2; margin-top: 4px; }
        
        .stock-prices { text-align: right; }
        .stock-current { font-size: 20px; font-weight: bold; color: #e17055; }
        .stock-hl { font-size: 12px; color: #7f8c8d; margin-top: 2px; }
        .txt-high { color: #eb4d4b; }
        .txt-low { color: #2ecc71; }
        
        .empty-tips { text-align: center; color: #a5b1c2; padding: 30px 0; font-size: 14px; }
    </style>
</head>
<body>

<div class="container">
    <h1>📊 台股即時自訂看盤</h1>
    
    <div class="input-group">
        <input type="number" id="stockInput" pattern="[0-9]*" inputmode="numeric" placeholder="輸入股號 (如 2330)">
        <button onclick="addStock()">新增</button>
    </div>

    <div class="tag-container" id="tagContainer"></div>
    <div class="status" id="statusMessage">請先新增股票代碼...</div>
    <div id="stockListContainer">
        <div class="empty-tips">暫無自訂股票，請在上方輸入</div>
    </div>
</div>

<script>
    let myStocks = [];
    let updateInterval = null;

    // 從手機瀏覽器本地儲存（LocalStorage）載入先前儲存的股票
    if(localStorage.getItem('myStocks')) {
        myStocks = JSON.parse(localStorage.getItem('myStocks'));
        renderTags();
        fetchStockData();
        resetTimer();
    }

    function addStock() {
        const input = document.getElementById('stockInput');
        const value = input.value.trim();
        if (value && !myStocks.includes(value)) {
            myStocks.push(value);
            localStorage.setItem('myStocks', JSON.stringify(myStocks)); // 儲存在手機裡
            input.value = '';
            renderTags();
            fetchStockData();
            resetTimer();
        }
    }

    function removeStock(code) {
        myStocks = myStocks.filter(s => s !== code);
        localStorage.setItem('myStocks', JSON.stringify(myStocks));
        renderTags();
        if (myStocks.length > 0) {
            fetchStockData();
            resetTimer();
        } else {
            document.getElementById('stockListContainer').innerHTML = '<div class="empty-tips">暫無自訂股票，請在上方輸入</div>';
            document.getElementById('statusMessage').innerText = "請先新增股票代碼...";
            clearInterval(updateInterval);
        }
    }

    function renderTags() {
        document.getElementById('tagContainer').innerHTML = myStocks.map(code => `
            <span class="stock-tag">${code}<span onclick="removeStock('${code}')">×</span></span>
        `).join('');
    }

    async function fetchStockData() {
        if (myStocks.length === 0) return;
        const statusMsg = document.getElementById('statusMessage');
        statusMsg.innerText = "更新中...";

        try {
            const response = await fetch(`/api/stock?stocks=${myStocks.join(',')}`);
            const data = await response.json();
            renderCards(data);
            statusMsg.innerText = `最後更新: ${new Date().toLocaleTimeString()} (每分自動更新)`;
        } catch (error) {
            statusMsg.innerText = "更新失敗，請確認網路連線";
        }
    }

    function renderCards(data) {
        const container = document.getElementById('stockListContainer');
        if (!data || data.length === 0) {
            container.innerHTML = '<div class="empty-tips" style="color:red;">找不到股票資料，請檢查股號</div>';
            return;
        }

        container.innerHTML = data.map(stock => `
            <div class="stock-card">
                <div class="stock-info">
                    <span class="stock-name">${stock.name || '未知'}</span>
                    <span class="stock-code">${stock.code}.TW</span>
                    <span class="stock-time">時間: ${stock.time}</span>
                </div>
                <div class="stock-prices">
                    <span class="stock-current">${stock.price}</span>
                    <div class="stock-hl">
                        高 <span class="txt-high">${stock.high}</span> | 
                        低 <span class="txt-low">${stock.low}</span>
                    </div>
                </div>
            </div>
        `).join('');
    }

    function resetTimer() {
        clearInterval(updateInterval);
        updateInterval = setInterval(fetchStockData, 5000);
    }
</script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/stock')
def get_stock():
    stocks_param = request.args.get('stocks', '')
    if not stocks_param:
        return jsonify([])
    
    query_list = [f"tse_{s}.tw" for s in stocks_param.split(',')]
    url = f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch={'|'.join(query_list)}&_={int(time.time()*1000)}"
    
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        output = []
        if 'msgArray' in data:
            for info in data['msgArray']:
                output.append({
                    'code': info.get('c'),
                    'name': info.get('n'),
                    'price': info.get('z', '-'),
                    'high': info.get('h', '-'),
                    'low': info.get('l', '-'),
                    'time': info.get('t', '-')
                })
        return jsonify(output)
    except Exception as e:
        return jsonify([]), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
