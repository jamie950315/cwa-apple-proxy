from datetime import datetime
from typing import List, Optional, Dict, Tuple
from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ConfigDict
import json
import math
import aiohttp
import math
from enum import Enum
import asyncio
from dotenv import load_dotenv
import os

# 從 backend.env 載入環境變數
load_dotenv("backend.env")
CWA_API_Authorization = os.getenv("CWA_API_Authorization", "")

if not CWA_API_Authorization:
    raise ValueError("請於 backend.env 設定中央氣象局 API 授權金鑰 (CWA_API_Authorization) 後再啟動服務")

request_times = 0

# 建立 FastAPI 應用程式實例
app = FastAPI(
    title="YouBike 路線分析 API",
    description="提供騎乘路線天氣與站點分析服務",
    version="1.0.0"
)

# 設定 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允許所有來源
    allow_credentials=True,
    allow_methods=["*"],  # 允許所有 HTTP 方法
    allow_headers=["*"],  # 允許所有 headers
)

#uvicorn main:app --reload

# ============ Pydantic Models ============

class LabelLevel(str, Enum):
    GREEN = "good"
    BLUE = "normal"
    ORANGE = "bad"

class LabelInfo(BaseModel):
    """標籤資訊"""
    level: LabelLevel
    category: str
    content: str

class WeatherBlock(BaseModel):
    """天氣資訊區塊"""
    temperature: str = Field(..., description="溫度（攝氏）")
    rain_probability: str = Field(..., description="降雨機率 (0-100)")
    condition_label: str = Field(..., description="天氣狀況標籤")
    uvi: str = Field(..., description="紫外線指數")
    aqi: str = Field(..., description="空氣品質指數")
    phenomena: str = Field(..., description="特報現象")
    start_time: str = Field(..., description="特報開始時間")
    end_time: str = Field(..., description="特報結束時間")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "temperature": "25.5",
                "rain_probability": "30",
                "condition_label": "晴",
                "uvi": "6",
                "aqi": "45",
                "phenomena": "陸上強風",
                "start_time": "2025-11-08 10:29:00",
                "end_time": "2025-11-09 23:00:00"
            }
        }
    )

class NearbyStation(BaseModel):
    """鄰近站點資訊"""
    station_name: str = Field(..., description="站點名稱")
    station_no: str = Field(..., description="站點代碼")
    distance: float = Field(..., description="與目標位置的距離(公里)")

class StationBlock(BaseModel):
    """站點資訊基礎結構"""
    station_name: str = Field(..., description="站點名稱")
    station_no: str = Field(..., description="站點代碼")
    lat: float = Field(..., description="緯度")
    lng: float = Field(..., description="經度")
    nearby_stations: List[NearbyStation] = Field(default=[], description="鄰近站點列表")

class OriginStationBlock(StationBlock):
    """起點站資訊"""
    available_bikes: int = Field(..., description="可借車輛數量")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "station_name": "臺大土木系館",
                "station_no": "500106143",
                "lat": 25.01761,
                "lng": 121.53844,
                "available_bikes": 5,
                "nearby_stations": [
                    {
                        "station_name": "捷運公館站(2號出口)",
                        "station_no": "500106007",
                        "distance": 0.5
                    }
                ]
            }
        }
    )

class DestinationStationBlock(StationBlock):
    """終點站資訊"""
    available_slots: int = Field(..., description="可用車位數量")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "station_name": "捷運公館站(2號出口)",
                "lat": 25.01491,
                "lng": 121.53438,
                "available_slots": 8
            }
        }
    )

class LabelBlock(BaseModel):
    """分析結果標籤"""
    labels: List[LabelInfo] = Field(default=[], description="標籤列表")
    suitability: str = Field(..., description="騎乘適合程度")

class RouteAnalysisRequest(BaseModel):
    """API 請求資料結構"""
    origin: str = Field(..., description="起點站名稱")
    destination: str = Field(..., description="終點站名稱")
    originLat: float = Field(..., description="起點站緯度")
    originLng: float = Field(..., description="起點站經度")
    originNo: str = Field(..., description="起點站代碼")
    destLat: float = Field(..., description="終點站緯度")
    destLng: float = Field(..., description="終點站經度")
    destNo: str = Field(..., description="終點站代碼")
    gender: str = Field(..., description="性別 (M/F)")
    routes: List[Dict] = Field(..., description="路線資料列表")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "origin": "螢橋國中",
                "destination": "捷運臺電大樓站(1號出口)",
                "originLat": 25.01933,
                "originLng": 121.52582,
                "originNo": "500106143",
                "destLat": 25.0197,
                "destLng": 121.529,
                "destNo": "500106007",
                "gender": "M",
                "routes": [
                    {
                        "bounds": {
                            "north": 25.019740000000002,
                            "south": 25.018130000000003,
                            "east": 121.52897000000002,
                            "west": 121.52584000000002
                        },
                        "legs": [
                            {
                                "duration": {"text": "3 分鐘", "value": 182},
                                "steps": [
                                    {
                                        "path": [
                                            {"lat": 25.01931, "lng": 121.52584},
                                            {"lat": 25.0195, "lng": 121.52616}
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        }
    )

class RouteAnalysisBlock(BaseModel):
    """路線分析區塊"""
    construction_count: int = Field(..., description="行經路線上的施工點位數量")
    riding_time: int = Field(..., description="預計騎乘時間(分鐘)")
    carbon_reduction: float = Field(..., description="減碳量(公斤)")
    calories: float = Field(..., description="卡路里消耗(大卡)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "construction_count": 2,
                "riding_time": 15,
                "carbon_reduction": 0.196,
                "calories": 65.7
            }
        }
    )

class RouteAnalysisResponse(BaseModel):
    """API 回傳資料結構"""
    weather_block: WeatherBlock
    origin_station_block: OriginStationBlock
    destination_station_block: DestinationStationBlock
    label_block: LabelBlock
    route_analysis_block: RouteAnalysisBlock
    predictions: List[int] = Field(default=[], description="終點站預測可還車位數列表")

# ============ 工具函數 ============

def check_construction_near_path(path_points: List[Dict[str, float]], construction_data: List[Dict]) -> int:
    """
    檢查路徑附近的施工點位數量
    
    Args:
        path_points: 路徑點位列表，每個點包含 lat 和 lng
        construction_data: 施工點位資料列表
    
    Returns:
        int: 施工點位數量
    """
    # 用於記錄已計算過的施工點，避免重複計算
    counted_constructions = set()
    count = 0
    
    # 對路徑上的每個點
    for point in path_points:
        point_lat, point_lng = point["lat"], point["lng"]
        
        # 檢查每個施工點
        for construction in construction_data:
            construction_id = construction["properties"]["Ac_no"]
            if construction_id in counted_constructions:
                continue
                
            # 取得施工點座標
            coords = construction["geometry"]["coordinates"]
            construction_lat, construction_lng = coords[1], coords[0]
            
            # 計算距離
            distance = calculate_distance(
                point_lat, point_lng,
                construction_lat, construction_lng
            )
            
            # 如果距離小於 100 公尺（0.1 公里）
            if distance <= 0.1:
                count += 1
                counted_constructions.add(construction_id)
    
    return count

async def analyze_route(routes: List[Dict], gender: str) -> RouteAnalysisBlock:
    """
    分析路線資料，計算各項指標
    
    Args:
        routes: 路線資料列表
        gender: 性別 (M/F)
    
    Returns:
        RouteAnalysisBlock: 路線分析結果
    """
    print("=== 開始分析路線資訊 ===")
    print(f"性別: {gender}")
    print(f"路線數量: {len(routes) if routes else 0}")
    
    # 讀取施工資料
    try:
        with open("Todaywork.json", "r", encoding="utf-8-sig") as f:
            construction_data = json.load(f)["features"]
            print(f"已讀取施工資料，共 {len(construction_data)} 筆")
    except Exception as e:
        print(f"讀取施工資料時發生錯誤: {str(e)}")
        construction_data = []
    
    # 1. 驗證輸入參數
    if not routes:
        print("警告：未提供路線資料")
        routes = []
    
    if gender not in ["M", "F"]:
        print(f"警告：性別參數不正確 ({gender})，使用預設值 'M'")
        gender = "M"
    
    # 2. 初始化變數
    total_duration = 0
    all_path_points = []
    
    # 3. 遍歷所有路線
    for route in routes:
        try:
            for leg in route.get("legs", []):
                # 累加騎乘時間
                if "duration" in leg and "value" in leg["duration"]:
                    duration = leg["duration"]["value"]
                    total_duration += duration
                    print(f"騎乘時間: {duration} 秒")
                
                # 收集所有路徑點
                for step in leg.get("steps", []):
                    if "path" in step:
                        all_path_points.extend(step["path"])
        except Exception as e:
            print(f"處理路線資料時發生錯誤: {str(e)}")
            print(f"問題路線資料: {route}")
            continue
    
    # 3. 計算各項指標
    # 騎乘時間（秒轉分鐘，無條件進位）
    riding_time = math.ceil(total_duration / 60)
    
    # 計算施工點位數量
    construction_count = check_construction_near_path(all_path_points, construction_data)
    
    # 減碳量固定為 0.196
    carbon_reduction = 0.196
    
    # 計算卡路里消耗
    weight = 75.4 if gender == "M" else 58.7
    calories = 5 * weight * riding_time * 1.05 / 60
    
    # 準備回傳結果
    result = RouteAnalysisBlock(
        construction_count=construction_count,
        riding_time=riding_time,
        carbon_reduction=carbon_reduction,
        calories=round(calories, 1)  # 四捨五入到小數點後一位
    )
    
    print("=== 路線分析結果 ===")
    print(f"施工點數量: {result.construction_count}")
    print(f"預計騎乘時間: {result.riding_time} 分鐘")
    print(f"預計減碳量: {result.carbon_reduction} 公斤")
    print(f"預計消耗卡路里: {result.calories} 大卡")
    print("==================")
    
    return result

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    使用 Haversine 公式計算兩點間的距離（公里）
    """
    R = 6371  # 地球半徑（公里）
    
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c

async def fetch_youbike_data() -> Dict:
    """
    從 YouBike API 獲取即時站點資料
    每次請求都重新獲取，確保資料最新且避免 session 相關問題
    """
    url = "https://tcgbusfs.blob.core.windows.net/dotapp/youbike/v2/youbike_immediate.json"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    print(f"YouBike API 回應狀態碼: {response.status}")
                    raise HTTPException(status_code=503, detail="YouBike API 服務暫時無法使用")
    except aiohttp.ClientError as e:
        print(f"存取 YouBike API 時發生錯誤: {str(e)}")
        raise HTTPException(status_code=503, detail="無法連接至 YouBike API 服務")
    except Exception as e:
        print(f"未預期的錯誤: {str(e)}")
        raise HTTPException(status_code=503, detail="處理 YouBike 資料時發生錯誤")

def find_nearest_stations(stations: List[Dict], target_lat: float, target_lng: float, k: int = 4) -> List[Tuple[Dict, float]]:
    """
    找出距離目標位置最近的k個站點
    
    Args:
        stations (List[Dict]): 站點列表
        target_lat (float): 目標緯度
        target_lng (float): 目標經度
        k (int): 要返回的站點數量，預設為3
        
    Returns:
        List[Tuple[Dict, float]]: 站點和距離的列表，按距離排序
    """
    # 計算所有站點的距離
    stations_with_distance = []
    for station in stations:
        dist = calculate_distance(
            target_lat, target_lng,
            float(station['latitude']), float(station['longitude'])
        )
        stations_with_distance.append((station, dist))
    
    # 按距離排序並返回前k個
    return sorted(stations_with_distance, key=lambda x: x[1])[:k]

# ============ 分析函式 ============

async def fetch_weather_data(lat: float, lng: float) -> Dict:
    """
    從中央氣象局 API 獲取天氣資料
    """
    url = "https://opendata.cwa.gov.tw/linked/graphql"
    headers = {
        "Authorization": CWA_API_Authorization,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    query = """
    query aqi($lat: Float!, $lng: Float!) {
        aqi(longitude: $lng, latitude: $lat) {
            sitename, aqi, status,
            report {
                WeatherElement {
                    Weather,
                    AirTemperature,
                    UVIndex
                }
            },
            town {
                forecast72hr {
                    ProbabilityOfPrecipitation {
                        Time {
                            StartTime,
                            EndTime,
                            ProbabilityOfPrecipitation
                        }
                    }
                }
            }
        }
    }
    """
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, 
                                  headers=headers,
                                  json={"query": query, "variables": {"lat": lat, "lng": lng}}) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    print(f"氣象局 API 回應狀態碼: {response.status}")
                    raise HTTPException(status_code=503, detail="氣象局 API 服務暫時無法使用")
    except Exception as e:
        print(f"獲取氣象資料時發生錯誤: {str(e)}")
        raise HTTPException(status_code=503, detail="無法獲取氣象資料")

async def fetch_weather_warning() -> Dict:
    """
    從氣象局 API 獲取天氣警特報資料
    
    Returns:
        Dict: 天氣警特報資料
    """
    url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/W-C0033-001"
    params = {
        "Authorization": CWA_API_Authorization,
        "locationName": "臺北市"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    print(f"天氣警特報 API 回應狀態碼: {response.status}")
                    return None
    except Exception as e:
        print(f"獲取天氣警特報資料時發生錯誤: {str(e)}")
        return None

async def get_weather_analysis(lat: float, lng: float) -> WeatherBlock:
    """
    取得指定位置的天氣資訊
    
    Args:
        lat (float): 緯度
        lng (float): 經度
        
    Returns:
        WeatherBlock: 天氣資訊區塊
    """
    try:
        weather_data = await fetch_weather_data(lat, lng)
        
        if not weather_data.get('data', {}).get('aqi'):
            raise ValueError("無法獲取氣象站資料")
            
        station_data = weather_data['data']['aqi'][0]
        weather_element = station_data['report']['WeatherElement']
        
        # 處理天氣數據，檢查異常值
        temperature = str(weather_element['AirTemperature'])
        if temperature in ['-98', '-99', 'X']:
            print(f"警告：異常的溫度數值: {temperature}")
            temperature = "-"
            
        uvi = str(weather_element['UVIndex'])
        if uvi in ['-98', '-99', 'X']:
            print(f"警告：異常的紫外線指數: {uvi}")
            uvi = "-"
            
        weather = weather_element['Weather']
        if not weather or weather in ['-98', '-99', 'X']:
            print(f"警告：異常的天氣現象: {weather}")
            weather = "-"
            
        aqi = str(station_data['aqi'])
        if aqi in ['-98', '-99', 'X']:
            print(f"警告：異常的AQI數值: {aqi}")
            aqi = "-"
            
        # 獲取最近3小時的降雨機率
        prob_data = station_data['town']['forecast72hr']['ProbabilityOfPrecipitation']['Time']
        
        # 取得當前時間並加上時區資訊
        current_time = datetime.now().astimezone()
        
        # 尋找當前時間區段的降雨機率
        current_prob = None
        for time_slot in prob_data:
            # 解析時間並確保有時區資訊
            start_time = datetime.fromisoformat(time_slot['StartTime'])
            end_time = datetime.fromisoformat(time_slot['EndTime'])
            
            # 確保所有時間都是 aware datetime
            if start_time.tzinfo is None:
                start_time = start_time.astimezone()
            if end_time.tzinfo is None:
                end_time = end_time.astimezone()
            
            if start_time <= current_time <= end_time:
                current_prob = str(time_slot['ProbabilityOfPrecipitation'])
                # print(f"找到當前時段 {start_time.strftime('%Y-%m-%d %H:%M')} - {end_time.strftime('%H:%M')} 的降雨機率: {current_prob}%")
                break
        
        # 如果沒有找到當前時段，使用第一筆資料
        if current_prob is None:
            current_prob = str(prob_data[0]['ProbabilityOfPrecipitation'])
            first_start = datetime.fromisoformat(prob_data[0]['StartTime']).astimezone()
            first_end = datetime.fromisoformat(prob_data[0]['EndTime']).astimezone()
            print(f"未找到當前時段，使用第一筆資料 {first_start.strftime('%Y-%m-%d %H:%M')} - {first_end.strftime('%H:%M')} 的降雨機率: {current_prob}%")
            
        if current_prob in ['-98', '-99', 'X']:
            print(f"警告：異常的降雨機率: {current_prob}")
            current_prob = "-"
            
        # 獲取天氣警特報資料
        warning_data = await fetch_weather_warning()
        phenomena = "-"
        start_time = "-"
        end_time = "-"
        
        if warning_data and warning_data.get('success') == 'true':
            records = warning_data.get('records', {})
            locations = records.get('location', [])
            
            for location in locations:
                if location.get('locationName') == '臺北市':
                    hazards = location.get('hazardConditions', {}).get('hazards', [])
                    if hazards:
                        hazard = hazards[0]  # 取第一個警特報
                        phenomena = hazard['info'].get('phenomena', '-') + hazard['info'].get('significance', '-')
                        start_time = hazard['validTime'].get('startTime', '-')
                        end_time = hazard['validTime'].get('endTime', '-')
                    break
        
        print(f"""
=== 氣象資料日誌 ===
站點名稱: {station_data['sitename']}
溫度: {temperature}°C
天氣: {weather}
AQI: {aqi}
UV指數: {uvi}
降雨機率: {current_prob}%
特報現象: {phenomena}
特報時間: {start_time} 至 {end_time}
===================
        """)
        
        return WeatherBlock(
            temperature=temperature,
            condition_label=weather,
            rain_probability=current_prob,
            uvi=uvi,
            aqi=aqi,
            phenomena=phenomena,
            start_time=start_time,
            end_time=end_time
        )
            
    except Exception as e:
        print(f"處理氣象資料時發生錯誤: {str(e)}")
        # 發生錯誤時返回預設值
        return WeatherBlock(
            temperature="-",
            condition_label="-",
            rain_probability="-",
            uvi="-",
            aqi="-",
            phenomena="-",
            start_time="-",
            end_time="-"
        )

async def get_origin_station_status(
    station_name: str,
    lat: float,
    lng: float
) -> OriginStationBlock:
    """
    取得起點站資訊
    
    Args:
        station_name (str): 站點名稱
        lat (float): 緯度
        lng (float): 經度
        
    Returns:
        OriginStationBlock: 起點站資訊區塊
    """
    try:
        stations = await fetch_youbike_data()
        
        # 1. 先嘗試用站點名稱完全匹配
        exact_match = next(
            (s for s in stations if s['sna'].replace('YouBike2.0_', '') == station_name),
            None
        )
        
        if exact_match:
            # 尋找最近的3個站點
            nearest_stations = find_nearest_stations(stations, lat, lng)
            nearby_list = [
                NearbyStation(
                    station_name=s['sna'].replace('YouBike2.0_', ''),
                    station_no=s['sno'],
                    distance=round(dist * 1000)  # 轉換為公尺並四捨五入到整數
                )
                for s, dist in nearest_stations
                if s['sna'].replace('YouBike2.0_', '') != station_name  # 排除當前站點
            ][:3]  # 確保最多只有3個
            
            print(f"InfoTime: {exact_match['infoTime']}, Station: {station_name}, Available Bikes: {exact_match['available_rent_bikes']}")
            return OriginStationBlock(
                station_name=station_name,
                station_no=exact_match['sno'],
                lat=float(exact_match['latitude']),
                lng=float(exact_match['longitude']),
                available_bikes=int(exact_match['available_rent_bikes']),
                nearby_stations=nearby_list
            )
        
        # 2. 如果找不到完全匹配，尋找最近的站點
        nearest_stations = find_nearest_stations(stations, lat, lng)
        if nearest_stations:
            main_station, main_distance = nearest_stations[0]
            nearby_list = [
                NearbyStation(
                    station_name=s['sna'].replace('YouBike2.0_', ''),
                    station_no=s['sno'],
                    distance=round(dist * 1000)  # 轉換為公尺並四捨五入到整數
                )
                for s, dist in nearest_stations[1:4]  # 取接下來的3個站點作為鄰近站點
            ]
            
            warning_msg = (
                f"找不到名為 '{station_name}' 的站點。"
                f"已改用最近的站點：{main_station['sna'].replace('YouBike2.0_', '')}"
                f"（距離約 {round(main_distance * 1000)} 公尺）"
            )
            print(warning_msg)
            
            return OriginStationBlock(
                station_name=main_station['sna'].replace('YouBike2.0_', ''),
                station_no=main_station['sno'],
                lat=float(main_station['latitude']),
                lng=float(main_station['longitude']),
                available_bikes=int(main_station['available_rent_bikes']),
                nearby_stations=nearby_list
            )
        
        raise HTTPException(
            status_code=404,
            detail=f"無法找到符合的 YouBike 站點：{station_name}"
        )
            
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=503,
            detail="YouBike 資料服務暫時無法使用"
        )

async def get_destination_station_status(
    station_name: str,
    lat: float,
    lng: float
) -> DestinationStationBlock:
    """
    取得終點站資訊
    
    Args:
        station_name (str): 站點名稱
        lat (float): 緯度
        lng (float): 經度
        
    Returns:
        DestinationStationBlock: 終點站資訊區塊
    """
    try:
        stations = await fetch_youbike_data()
        
        # 1. 先嘗試用站點名稱完全匹配
        exact_match = next(
            (s for s in stations if s['sna'].replace('YouBike2.0_', '') == station_name),
            None
        )
        
        if exact_match:
            # 尋找最近的3個站點
            nearest_stations = find_nearest_stations(stations, lat, lng)
            nearby_list = [
                NearbyStation(
                    station_name=s['sna'].replace('YouBike2.0_', ''),
                    station_no=s['sno'],
                    distance=round(dist * 1000)  # 轉換為公尺並四捨五入到整數
                )
                for s, dist in nearest_stations
                if s['sna'].replace('YouBike2.0_', '') != station_name  # 排除當前站點
            ][:3]  # 確保最多只有3個
            
            print(f"InfoTime: {exact_match['infoTime']}, Station: {station_name}, Available Slots: {exact_match['available_return_bikes']}")
            return DestinationStationBlock(
                station_name=station_name,
                station_no=exact_match['sno'],
                lat=float(exact_match['latitude']),
                lng=float(exact_match['longitude']),
                available_slots=int(exact_match['available_return_bikes']),
                nearby_stations=nearby_list
            )
        
        # 2. 如果找不到完全匹配，尋找最近的站點
        nearest_stations = find_nearest_stations(stations, lat, lng)
        if nearest_stations:
            main_station, main_distance = nearest_stations[0]
            nearby_list = [
                NearbyStation(
                    station_name=s['sna'].replace('YouBike2.0_', ''),
                    station_no=s['sno'],
                    distance=round(dist * 1000)  # 轉換為公尺並四捨五入到整數
                )
                for s, dist in nearest_stations[1:4]  # 取接下來的3個站點作為鄰近站點
            ]
            
            warning_msg = (
                f"找不到名為 '{station_name}' 的站點。"
                f"已改用最近的站點：{main_station['sna'].replace('YouBike2.0_', '')}"
                f"（距離約 {round(main_distance * 1000)} 公尺）"
            )
            print(warning_msg)
            
            return DestinationStationBlock(
                station_name=main_station['sna'].replace('YouBike2.0_', ''),
                station_no=main_station['sno'],
                lat=float(main_station['latitude']),
                lng=float(main_station['longitude']),
                available_slots=int(main_station['available_return_bikes']),
                nearby_stations=nearby_list
            )
        
        raise HTTPException(
            status_code=404,
            detail=f"無法找到符合的 YouBike 站點：{station_name}"
        )
            
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=503,
            detail="YouBike 資料服務暫時無法使用"
        )

def calculate_suitability(labels: List[LabelInfo]) -> str:
    """
    根據標籤計算路線適合程度
    
    Args:
        labels (List[LabelInfo]): 標籤列表
        
    Returns:
        str: 適合程度描述
    """
    orange_count = sum(1 for label in labels if label.level == LabelLevel.ORANGE)
    green_count = sum(1 for label in labels if label.level == LabelLevel.GREEN)
    
    if orange_count == 0 and green_count >= 1:
        return "非常適合"
    elif orange_count >= 2:
        return "需要小心"
    else:
        return "適合"

def get_labels(
    weather: WeatherBlock,
    origin: OriginStationBlock,
    destination: DestinationStationBlock,
    route: RouteAnalysisBlock
) -> LabelBlock:
    """
    根據天氣與站點資訊產生分析標籤
    
    Args:
        weather (WeatherBlock): 天氣資訊
        origin (OriginStationBlock): 起點站資訊
        destination (DestinationStationBlock): 終點站資訊
        
    Returns:
        LabelBlock: 分析結果標籤
    """
    all_labels = []
    
    # 1. 起始站可租借數量 (橘)
    if origin.available_bikes != "-":
        if origin.available_bikes <= 3:
            all_labels.append(LabelInfo(
                level=LabelLevel.ORANGE,
                category="起始站狀態",
                content="起點站車數較少"
            ))
    
    # 2. 終點站空位數量 (橘)
    if destination.available_slots != "-":
        if destination.available_slots <= 3:
            all_labels.append(LabelInfo(
                level=LabelLevel.ORANGE,
                category="終點站狀態",
                content="終點站空位較少"
            ))
    
    # 3. 天氣特報 (橘)
    if weather.phenomena != "-":
        #如果天氣現象不包含特報字樣，則添加特報
        if "特報" not in weather.phenomena:
            weather.phenomena += "特報"
        all_labels.append(LabelInfo(
            level=LabelLevel.ORANGE,
            category="天氣特報",
            content=f"{weather.phenomena}"
        ))
    
    # 4. 天氣現象
    if weather.condition_label != "-":
        condition = weather.condition_label
        if "雨" in condition:
            all_labels.append(LabelInfo(
                level=LabelLevel.ORANGE,
                category="天氣現象",
                content="天雨路滑"
            ))
        elif "多雲" in condition or "陰" in condition:
            all_labels.append(LabelInfo(
                level=LabelLevel.BLUE,
                category="天氣現象",
                content="多雲舒適"
            ))
        elif "晴" in condition:
            all_labels.append(LabelInfo(
                level=LabelLevel.GREEN,
                category="天氣現象",
                content="天氣晴朗"
            ))
            
    
    # 5. 溫度 (橘)
    if weather.temperature != "-":
        try:
            temp = float(weather.temperature)
            if temp >= 30:
                all_labels.append(LabelInfo(
                    level=LabelLevel.ORANGE,
                    category="溫度",
                    content="小心中暑"
                ))
        except ValueError:
            pass
    
    # 6. AQI
    if weather.aqi != "-":
        try:
            aqi = float(weather.aqi)
            if aqi <= 50:
                all_labels.append(LabelInfo(
                    level=LabelLevel.GREEN,
                    category="空氣品質",
                    content="空氣品質良好"
                ))
            elif 51 <= aqi <= 100:
                all_labels.append(LabelInfo(
                    level=LabelLevel.BLUE,
                    category="空氣品質",
                    content="空氣品質普通"
                ))
            elif aqi > 100:
                all_labels.append(LabelInfo(
                    level=LabelLevel.ORANGE,
                    category="空氣品質",
                    content="空氣品質欠佳"
                ))
        except ValueError:
            pass
    
    # 7. UVI
    if weather.uvi != "-":
        try:
            uvi = float(weather.uvi)
            if 3 <= uvi <= 5:
                all_labels.append(LabelInfo(
                    level=LabelLevel.BLUE,
                    category="紫外線",
                    content="紫外線中等"
                ))
            elif uvi >= 6:
                all_labels.append(LabelInfo(
                    level=LabelLevel.ORANGE,
                    category="紫外線",
                    content="紫外線需防護"
                ))
        except ValueError:
            pass
    
    # 8. 道路施工
    if route.construction_count >= 1:
        all_labels.append(LabelInfo(
            level=LabelLevel.ORANGE,
            category="道路施工",
            content=f"小心道路施工"
        ))
    
    # 按照優先順序排序標籤
    # 1. 先按照等級排序：橘色 > 綠色 > 藍色
    # 2. 每個等級內按照定義的順序排序
    level_priority = {
        LabelLevel.ORANGE: 1,
        LabelLevel.GREEN: 2,
        LabelLevel.BLUE: 3
    }
    
    category_priority = {
        "起始站狀態": 1,
        "終點站狀態": 2,
        "天氣特報": 3,
        "天氣現象": 4,
        "溫度": 5,
        "空氣品質": 6,
        "紫外線": 7,
        "道路施工": 8
    }
    
    sorted_labels = sorted(
        all_labels,
        key=lambda x: (
            level_priority[x.level],
            category_priority[x.category]
        )
    )
    
    # 只取前三個標籤
    final_labels = sorted_labels[:3]
    
    # 計算適合程度
    suitability = calculate_suitability(final_labels)
    
    # 返回標籤和適合程度
    return LabelBlock(
        labels=final_labels,
        suitability=suitability
    )

# ============ API Endpoints ============

from bike_predictor import predict_station_availability

@app.post("/route/analysis", response_model=RouteAnalysisResponse)
async def route_analysis(
    request: RouteAnalysisRequest,
    raw_request: Request
) -> RouteAnalysisResponse:
    # 讀取並保存原始請求內容
    if False:  # 設定【保存 request 內容】開關 
        try:
            raw_body = await raw_request.body()
            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_path = f"request_logs/request_{current_time}.json"
            
            # 將原始請求內容寫入文件
            with open(log_path, "wb") as f:
                f.write(raw_body)
                
            print(f"請求內容已保存至: {log_path}")
        except Exception as e:
            print(f"保存請求內容時發生錯誤: {str(e)}")
            
    #==============================================
    # Demo用
    if False:  # 設定 【Demo 模式】開關
        global request_times
        demo_files = [
            "demo_data/非常適合.json",
            "demo_data/適合_道路施工.json",
            "demo_data/小心.json",
            "demo_data/特殊天氣.json",
        ]
        
        try:
            # 根據 request_times 選擇對應的檔案
            current_file = demo_files[request_times % len(demo_files)]
            with open(current_file, "r", encoding="utf-8") as f:
                demo_data = json.load(f)
            
            request_times += 1
            print(f"返回 Demo 資料: {current_file}")
            return demo_data
            
        except Exception as e:
            print(f"讀取 Demo 資料時發生錯誤: {str(e)}")
    #==============================================
    
    
    
    # 取得終點站預測資料
    predictions_list = []
    try:
        # 確保request.destNo為type=string_type
        predictions = predict_station_availability(str(request.destNo))
        for _, count in predictions:
            predictions_list.append(count)
        print(f"成功獲取站點 {request.destNo} 的預測資料")
    except ValueError as e:
        print(f"預測失敗: {e}")
        
    """
    分析自行車路線，提供天氣與站點資訊
    """
    # 輸出接收到的站點名稱
    print("====== 接收到的請求參數 ======")
    print(f"起點站: {request.origin} (編號: {request.originNo})")
    print(f"終點站: {request.destination} (編號: {request.destNo})")
    print("==============================")

    # 計算路線中點位置
    midpoint_lat = (request.originLat + request.destLat) / 2
    midpoint_lng = (request.originLng + request.destLng) / 2
    
    # 取得天氣資訊（使用路線中點位置）
    weather_block = await get_weather_analysis(midpoint_lat, midpoint_lng)
    
    # 取得起點站資訊
    origin_block = await get_origin_station_status(
        request.origin, request.originLat, request.originLng
    )
    
    # 取得終點站資訊
    destination_block = await get_destination_station_status(
        request.destination, request.destLat, request.destLng
    )
    
    try:
        # 分析路線資訊
        route_block = await analyze_route(request.routes, request.gender)
    except Exception as e:
        print(f"路線分析時發生錯誤: {str(e)}")
        # 返回預設值
        route_block = RouteAnalysisBlock(
            construction_count=0,
            riding_time=0,
            carbon_reduction=0.196,
            calories=0.0
        )
    
    # 產生分析標籤
    label_block = get_labels(weather_block, origin_block, destination_block, route_block)
    
    # 回傳完整分析結果
    return RouteAnalysisResponse(
        weather_block=weather_block,
        origin_station_block=origin_block,
        destination_station_block=destination_block,
        label_block=label_block,
        route_analysis_block=route_block,
        predictions=predictions_list
    )


# ======================
# 健康檢查 / 測試用
# ======================

@app.get("/")
async def root():
    return {"message": "BikeFlow API is running 🚴‍♂️"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
