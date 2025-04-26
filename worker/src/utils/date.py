from datetime import datetime, timedelta

def convert_to_unix_timestamp(posted_date) -> int:
    if 'day' in posted_date:
        days = int(posted_date.split()[0])
        delta = timedelta(days=days)
    elif 'week' in posted_date:
        weeks = int(posted_date.split()[0])
        delta = timedelta(weeks=weeks)
    elif 'month' in posted_date:
        months = int(posted_date.split()[0])
        delta = timedelta(weeks=months*4)  # Approximation: 1 month = 4 weeks
    elif 'year' in posted_date:
        years = int(posted_date.split()[0])
        delta = timedelta(weeks=years*52)
    elif 'hour' in posted_date:
        hours = int(posted_date.split()[0])
        delta = timedelta(hours=hours)
    else:
        return None  # Return None for unknown formats

    timestamp = (datetime.now() - delta).timestamp()
    return int(timestamp)
