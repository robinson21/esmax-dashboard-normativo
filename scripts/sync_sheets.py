#!/usr/bin/env python3
"""Read ESMAX Google Sheet and export as JSON for the dashboard."""
import json, os, sys
import requests
from urllib.request import Request, urlopen
from urllib.parse import urlencode, quote

SHEET_ID = os.environ['SHEET_ID']
API_KEY = os.environ.get('GOOGLE_API_KEY', '')  # Prefer API key (public sheets)
CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
REFRESH_TOKEN = os.environ.get('GOOGLE_REFRESH_TOKEN', '')

def get_access_token():
    """Refresh the OAuth token (fallback mode)."""
    data = urlencode({
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'refresh_token': REFRESH_TOKEN,
        'grant_type': 'refresh_token'
    }).encode()
    req = Request('https://oauth2.googleapis.com/token', data=data,
                  headers={'Content-Type': 'application/x-www-form-urlencoded',
                           'Accept': 'application/json'})
    resp = json.loads(urlopen(req).read())
    return resp['access_token']

def fetch_sheet(access_token, sheet_name, range_str):
    """Read a sheet tab via Google Sheets API v4."""
    encoded_range = quote(f"'{sheet_name}'!{range_str}")
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/{encoded_range}"
    req = Request(url, headers={'Authorization': f'Bearer {access_token}'})
    resp = json.loads(urlopen(req).read())
    rows = resp.get('values', [])
    if not rows:
        return []
    headers = rows[0]
    result = []
    for row in rows[1:]:
        obj = {}
        for i, h in enumerate(headers):
            obj[h] = row[i] if i < len(row) else ''
        result.append(obj)
    return result

def fetch_sheet_public(sheet_name, range_str):
    """Read a public sheet using API key (no OAuth needed)."""
    encoded_range = quote(f"'{sheet_name}'!{range_str}")
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/{encoded_range}?key={API_KEY}"
    r = requests.get(url, timeout=15)
    resp = r.json()
    rows = resp.get('values', [])
    if not rows:
        return []
    headers = rows[0]
    result = []
    for row in rows[1:]:
        obj = {}
        for i, h in enumerate(headers):
            obj[h] = row[i] if i < len(row) else ''
        result.append(obj)
    return result

def main():
    # Use API key if available (public sheet, no expiry)
    if API_KEY:
        fichas = fetch_sheet_public('Fichas de Cumplimiento', 'A1:L200')
        planes = fetch_sheet_public('Plan de Acción', 'A1:I200')
        resumen = fetch_sheet_public('Resumen Normas Aplicables', 'A1:G200')
    else:
        # Fallback: OAuth (will expire)
        token = get_access_token()
        fichas = fetch_sheet(token, 'Fichas de Cumplimiento', 'A1:L200')
        planes = fetch_sheet(token, 'Plan de Acción', 'A1:I200')
        resumen = fetch_sheet(token, 'Resumen Normas Aplicables', 'A1:G200')
    
    output = {
        'fichas': fichas,
        'planes': planes,
        'resumen': resumen,
        'last_sync': __import__('datetime').datetime.now().isoformat()
    }
    
    out_dir = os.environ.get('OUTPUT_DIR', 'docs')
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, 'data.json'), 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"Synced: {len(fichas)} fichas, {len(planes)} planes, {len(resumen)} resumen")
    if API_KEY:
        print("Mode: API Key (público, sin expiración)")
    else:
        print("Mode: OAuth (expira)")

if __name__ == '__main__':
    main()