# Test creating instance via API
import requests
import json

def test_create_instance():
    url = "http://localhost:8000/api/instances/create"
    
    payload = {
        "account_id": "DEMO_BN001",
        "platform": "binance", 
        "strategy": "martingale_hedge",
        "symbol": "ETHUSDT",
        "parameters": {
            "symbol": "ETHUSDT"
        }
    }
    
    try:
        print("发送创建实例请求...")
        print(f"URL: {url}")
        print(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
        
        response = requests.post(url, json=payload, timeout=10)
        
        print(f"\n响应状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 创建成功!")
            print(f"响应内容: {json.dumps(result, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ 创建失败!")
            print(f"错误内容: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求异常: {e}")
    except json.JSONDecodeError as e:
        print(f"❌ JSON解析失败: {e}")
        print(f"原始响应: {response.text}")
    except Exception as e:
        print(f"❌ 其他错误: {e}")

if __name__ == "__main__":
    test_create_instance()