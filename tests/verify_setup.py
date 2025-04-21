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