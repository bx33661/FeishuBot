import requests
import json
import schedule
import time

SCHEDULE_TIME = "23:01"
WEBHOOK_URL = "https://open.feishu.cn/open-apis/bot/v2/hook/...."
DATA_URL = "https://gitee.com/Probius/Hello-CTFtime/raw/main/CN.json"

def fetch_ctf_data():
    #获取数据
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
    message_content = []

    for event in events:
        # 构造QQ群链接
        qq_group = list(event["contac"].values())[0] if event["contac"] else ""
        qq_link = f"tencent://groupwpa/?subcmd=allparam&uin={qq_group}" if qq_group else ""

        # 构建消息段落（修正样式结构）
        event_blocks = [
            [
                {"tag": "text", "text": "🔰 赛事名称：", "bold": True},
                {"tag": "a", "text": event["name"], "href": event["link"]}
            ],
            [
                {"tag": "text", "text": "📅 报名时间：", "bold": True},
                {"tag": "text", "text": f"{event['reg_time_start']} - {event['reg_time_end']}"}
            ],
            [
                {"tag": "text", "text": "⏰ 比赛时间：", "bold": True},
                {"tag": "text", "text": f"{event['comp_time_start']} - {event['comp_time_end']}"}
            ],
            [
                {"tag": "text", "text": "🏢 主办方：", "bold": True},
                {"tag": "text", "text": event["organizer"]}
            ],
            [
                {"tag": "text", "text": "📱 联系方式：", "bold": True},
                {"tag": "a", "text": f"QQ群 {qq_group}", "href": qq_link} if qq_link else
                {"tag": "text", "text": "暂无"}
            ]
        ]
        message_content.extend(event_blocks)

    # 添加统计信息（添加粗体样式）
    message_content.append([
        {"tag": "text", "text": f"📊 共 {len(events)} 个赛事", "bold": True}
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


def send_to_feishu(data_json):
    ctf_data = data_json
    if not ctf_data:
        return

    # 发送请求
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(WEBHOOK_URL,
                               headers=headers,
                               data=json.dumps(ctf_data, ensure_ascii=False).encode("utf-8"))
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

#定时任务
def job():
    print(f"开始执行任务: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}")
    data = format_message(fetch_ctf_data())
    send_to_feishu(data)

if __name__ == "__main__":
    schedule.every().day.at(SCHEDULE_TIME).do(job)

    job()

    while True:
        schedule.run_pending()
        time.sleep(60)