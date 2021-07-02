


def format_time(seconds):
    if seconds < 200:
        return f'{seconds:4.1f} seconds'
    elif seconds < 60*200:
        return f'{seconds/60:4.1f} minutes'
    elif seconds < 60*60*200:
        return f'{seconds/3600:4.1f} hours'
    else:
        return f'{seconds/(24 * 3600):4.1f} days'
