"""Spatial CWA products: analyzed temperature grid and radar 1-hour quantitative precipitation forecast."""
import math,time,re
from collections import OrderedDict
from cwa_model import epoch,number
_GRID_CACHE=OrderedDict()

def twd67_coordinates(lat,lon,station=None):
    """Convert locally by the station-published TWD67/WGS84 delta; this avoids a datum-grid dependency."""
    try:
        coords={c.get('CoordinateName'):c for c in station.get('GeoInfo',{}).get('Coordinates',[])} if station else {}
        a,b=coords.get('WGS84'),coords.get('TWD67')
        if a and b:
            wlat,wlon=float(a['StationLatitude']),float(a['StationLongitude'])
            tlat,tlon=float(b['StationLatitude']),float(b['StationLongitude'])
            return lat+(tlat-wlat),lon+(tlon-wlon)
    except (KeyError,TypeError,ValueError):pass
    # Taiwan-local fallback determined from the CWA dual-coordinate station records.
    return lat+0.0017,lon-0.0082

def _values(key,text):
    key=(*key,hash(text))
    cached=_GRID_CACHE.get(key)
    if cached is not None:return cached
    vals=[]
    for token in text.replace('\n',',').split(','):
        token=token.strip()
        if token:
            try:vals.append(float(token))
            except ValueError:vals.append(math.nan)
    _GRID_CACHE[key]=vals
    while len(_GRID_CACHE)>4:_GRID_CACHE.popitem(last=False)
    return vals

def _cell(vals,nx,ny,start_lon,start_lat,res,lat,lon,invalid):
    ix=round((lon-start_lon)/res);iy=round((lat-start_lat)/res)
    if not (0<=ix<nx and 0<=iy<ny):return None
    value=vals[iy*nx+ix]
    if not math.isfinite(value) or value<=invalid:return None
    cell_lon=start_lon+ix*res;cell_lat=start_lat+iy*res
    km=111.2*math.hypot(cell_lat-lat,(cell_lon-lon)*math.cos(math.radians(lat)))
    return value,cell_lat,cell_lon,km

def temperature_analysis(product,lat,lon,station=None,now=None):
    try:
        d=product['cwaopendata']['dataset'];geo=d['GeoInfo'];dt=epoch(d['DataTime']['DateTime']);res=0.03
        now=time.time() if now is None else now
        if dt is None or not -300<=now-dt<=7200:return None
        left,bottom,right,top=map(float,[geo['BottomLeftLongitude'],geo['BottomLeftLatitude'],geo['TopRightLongitude'],geo['TopRightLatitude']])
        nx=round((right-left)/res)+1;ny=round((top-bottom)/res)+1
        text=d['Resource']['Content'];vals=_values(('temp',dt,len(text)),text)
        if len(vals)!=nx*ny:return None
        a,b=twd67_coordinates(lat,lon,station);hit=_cell(vals,nx,ny,left,bottom,res,a,b,-900)
        if not hit:return None
        value,clat,clon,km=hit
        if not -60<=value<=65:return None
        return {'temperature':value,'time':dt,'gridLatitudeTWD67':clat,'gridLongitudeTWD67':clon,'gridDistanceKm':round(km,3),'source':'CWA O-A0038-003 hourly analyzed temperature grid'}
    except (KeyError,TypeError,ValueError,IndexError):return None

def qpf_next_hour(product,lat,lon,station=None,now=None):
    try:
        d=product['cwaopendata']['dataset'];meta=d['datasetInfo']['parameterSet'];start=epoch(meta['DateTime']);now=time.time() if now is None else now
        if start is None or not -300<=now-start<=2400:return None
        nx,ny=int(meta['GridDimensionX']),int(meta['GridDimensionY']);res=float(meta['GridResolution'])
        left,bottom=float(meta['StartPointLongitude']),float(meta['StartPointLatitude'])
        origin='parameterSet'
        desc=d['contents'].get('contentDescription','')
        match=re.search(r'東經[為\s]*([0-9.]+).*?北緯[為\s]*([0-9.]+)',desc)
        if match:
            documented_lon,documented_lat=map(float,match.groups())
            if abs(documented_lon-left)<0.1 and abs(documented_lat-bottom)<0.1:
                left,bottom=documented_lon,documented_lat;origin='contentDescription explicit first cell'
        text=d['contents']['content'];vals=_values(('qpf',start,len(text)),text)
        if len(vals)!=nx*ny:return None
        a,b=twd67_coordinates(lat,lon,station);hit=_cell(vals,nx,ny,left,bottom,res,a,b,-90)
        if not hit:return None
        amount,clat,clon,km=hit
        if not 0<=amount<=500:return None
        return {'originDefinition':origin,'start':start,'end':start+3600,'amount':amount,'gridLatitudeTWD67':clat,'gridLongitudeTWD67':clon,'gridDistanceKm':round(km,3),'source':'CWA F-B0046-001 radar quantitative precipitation forecast, next 1 hour'}
    except (KeyError,TypeError,ValueError,IndexError):return None
