import redis
import sys

def test_redis_connection():
    try:
        # 创建Redis连接
        r = redis.Redis(
            host='127.0.0.1',
            port=6379,
            socket_timeout=5,
            retry_on_timeout=True
        )
        
        # 测试连接
        r.ping()
        print("Redis连接成功!")
        
        # 测试基本操作
        r.set('test_key', 'test_value')
        value = r.get('test_key')
        print(f"测试读写成功: {value}")
        
        # 清理测试数据
        r.delete('test_key')
        
    except redis.ConnectionError as e:
        print(f"Redis连接错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"其他错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_redis_connection() 