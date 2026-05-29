#!/usr/bin/env python3
"""Read ESMAX Google Sheet and export as JSON for the dashboard."""
import json, os, sys
import googleapiclient.discovery
import google.oauth2.credentials

SHEET_ID = os.environ['SHEET_ID']

def get_creds():
    return google.oauth2.credentials.Credentials(
        token=None,
        refresh_token=os.environ['GOOGLE_REFRESH_TOKEN'],
        token_uri='https://oauth2.googleapis.com/token',
        client_id=os.environ['GOOGLE_CLIENT_ID'],
        client_secret=os.environ['GOOGLE_CLIENT_SECRET'],
        scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
    )

def sheet_to_dict(service, sheet_name, range_str):
    data = service.spreadsheets().values().get(
        spreadsheetId=SHEET_ID,
        range=f"'{sheet_name}'!{range_str}"
    ).execute()
    rows = data.get('values', [])
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
    service = googleapiclient.discovery.build('sheets', 'v4', credentials=get_creds())
    
    fichas = sheet_to_dict(service, 'Fichas de Cumplimiento', 'A1:L200')
    planes = sheet_to_dict(service, 'Plan de Acción', 'A1:I200')
    resumen = sheet_to_dict(service, 'Resumen Normas Aplicables', 'A1:G200')
    
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

if __name__ == '__main__':
    main()
