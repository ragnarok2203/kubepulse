"""
KubePulse SRE Server Launcher
Runs the KubePulse SRE Command Center on localhost:5050.
"""

import sys
from app import create_app
from config import Config

def main():
    app = create_app()
    banner = f"""
======================================================================
  _  ___     _          _____      _            ____  ____  _____ 
 | |/ / |   | |        |  __ \    | |          / ___||  _ \| ____|
 | ' /| |   | |__   ___| |__) |  _| |___  ___ | \___ | |_) | |__  
 |  < | |   | '_ \ / _ \  ___/ || | / __|/ _ \ \___ \|  _ <|  __| 
 | . \| |___| |_) |  __/ |   | || | \__ \  __/  ___) | | \ \ |___ 
 |_|\_\_____|_.__/ \___|_|    \_,_|_|___/\___| |____/|_|  \_\_____|

 Autonomous Kubernetes Observability, Error Budget & Self-Healing Engine
 Target SLO: {Config.SLO_AVAILABILITY_TARGET}% Availability (Rolling 30-Day Window)
======================================================================
 [*] Host:    http://127.0.0.1:{Config.PORT}
 [*] Mode:    {Config.CLUSTER_MODE.upper()}
 [*] Health:  http://127.0.0.1:{Config.PORT}/healthz
 [*] Press CTRL+C to stop
======================================================================
"""
    print(banner)
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)

if __name__ == "__main__":
    main()
