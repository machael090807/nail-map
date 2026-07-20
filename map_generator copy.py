import geopandas as gpd
import folium

# ==========================================
# 1. 設定檔案路徑 (對應你剛剛解壓縮的資料夾)
# ==========================================
file_path = '1150409細部計畫圖/細計-面.shp'

print("讀取圖資中，請稍候 (檔案較大可能需要幾十秒)...")
try:
    gdf = gpd.read_file(file_path, encoding='utf-8')
except Exception as e:
    print("UTF-8 讀取失敗，自動切換為 Big5 編碼重試...")
    gdf = gpd.read_file(file_path, encoding='Big5')

# ==========================================
# 2. 座標系統轉換 (轉換為網頁地圖通用的 WGS84)
# ==========================================
print("轉換座標系統中...")
if gdf.crs is None:
    print("發現未定義座標系統，自動補上 TWD97 (EPSG:3826)...")
    gdf = gdf.set_crs(epsg=3826)

if gdf.crs != 'EPSG:4326':
    gdf = gdf.to_crs(epsg=4326)

# ==========================================
# 3. 自動偵測「土地使用分區」的欄位名稱
# ==========================================
possible_columns = ['LUSE', 'ZONE', '使用分區', '分區', 'LANDUSE', '分區名稱']
zoning_column = None

for col in possible_columns:
    if col in gdf.columns:
        zoning_column = col
        break

if not zoning_column:
    print(f"⚠️ 找不到預設的分區欄位。目前的欄位有：{gdf.columns.tolist()}")
    zoning_column = input("請輸入上面列表中的『分區名稱』欄位名: ")
else:
    print(f"✅ 成功偵測到分區欄位：{zoning_column}")

# ==========================================
# 4. 定義美甲店營登的 QA 判定邏輯 (核心業務邏輯)
# ==========================================
def get_color(zoning_name):
    if not isinstance(zoning_name, str):
        return 'transparent'
    
    exclude_keywords = ['道路', '河川', '行水', '公園', '學校', '機關', '廣場', '綠地', '停車場', '車站', '捷運', '鐵路', '溝渠', '公共設施']
    if any(keyword in zoning_name for keyword in exclude_keywords):
        return 'transparent'
    
    elif any(keyword in zoning_name for keyword in ['第一種商業區', '第二種商業區', '第三種商業區', '第四種商業區']):
        return '#2ECC71'
        
    elif '特' in zoning_name or any(keyword in zoning_name for keyword in ['第三種住宅區', '第四種住宅區']):
        return '#F39C12'
        
    else:
        return '#95A5A6'

print("進行法規邏輯判定與填色中...")
gdf['color'] = gdf[zoning_column].apply(get_color)
gdf = gdf[gdf['color'] != 'transparent']

# ==========================================
# 5. 渲染 Folium 互動地圖
# ==========================================
m = folium.Map(location=[25.0928, 121.5245], zoom_start=15, tiles='OpenStreetMap', zoom_control=False)

from folium import Element

# ==========================================
# 5.0 搜尋框樣式統一 (跟圖例框同樣的圓角、陰影、背景，電腦/手機都套用)
# ==========================================
geocoder_style_css = '''
<style>
.leaflet-control-geocoder {
    border-radius: 8px !important;
    border: 1px solid #ccc !important;
    background-color: rgba(255, 255, 255, 0.95) !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
    /* 💡 不能用 overflow: hidden，否則手機版的搜尋建議清單會被裁切，導致點不到選項 */
}
.leaflet-control-geocoder-form {
    border-radius: 8px !important;
    overflow: hidden; /* 只讓「輸入框本身」裁圓角，不影響下方彈出的建議清單 */
}
.leaflet-control-geocoder-form input {
    height: 40px !important;
    padding: 0 12px 0 40px !important;
    font-size: 16px !important;        /* 💡 手機瀏覽器 (iOS) 對小於16px的輸入框會自動放大畫面，統一設16px避免跑版 */
    box-sizing: border-box !important;
    border: none !important;
}
.leaflet-control-geocoder-icon {
    width: 34px !important;
    height: 40px !important;
    position: absolute !important;
    left: 0;
    top: 0;
    z-index: 2;
}
.leaflet-control-geocoder-results {
    box-sizing: border-box !important;
    border-radius: 0 0 8px 8px !important;
}
</style>
'''
m.get_root().html.add_child(Element(geocoder_style_css))

# ==========================================
# 5.1 手機版響應式調整 (電腦版完全不受影響)
# ==========================================
responsive_css = '''
<style>
@media (max-width: 600px) {
    #zoning-legend {
        top: auto !important;
        bottom: 10px !important;
        left: 10px !important;
        right: 10px !important;
        width: auto !important;
        max-width: none !important;
    }

    .leaflet-control-geocoder {
        width: calc(100vw - 20px) !important;
        max-width: none !important;
    }
    .leaflet-control-geocoder-form input {
        width: 100% !important;
        box-sizing: border-box !important;
    }
    .leaflet-control-geocoder-results {
        width: 100% !important;
        box-sizing: border-box !important;
    }
}
</style>
'''
m.get_root().html.add_child(Element(responsive_css))

geocoder_html = f'''
<link rel="stylesheet" href="https://unpkg.com/leaflet-control-geocoder/dist/Control.Geocoder.css" />
<script src="https://unpkg.com/leaflet-control-geocoder/dist/Control.Geocoder.js"></script>
<script>
window.addEventListener('load', function() {{
    var map = {m.get_name()};
    L.Control.geocoder({{
        position: 'topleft',
        collapsed: false,
        placeholder: '輸入地址',
        errorMessage: '找不到符合的地址',
        defaultMarkGeocode: true,
        geocoder: L.Control.Geocoder.nominatim({{
            geocodingQueryParams: {{
                'accept-language': 'zh-TW',
                countrycodes: 'tw'
            }}
        }})
    }}).addTo(map);
}});
</script>
'''
m.get_root().html.add_child(Element(geocoder_html))

print("生成地圖圖層中 (多邊形數量極大，這步驟大約需要 1~2 分鐘，請喝口水)...")
folium.GeoJson(
    gdf,
    style_function=lambda feature: {
        'fillColor': feature['properties']['color'],
        'color': '#333333',
        'weight': 0.3,
        'fillOpacity': 0.4
    },
    tooltip=folium.GeoJsonTooltip(
        fields=[zoning_column], 
        aliases=['法定土地分區:'],
        style=("background-color: white; color: #333333; font-family: arial; font-size: 14px; padding: 10px; border-radius: 5px;")
    )
).add_to(m)

# ==========================================
# 5.5 建立響應式浮動圖例面板 (完美適配手機與電腦)
# ==========================================
legend_html = '''
<div id="zoning-legend" style="
    position: fixed; 
    top: 10px;
    right: 10px;         
    max-width: 260px;
    width: calc(100% - 20px);
    max-height: 80vh;
    overflow-y: auto;   
    background-color: rgba(255, 255, 255, 0.95); 
    border: 1px solid #ccc; 
    z-index: 9999; 
    font-size: 14px;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    padding: 12px; 
    border-radius: 8px; 
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
">
    <div id="legend-header" style="display: flex; align-items: center; justify-content: space-between; cursor: pointer;">
        <h4 style="margin: 0; font-weight: bold; color: #333; font-size: 15px;">💅 台北美甲營登避雷地圖</h4>
        <span id="legend-toggle-icon" style="font-size: 16px; color: #333; margin-left: 8px; user-select: none;">▾</span>
    </div>

    <div id="legend-body" style="margin-top: 10px;">
        <div style="display: flex; align-items: center; margin-bottom: 8px;">
            <span style="background-color: #2ECC71; min-width: 16px; height: 16px; display: inline-block; margin-right: 8px; border-radius: 3px; border: 1px solid #bbb;"></span>
            <span style="color: #333; line-height: 1.3;"><b>綠色：純商業區</b> (安全牌，直接營登)</span>
        </div>
        
        <div style="display: flex; align-items: center; margin-bottom: 8px;">
            <span style="background-color: #F39C12; min-width: 16px; height: 16px; display: inline-block; margin-right: 8px; border-radius: 3px; border: 1px solid #bbb;"></span>
            <span style="color: #333; line-height: 1.3;"><b>橙色：附條件/住三</b> (需查回饋金或路寬)</span>
        </div>
        
        <div style="display: flex; align-items: center;">
            <span style="background-color: #95A5A6; min-width: 16px; height: 16px; display: inline-block; margin-right: 8px; border-radius: 3px; border: 1px solid #bbb;"></span>
            <span style="color: #333; line-height: 1.3;"><b>灰色：純住宅區</b> (大雷區，無法做美業)</span>
        </div>
    </div>
</div>

<script>
(function() {
    document.addEventListener('DOMContentLoaded', function() {
        var header = document.getElementById('legend-header');
        var body = document.getElementById('legend-body');
        var icon = document.getElementById('legend-toggle-icon');

        if (window.innerWidth < 600) {
            body.style.display = 'none';
            icon.textContent = '▸';
        }

        header.addEventListener('click', function() {
            var isHidden = body.style.display === 'none';
            body.style.display = isHidden ? 'block' : 'none';
            icon.textContent = isHidden ? '▾' : '▸';
        });
    });
})();
</script>
'''

m.get_root().html.add_child(Element(legend_html))

# ==========================================
# 6. 輸出成果
# ==========================================
output_filename = 'index.html'
m.save(output_filename)
print(f"🎉 測試通過！地圖已成功生成：{output_filename}")
print("👉 請在 VS Code 左側檔案總管點擊該檔案，按右鍵選擇『Open with Live Server』，或直接將檔案拖入 Chrome 瀏覽器觀看成果！")