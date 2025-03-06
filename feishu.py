import requests
import json
import schedule
import time
from datetime import datetime

# 配置URL
WEBHOOK_URL = "https://open.feishu.cn/open-apis/bot/v2/hook/6e5c020f-5963-4e0b-8a0b-88a54f9da27b"
DATA_URL = "https://gitee.com/Probius/Hello-CTFtime/raw/main/CN.json"

def fetch_ctf_data():
    """从Gitee获取CTF比赛数据"""
    try:
        response = requests.get(DATA_URL)
        return response.json()
    except Exception as e:
        print(f"获取数据失败: {str(e)}")
        return None

def format_message(data):
    """将CTF数据格式化为飞书消息格式"""
    if not data or "data" not in data or "result" not in data["data"]:
        return {
            "msg_type": "text",
            "content": {
                "text": "暂无有效赛事数据"
            }
        }

    events = data["data"]["result"]
    # 不再过滤已结束赛事，显示所有赛事
    message_content = []
    for event in events:
        # 构造QQ群链接
        qq_group = list(event["contac"].values())[0] if event["contac"] else ""
        qq_link = f"tencent://groupwpa/?subcmd=allparam&uin={qq_group}" if qq_group else ""

        # 构建消息段落
        event_block = [
            [
                {"tag": "text", "text": "🔰 赛事名称：", "style": {"bold": True}},
                {"tag": "a", "text": event["name"], "href": event["link"]}
            ],
            [
                {"tag": "text", "text": "📅 报名时间：", "style": {"bold": True}},
                {"tag": "text", "text": f"{event['reg_time_start']} - {event['reg_time_end']}"}
            ],
            [
                {"tag": "text", "text": "⏰ 比赛时间：", "style": {"bold": True}},
                {"tag": "text", "text": f"{event['comp_time_start']} - {event['comp_time_end']}"}
            ],
            [
                {"tag": "text", "text": "🏢 主办方：", "style": {"bold": True}},
                {"tag": "text", "text": event["organizer"]}
            ],
            [
                {"tag": "text", "text": "📱 联系方式：", "style": {"bold": True}},
                {"tag": "a", "text": f"QQ群 {qq_group}", "href": qq_link} if qq_link else
                {"tag": "text", "text": "暂无"}
            ],
            [{"tag": "hr"}]
        ]
        message_content.extend(event_block)

    # 添加统计信息
    # 修改统计信息显示总赛事数量
    message_content.append([
        {"tag": "text", "text": f"📊 共 {len(events)} 个赛事"}
    ])

    return {
        "msg_type": "post",
        "content": {
            "post": {
                "zh_cn": {
                    "title": "🏁 CTF赛事速递",
                    "content": message_content
                }
            }
        }
    }

def send_to_feishu():
    """发送消息到飞书机器人"""
    ctf_data = fetch_ctf_data()
    if not ctf_data:
        return

    # 构造消息
    message = format_message(ctf_data)

    # 发送请求
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(WEBHOOK_URL,
                               headers=headers,
                               data=json.dumps(message))
        response.raise_for_status()
        print(f"消息发送成功: {response.status_code}")
    except requests.exceptions.RequestException as e:
        error_msg = {
            "msg_type": "text",
            "content": {
                "text": f"🚨 网络请求异常：{str(e)}"
            }
        }
        requests.post(WEBHOOK_URL, json=error_msg)
    except Exception as e:
        error_msg = {
            "msg_type": "text",
            "content": {
                "text": f"⚠️ 未知错误：{str(e)}"
            }
        }
        requests.post(WEBHOOK_URL, json=error_msg)

# 定时任务配置（每天9点和21点执行）
schedule.every().day.at("09:00").do(send_to_feishu)
schedule.every().day.at("21:00").do(send_to_feishu)

# 立即执行一次测试
print("开始执行CTF赛事推送...")
send_to_feishu()

# 启动定时任务
while True:
    schedule.run_pending()
    time.sleep(60)