from poc.chains import ChainsManager
from poc.openai_chat import openai_chat

if __name__ == "__main__":
    chains_manager = ChainsManager()
    user_msg = "我要一個芭樂，15 個蘋果"
    response = chains_manager.main(user_msg)

    print(f"Finsihed! response: {response}")

    print("Done!")
