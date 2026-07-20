import folium
from folium import Element

# ==========================================
# 1. 初始化地圖物件 (設定中心點與基礎圖層)
# ==========================================
m = folium.Map(
    location=[25.08, 121.52],  # 台北市中心
    zoom_start=13,
    tiles='OpenStreetMap',
    zoom_control=True          # 保持預設縮放控制項，確保穩定執行
)


# ==========================================
# 2. 你的地理圖資與圖層渲染邏輯
# ==========================================
# (你原本讀取 Shapefile、處理分區、填色的程式碼請放在這裡...)
# 例如：
# ... 讀取圖資 ...
# ... 迴圈加入多邊形圖層 ...


# ==========================================
# 3. 建立響應式浮動圖例 (電腦常駐、手機自動收納可點擊展開)
# ==========================================
legend_html = '''
<style>
    /* 1. 電腦版與預設樣式 */
    .info-legend {
        position: fixed;
        top: 70px; 
        left: 10px;
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        padding: 12px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-size: 14px;
        z-index: 9999;
        border: 1px solid #ccc;
    }

    .color-item {
        display: flex; 
        align-items: center; 
        margin-bottom: 8px;
    }
    
    .color-box {
        min-width: 16px; 
        height: 16px; 
        display: inline-block; 
        margin-right: 8px; 
        border-radius: 3px; 
        border: 1px solid #bbb;
    }

    /* 2. 手機版強制收納樣式 (寬度 768px 以下觸發) */
    @media (max-width: 768px) {
        .info-legend {
            top: 10px !important;
            left: auto !important;
            right: 10px !important;
            padding: 8px 12px !important;
            width: auto !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            cursor: pointer;
        }
        
        /* 隱藏詳細解說文字，手機版預設收起來 */
        .info-legend .legend-body {
            display: none !important;
        }
        
        /* 手機版標題加上點擊提示 */
        .info-legend h4::after {
            content: " 📋 點我看圖例";
            font-size: 12px;
            color: #2980B9;
            font-weight: normal;
        }
    }
</style>

<div class="info-legend" onclick="this.classList.toggle('expanded')">
    <h4 style="margin: 0; font-size: 14px; color: #333;">
        💅 台北美甲地圖
    </h4>
    
    <div class="legend-body" style="margin-top: 10px;">
        <div class="color-item">
            <span class="color-box" style="background-color: #2ECC71;"></span>
            <span style="color: #333;"><b>綠色：純商業區</b> (安全)</span>
        </div>
        <div class="color-item">
            <span class="color-box" style="background-color: #F39C12;"></span>
            <span style="color: #333;"><b>橙色：附條件/住三</b> (需查)</span>
        </div>
        <div class="color-item" style="margin-bottom: 0;">
            <span class="color-box" style="background-color: #95A5A6;"></span>
            <span style="color: #333;"><b>灰色：純住宅區</b> (雷區)</span>
        </div>
    </div>
</div>

<style>
    /* 當手機版點擊展開時的樣式切換 */
    @media (max-width: 768px) {
        .info-legend.expanded .legend-body {
            display: block !important;
            margin-top: 8px !important;
        }
        .info-legend.expanded h4::after {
            content: " (收起)";
            color: #e74c3c;
        }
    }
</style>
'''

# 將圖例掛載到地圖上
m.get_root().html.add_child(Element(legend_html))


# ==========================================
# 4. 輸出儲存為 index.html (對應 GitHub Pages 首頁)
# ==========================================
output_filename = 'index.html'
m.save(output_filename)
print(f"🎉 測試通過！地圖已成功生成：{output_filename}")