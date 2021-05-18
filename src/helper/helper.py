import os

def get_cogs():
    cogs = []
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py') and not filename.startswith('custom_help'):
            cogs.append(filename[0:-3])
    return cogs

# Parses timestamp input by user from music play command
def parse_time(timestamp):
    time_formats = ['%M:%S', '%H:%M:%S']