def export_ics_from_queue(queue_items):
    lines=['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//MarketingOps//SocialQueue//IT']
    for it in queue_items:
        dt=(it.get('datetime') or '').replace('-','').replace(':','').replace(' ','T')
        uid=f"queue-{it.get('id')}@local"
        summary=f"{it.get('channel')} — { (it.get('text') or '')[:40] }"
        lines+=['BEGIN:VEVENT',f'UID:{uid}',f'DTSTART:{dt}Z',f'SUMMARY:{summary}','END:VEVENT']
    lines.append('END:VCALENDAR')
    return '\r\n'.join(lines)
