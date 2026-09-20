"""Pure validation/normalization of the bridge's pre-extracted CWA WRF points.
No network calls or file access: the caller supplies the bounded JSON product.
Rain accumulations are differenced only within one initialization cycle.
"""
import math

def _valid_row_time(row):
    initial=row.get('initialTime');lead=row.get('leadHours');forecast=row.get('forecastTime')
    return (not isinstance(initial,bool) and isinstance(initial,(int,float)) and math.isfinite(initial)
            and not isinstance(lead,bool) and isinstance(lead,(int,float)) and math.isfinite(lead) and lead==int(lead) and lead>=0 and int(lead)%6==0
            and not isinstance(forecast,bool) and isinstance(forecast,(int,float)) and math.isfinite(forecast)
            and forecast==initial+int(lead)*3600)

def normalize_nwp(product, county, town, now):
    if not isinstance(product, dict) or product.get('version') != 1:
        return None
    try:
        index = next(i for i, item in enumerate(product['towns'])
                     if item.get('county') == county and item.get('town') == town)
        all_rows = [row for rows in product['fields'].values() for row in rows if isinstance(row,dict) and _valid_row_time(row)]
        cycles = {row['initialTime'] for row in all_rows
                  if isinstance(row.get('initialTime'), (int, float))
                  and math.isfinite(row['initialTime']) and -300 <= now-row['initialTime'] <= 86400}
        if not cycles:
            return None
        cycle = max(cycles)
        pressure = []
        for row in product['fields'].get('pressure', []):
            if not isinstance(row,dict) or not _valid_row_time(row) or row.get('initialTime') != cycle:
                continue
            value = row['values'][index]
            if isinstance(value, (int, float)) and math.isfinite(value) and 850 <= value <= 1100:
                pressure.append({'forecastStart': row['forecastTime'], 'pressure': value})
        rain = []
        rows = sorted((row for row in product['fields'].get('apcp', []) if isinstance(row,dict) and _valid_row_time(row) and row.get('initialTime') == cycle),
                      key=lambda row: row['leadHours'])
        previous_time, previous_lead, previous_value = cycle, 0, 0.0
        for row in rows:
            value = row['values'][index]
            valid = isinstance(value, (int, float)) and math.isfinite(value) and 0 <= value <= 5000
            if valid and previous_value is not None and row['leadHours']-previous_lead == 6:
                difference = value-previous_value
                if -0.0002 <= difference <= 3000:
                    rain.append({'start': previous_time, 'end': row['forecastTime'],
                                 'amount': max(0.0, difference),
                                 'source': 'CWA WRF-3km APCP difference, same initialization; 6h water equivalent'})
            previous_time, previous_lead, previous_value = row['forecastTime'], row['leadHours'], value if valid else None
        reference = None
        if rows:
            reference = product.get('geometry', {}).get(rows[-1].get('geometry'), [])[index]
        return {'initialTime': cycle, 'generatedAt': product['generatedAt'],
                'county': county, 'town': town, 'grid': reference,
                'source': 'CWA M-A0064 WRF-3km GRIB2',
                'spatialScope': 'nearest model cell to CWA township reference',
                'points': sorted(pressure, key=lambda row: row['forecastStart']), 'rainIntervals': rain}
    except (KeyError, TypeError, ValueError, IndexError, StopIteration):
        return None
