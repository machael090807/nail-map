import geopandas as gpd
import folium
from folium.plugins import Geocoder

# ==========================================
# 1. 設定檔案路徑 (對應你剛剛解壓縮的資料夾)
# ==========================================
file_path = '1150409細部計畫圖/細計-面.shp'

print("讀取圖資中，請稍候 (檔案較大可能需要幾十秒)...")
# 💡 防呆機制：台灣政府開放資料常混用 utf-8 或 Big5 編碼
try:
    gdf = gpd.read_file(file_path, encoding='utf-8')
except Exception as e:
    print("UTF-8 讀取失敗，自動切換為 Big5 編碼重試...")
    gdf = gpd.read_file(file_path, encoding='Big5')

# ==========================================
# 2. 座標系統轉換 (轉換為網頁地圖通用的 WGS84)
# ==========================================
print("轉換座標系統中...")
# 1. 如果圖資沒有定義座標系統，手動幫它宣告為台灣標準 TWD97 (EPSG:3826)
if gdf.crs is None:
    print("發現未定義座標系統，自動補上 TWD97 (EPSG:3826)...")
    gdf = gdf.set_crs(epsg=3826)

# 2. 接著再安全地轉換為網頁地圖通用的 WGS84 (EPSG:4326)
if gdf.crs != 'EPSG:4326':
    gdf = gdf.to_crs(epsg=4326)

# ==========================================
# 3. 自動偵測「土地使用分區」的欄位名稱
# ==========================================
# 政府圖資的欄位名稱常有變動，這裡寫一個自動抓取常見欄位名的邏輯
possible_columns = ['LUSE', 'ZONE', '使用分區', '分區', 'LANDUSE', '分區名稱']
zoning_column = None

for col in possible_columns:
    if col in gdf.columns:
        zoning_column = col
        break

# 如果找不到預設欄位，會印出所有欄位讓你手動填寫
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
        return 'transparent' # 處理空值
    
    # 🚫 1. 隱藏區：將道路、河川、公園等公共用地設為透明 (透出底圖)
    exclude_keywords = ['道路', '河川', '行水', '公園', '學校', '機關', '廣場', '綠地', '停車場', '車站', '捷運', '鐵路', '溝渠', '公共設施']
    if any(keyword in zoning_name for keyword in exclude_keywords):
        return 'transparent'
    
    # 🟢 2. 綠色：純商業區 (無敵區)
    elif any(keyword in zoning_name for keyword in ['第一種商業區', '第二種商業區', '第三種商業區', '第四種商業區']):
        return '#2ECC71'
        
    # 🟠 3. 橙色：附條件或變種區 (商三特、住三、住四等)
    elif '特' in zoning_name or any(keyword in zoning_name for keyword in ['第三種住宅區', '第四種住宅區']):
        return '#F39C12'
        
    # ⚪ 4. 灰色：純住宅、工業區、保護區等無法營業的街廓
    else:
        return '#95A5A6'

print("進行法規邏輯判定與填色中...")
gdf['color'] = gdf[zoning_column].apply(get_color)

# 🚀 神級優化：直接把被標記為 'transparent' 的區塊從資料裡刪掉！
# 這樣地圖就不會去畫馬路跟河川，除了能切出漂亮街廓，網頁跑起來也會超順！
gdf = gdf[gdf['color'] != 'transparent']

# ==========================================
# 5. 渲染 Folium 互動地圖
# ==========================================
# 初始化地圖，中心點設定在士林區周邊
# 初始化地圖，更換為路名最詳細的 OpenStreetMap
m = folium.Map(location=[25.0928, 121.5245], zoom_start=15, tiles='OpenStreetMap')

# 在地圖上加入「地址搜尋框」外掛
Geocoder(position='topleft').add_to(m)

print("生成地圖圖層中 (多邊形數量極大，這步驟大約需要 1~2 分鐘，請喝口水)...")
folium.GeoJson(
    gdf,
    style_function=lambda feature: {
        'fillColor': feature['properties']['color'],
        'color': '#333333',     # 邊界線顏色 (深灰)
        'weight': 0.5,          # 邊界線粗細
        'fillOpacity': 0.4      # 區塊透明度
    },
    # 設定滑鼠移過去時，顯示該地塊的分區名稱
    tooltip=folium.GeoJsonTooltip(
        fields=[zoning_column], 
        aliases=['法定土地分區:'],
        style=("background-color: white; color: #333333; font-family: arial; font-size: 14px; padding: 10px; border-radius: 5px;")
    )
).add_to(m)

# ==========================================
# 5.5 建立響應式浮動圖例面板 (完美適配手機與電腦)
# ==========================================
from folium import Element

legend_html = '''
<div style="
    position: fixed; 
    top: 70px;          /* 💡 往下移 70px，完美閃避左上角的搜尋框 */
    left: 10px;         
    max-width: 260px;   /* 💡 限制最大寬度，手機版絕不爆版 */
    width: calc(100% - 20px);
    max-height: 80vh;   /* 💡 限制高度，超出時自動出現內部捲軸 */
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
    <h4 style="margin-top: 0; margin-bottom: 10px; font-weight: bold; color: #333; font-size: 15px;">💅 台北美甲營登避雷地圖</h4>
    
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
'''

# 將寫好的 HTML 圖例掛載到地圖的根節點上
m.get_root().html.add_child(Element(legend_html))

# ==========================================
# 6. 輸出成果
# ==========================================
output_filename = 'shilin_nail_salon_map.html'
m.save(output_filename)
print(f"🎉 測試通過！地圖已成功生成：{output_filename}")
print("👉 請在 VS Code 左側檔案總管點擊該檔案，按右鍵選擇『Open with Live Server』，或直接將檔案拖入 Chrome 瀏覽器觀看成果！")