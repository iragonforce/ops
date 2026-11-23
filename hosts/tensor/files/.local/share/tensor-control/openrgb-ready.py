#!/usr/bin/env python3
import time
from openrgb import OpenRGBClient
for _ in range(30):
    try:
        c=OpenRGBClient('127.0.0.1',6742,name='Tensor readiness')
        ok=any('5070' in d.name and len(d.colors)>0 for d in c.devices)
        if ok:
            board=next((d for d in c.devices if d.name=='ASUS ROG STRIX X870-A GAMING WIFI'),None)
            if board is not None:
                header=next((z for z in board.zones if z.name=='Addressable RGB Header 1'),None)
                if header is not None and len(header.leds)==0:
                    header.resize(10)
        c.disconnect()
        if ok:raise SystemExit(0)
    except SystemExit:raise
    except Exception:pass
    time.sleep(1)
raise SystemExit('RTX 5070 LED discovery incomplete; retry server startup')
