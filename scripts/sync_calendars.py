#!/usr/bin/env python3
from __future__ import annotations
import json, os, re, sys, urllib.request
from datetime import datetime, timezone
from pathlib import Path

OUTPUT = Path(os.getenv('OUTPUT', 'data/calendar.json'))
AIRBNB = os.getenv('AIRBNB_ICAL_URL', '').strip()
BOOKING = os.getenv('BOOKING_ICAL_URL', '').strip()

def unfold(text: str) -> list[str]:
    lines: list[str] = []
    for line in text.replace('\r\n','\n').replace('\r','\n').split('\n'):
        if line.startswith((' ','\t')) and lines: lines[-1] += line[1:]
        else: lines.append(line)
    return lines

def fetch(url: str, source: str) -> list[dict[str,str]]:
    request = urllib.request.Request(url, headers={'User-Agent':'ParisAuriolCalendar/1.0'})
    with urllib.request.urlopen(request, timeout=30) as response:
        text = response.read().decode('utf-8','replace')
    events: list[dict[str,str]] = []
    current: dict[str,str] | None = None
    for line in unfold(text):
        if line == 'BEGIN:VEVENT': current = {}
        elif line == 'END:VEVENT' and current is not None:
            if current.get('start') and current.get('end') and current['start'] < current['end']:
                current['source'] = source
                events.append(current)
            current = None
        elif current is not None:
            if line.startswith('DTSTART'):
                value = line.split(':',1)[-1]
                digits = re.sub(r'\D','',value)
                if len(digits) >= 8: current['start'] = f'{digits[:4]}-{digits[4:6]}-{digits[6:8]}'
            elif line.startswith('DTEND'):
                value = line.split(':',1)[-1]
                digits = re.sub(r'\D','',value)
                if len(digits) >= 8: current['end'] = f'{digits[:4]}-{digits[4:6]}-{digits[6:8]}'
    return events

def merge_ranges(events: list[dict[str,str]]) -> list[dict[str,str]]:
    pairs = sorted({(event['start'], event['end']) for event in events})
    merged: list[list[str]] = []
    for start, end in pairs:
        if not merged or start > merged[-1][1]: merged.append([start,end])
        elif end > merged[-1][1]: merged[-1][1] = end
    return [{'start':start,'end':end} for start,end in merged]

def main() -> int:
    if not AIRBNB and not BOOKING:
        print('Aucun secret iCal configuré : aucune modification.')
        return 0
    if not AIRBNB or not BOOKING:
        print('Les deux secrets AIRBNB_ICAL_URL et BOOKING_ICAL_URL sont obligatoires.', file=sys.stderr)
        return 2
    airbnb_events = fetch(AIRBNB, 'airbnb')
    booking_events = fetch(BOOKING, 'booking')
    busy = merge_ranges(airbnb_events + booking_events)
    previous = {}
    if OUTPUT.exists():
        try: previous = json.loads(OUTPUT.read_text(encoding='utf-8'))
        except Exception: previous = {}
    sources = {'airbnb':len(airbnb_events),'booking':len(booking_events)}
    if previous.get('status') == 'active' and previous.get('busy') == busy and previous.get('sources') == sources:
        print(f'Aucun changement : {len(busy)} période(s) bloquée(s).')
        return 0
    payload = {'status':'active','updated_at':datetime.now(timezone.utc).isoformat(),'busy':busy,'sources':sources}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(f'Calendrier mis à jour : {len(busy)} période(s), Airbnb={len(airbnb_events)}, Booking={len(booking_events)}.')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
