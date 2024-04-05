# ME102B Frisbee Launcher

## Overview

## Deployment
Start by running the server on the remote machine (laptop) using
``` bash
python3 server.py
```
Then, on the onboard machine, run the client using
``` bash
python3 client.py
```

Yaw motor:
* p < 20 => full reverse
* 20 < p <= 58 => prop. reverse
* 58 < p < 63 => neutral
* 63 <= p < 100 => prop. forward    
