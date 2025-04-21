# OBS Weather Tools Development Environment Setup

## Required Software

- Windows 10 version 2004+ or Windows 11
- Visual Studio Code
- Python 3.10+
- WSL2 with Ubuntu
- Redis (via WSL2)

## WSL2 Installation and Setup

1. Install WSL2 (PowerShell as Administrator):

```powershell
wsl --install
```

2.Verify and set WSL2 as default:

```powershell
wsl --version
wsl --set-default-version 2
```

3.Install Ubuntu from Microsoft Store and create user account when prompted

4.Update Ubuntu (in WSL2 terminal):

```bash
sudo apt update && sudo apt upgrade -y
```

## Redis Setup in WSL2

1. Install Redis:
```bash
# Update package list first
sudo apt update
# Install Redis server
sudo apt install redis-server
```

2. Edit Redis configuration:
```bash
sudo nano /etc/redis/redis.conf
```

3. Update these configuration settings:
```conf
# Bind to localhost only for security
bind 127.0.0.1
# Standard Redis port
port 6379
# Set memory limit for WSL2 environment
maxmemory 512mb
# Memory management policy
maxmemory-policy allkeys-lru
# Enable AOF persistence for data durability
appendonly yes
appendfsync everysec
# Basic security settings
protected-mode yes
```

4. Start and enable Redis service:
```bash
# Start Redis server
sudo service redis-server start
# Enable Redis to start on boot
sudo systemctl enable redis-server
# Verify service status
sudo systemctl status redis-server
```

5. Test Redis connection:
```bash
# Simple connection test
redis-cli ping
# Should return "PONG"

# Extended test with data operations
redis-cli << EOF
SET test "Hello"
GET test
DEL test
EOF
```

### Redis Configuration Validation

To verify your Redis setup is correct, run these checks:

1. Check Redis service status:
```bash
sudo systemctl status redis-server
```

2. Verify memory settings:
```bash
redis-cli INFO memory | grep used_memory_human
```

3. Check persistence configuration:
```bash
redis-cli CONFIG GET appendonly
redis-cli CONFIG GET appendfsync
```

### Troubleshooting Redis

Common issues and solutions:

1. Redis won't start:
```bash
# Check logs for errors
sudo tail -f /var/log/redis/redis-server.log
# Verify permissions
sudo chown -R redis:redis /var/lib/redis
```

2. Connection refused:
```bash
# Check if Redis is listening
sudo netstat -tlpn | grep redis
# Verify bind address in config
sudo grep "bind" /etc/redis/redis.conf
```

3. Memory issues:
```bash
# Monitor memory usage
redis-cli INFO memory
# Clear all data if needed
redis-cli FLUSHALL
```

### Redis Health Monitoring

Set up basic monitoring:

1. Check real-time metrics:
```bash
# Monitor command latency
redis-cli --latency

# Watch live commands
redis-cli MONITOR
```

2. Configure log rotation:
```bash
sudo nano /etc/logrotate.d/redis-server
```

Add this configuration:
```conf
/var/log/redis/redis-server.log {
    weekly
    rotate 7
    compress
    delaycompress
    notifempty
    missingok
    create 640 redis redis
}

## Python Environment

1. Create virtual environment:

```bash
python -m venv venv
source venv/bin/activate
```

2. Install dependencies:

```bash
pip install redis aioredis pytest pytest-asyncio
```

## VS Code Setup

1. Required Extensions:
   - Remote - WSL
   - Python
   - Redis

2. Workspace Settings:

```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.terminal.activateEnvironment": true,
    "terminal.integrated.defaultProfile.windows": "Ubuntu (WSL)"
}
```

## Verification Script

Create and run this test to verify your setup:

```python
# tests/verify_setup.py
import redis.asyncio as redis
import asyncio
import sys

async def verify_environment():
    print(f"Python Version: {sys.version}")

    try:
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        await r.set('test', 'Environment OK')
        result = await r.get('test')
        await r.delete('test')
        await r.close()

        print("Redis Connection: Success")
        print(f"Test Result: {result}")
        return True
    except Exception as e:
        print(f"Redis Error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(verify_environment())
    print("\nSetup Status:", "✓ Ready" if success else "✗ Failed")
```

## Troubleshooting

### Redis Issues

- Check service: `sudo service redis-server status`
- Restart Redis: `sudo service redis-server restart`
- View logs: `sudo tail -f /var/log/redis/redis-server.log`

### WSL2 Issues

- Restart WSL: `wsl --shutdown` then reopen terminal
- Check version: `wsl -l -v`
- Update WSL: `wsl --update`

## Daily Development Workflow

1. Start VS Code
2. Open integrated terminal (Ctrl + `)
3. Verify Redis is running:

```bash
redis-cli ping
```

4. Activate virtual environment:

```bash
source venv/bin/activate
```

You're now ready to develop!
