import requests
import uuid

API_URL = "http://127.0.0.1:8001/chat"

def main():
    """一个简单的命令行客户端，用于与FastAPI服务器交互。"""
    session_id = str(uuid.uuid4())
    print("\n\n智能药房导购 Multi-Agent (Client模式) 已启动。")
    print(f"新会话已创建，ID: {session_id}")
    print("你好，我是一位香港地区的药房辅助小助手细W，请告诉我你的症状与所处的地区（港岛/九龙/新界）？(输入 'exit' 退出)")

    while True:
        try:
            query = input("> ")
            if query.lower() == 'exit':
                print("多谢使用，再见！")
                break
            if not query.strip():
                continue

            payload = {
                "query": query,
                "session_id": session_id
            }

            response = requests.post(API_URL, json=payload, timeout=180)
            response.raise_for_status()  # 如果HTTP状态码是4xx或5xx，则抛出异常

            data = response.json()
            
            print(f"\n小助手: {data['reply']}")

            if data['session_complete']:
                print("\n--- [会话结束] 本次查询已完成。开始新的会话。---\n")
                print("你好，我是一位香港地区的药房辅助小助手细W，请告诉我你的症状与所处的地区（港岛/九龙/新界）？(输入 'exit' 退出)")
                session_id = str(uuid.uuid4()) # 开始一个新会话
                print(f"新会话已创建，ID: {session_id}")


        except requests.exceptions.RequestException as e:
            print(f"\n[错误] 无法连接到服务器: {e}")
            print("请确保服务器正在运行。")
            break
        except Exception as e:
            print(f"\n[发生未知错误]: {e}")

if __name__ == "__main__":
    main()