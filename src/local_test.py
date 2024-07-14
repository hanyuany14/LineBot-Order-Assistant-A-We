# from src.llm_agents.monitor_agent import MonitorAgent

# if __name__ == "__main__":

#     user_msg = "我要一個芭樂，15 個蘋果"

#     situation = MonitorAgent().judge(user_msg)
#     print(f"店經理 Manager 判斷這是一個: '{situation}' 情境")

#     if situation == "order":
#         reply = LineBot().checking_stock_response(
#             msg_type=event_dict.message.type, msg_text=event_dict.message.text
#         )

#     elif situation == "chat":
#         reply = LineBot().chat_with_user_response(event)
#         print(f"reply: {reply}")
#         line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
