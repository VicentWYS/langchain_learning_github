import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

load_dotenv()

API_KEY = os.getenv("DEEPSEEK_API_KEY")
BASE_URL = os.getenv("DEEPSEEK_BASE_URL")

if not API_KEY or API_KEY == "your_api_key_here":
    raise ValueError("\n请先在 .env 文件中设置有效的 API_KEY\n")

if not BASE_URL or BASE_URL == "your_base_url_here":
    raise ValueError("\n请先在 .env 文件中设置有效的 BASE_URL\n")

model = init_chat_model(
    model="deepseek-v4-flash",
    model_provider="openai",
    api_key=API_KEY,
    base_url=BASE_URL,
    temperature=0.8,
)


def chat_example():
    conversation = [
        {
            "role": "system",
            "content": "你是一名表达简洁的智能助手，每次回答的字数都限制在50字以内。",
        },
        {
            "role": "user",
            "content": "请简单介绍成语：南辕北辙",
        },
    ]

    response = model.invoke(conversation)
    print(f"AI 回复：{response.content}")


def main():
    try:
        chat_example()
    except KeyboardInterrupt:
        print("\n\n程序中断")
    except Exception as e:
        print(f"\n\n错误:{e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
