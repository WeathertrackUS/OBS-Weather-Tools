import redis.asyncio as redis
import asyncio
import sys
import unittest

async def verify_environment():
    print(f"Python Version: {sys.version}")
    
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    await r.set('test', 'Environment OK')
    result = await r.get('test')
    await r.delete('test')
    await r.close()

    print("Redis Connection: Success")
    print(f"Test Result: {result}")
    return result

class TestEnvironmentSetup(unittest.TestCase):
    def test_redis_connection(self):
        result = asyncio.run(verify_environment())
        self.assertEqual(result, 'Environment OK', "Redis setup verification failed.")

if __name__ == "__main__":
    unittest.main()
