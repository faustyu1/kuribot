import time
import os
import psutil
import asyncio

async def get_cmd_output(cmd):
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await process.communicate()
        return stdout.decode().strip()
    except:
        return ""

def get_uptime():
    try:
        p = psutil.Process(os.getpid())
        uptime_seconds = time.time() - p.create_time()
        m, s = divmod(uptime_seconds, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        
        if d > 0:
            return f"{int(d)}d {int(h)}h {int(m)}m"
        if h > 0:
            return f"{int(h)}h {int(m)}m {int(s)}s"
        return f"{int(m)}m {int(s)}s"
    except:
        return "Unknown"
