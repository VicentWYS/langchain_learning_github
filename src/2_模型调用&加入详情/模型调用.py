import os
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()

# ============================================================
# 目录配置
# ============================================================
BASE_DIR = Path(__file__).parent
PROMPTS_DIR = BASE_DIR / "prompts"
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# 模型配置
# ============================================================
@dataclass
class ModelConfig:
    """模型调用配置，所有参数均有默认值，可按需覆盖。"""

    model: str = "deepseek-v4-flash"
    temperature: float = 0.8
    enable_search: bool = False  # 联网搜索
    enable_thinking: bool = False  # 深度思考


# ============================================================
# 提示词加载
# ============================================================
def load_prompt(filename: str) -> str:
    """从 prompts 目录读取提示词文件内容。"""
    filepath = PROMPTS_DIR / filename
    if not filepath.exists():
        raise FileNotFoundError(f"提示词文件不存在: {filepath}")
    return filepath.read_text(encoding="utf-8").strip()


# ============================================================
# 日志记录
# ============================================================
def _extract_token_usage(response) -> dict:
    """从 AIMessage 中提取 token 用量信息。"""
    usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}

    # langchain 标准的 usage_metadata
    if hasattr(response, "usage_metadata") and response.usage_metadata:
        um = response.usage_metadata
        usage["input_tokens"] = um.get("input_tokens", 0)
        usage["output_tokens"] = um.get("output_tokens", 0)
        usage["total_tokens"] = um.get("total_tokens", 0)
        return usage

    # OpenAI 兼容 API 的 token_usage
    rm = getattr(response, "response_metadata", {}) or {}
    tu = rm.get("token_usage", {})
    if tu:
        usage["input_tokens"] = tu.get("prompt_tokens", 0)
        usage["output_tokens"] = tu.get("completion_tokens", 0)
        usage["total_tokens"] = tu.get("total_tokens", 0)

    return usage


def write_call_log(
    model_name: str,
    system_prompt: str,
    user_prompt: str,
    output: str,
    start_time: datetime,
    end_time: datetime,
    duration_sec: float,
    token_usage: dict,
) -> Path:
    """将本次调用详情写入日志文件，返回日志文件路径。"""
    timestamp = start_time.strftime("%Y%m%d_%H%M%S")
    log_path = LOGS_DIR / f"call_{timestamp}.log"

    sys_len = len(system_prompt)
    usr_len = len(user_prompt)
    out_len = len(output)
    total_len = sys_len + usr_len + out_len

    yaml_header = (
        f"model: {model_name}\n"
        f"start_time: \"{start_time.strftime('%Y-%m-%d %H:%M:%S')}\"\n"
        f"end_time: \"{end_time.strftime('%Y-%m-%d %H:%M:%S')}\"\n"
        f"duration_sec: {duration_sec:.2f}\n"
        f"char_count:\n"
        f"  system: {sys_len}\n"
        f"  user: {usr_len}\n"
        f"  output: {out_len}\n"
        f"  total: {total_len}\n"
        f"token_usage:\n"
        f"  input: {token_usage['input_tokens']}\n"
        f"  output: {token_usage['output_tokens']}\n"
        f"  total: {token_usage['total_tokens']}"
    )

    lines = [
        yaml_header,
        "---",
        "[SystemPrompt]",
        system_prompt,
        "",
        "[UserPrompt]",
        user_prompt,
        "",
        "[Output]",
        output,
    ]

    log_path.write_text("\n".join(lines), encoding="utf-8")
    return log_path


# ============================================================
# 模型调用
# ============================================================
def call_model(config: ModelConfig, system_prompt: str, user_prompt: str) -> dict:
    """
    使用给定配置调用模型，返回包含调用详情的字典。
    """
    API_KEY = os.getenv("DEEPSEEK_API_KEY")
    BASE_URL = os.getenv("DEEPSEEK_BASE_URL")

    if not API_KEY or API_KEY == "your_api_key_here":
        raise ValueError("请在 .env 文件中设置有效的 DEEPSEEK_API_KEY")
    if not BASE_URL or BASE_URL == "your_base_url_here":
        raise ValueError("请在 .env 文件中设置有效的 DEEPSEEK_BASE_URL")

    model_kwargs = {}
    if config.enable_search:
        model_kwargs["enable_search"] = True
    if config.enable_thinking:
        model_kwargs["enable_thinking"] = True

    model = init_chat_model(
        model=config.model,
        model_provider="openai",
        api_key=API_KEY,
        base_url=BASE_URL,
        temperature=config.temperature,
        **(model_kwargs),
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]

    start_time = datetime.now()
    start_perf = time.perf_counter()

    response = model.invoke(messages)

    end_perf = time.perf_counter()
    end_time = datetime.now()
    duration_sec = end_perf - start_perf

    output = response.content
    token_usage = _extract_token_usage(response)

    log_path = write_call_log(
        model_name=config.model,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        output=output,
        start_time=start_time,
        end_time=end_time,
        duration_sec=duration_sec,
        token_usage=token_usage,
    )

    return {
        "model": config.model,
        "output": output,
        "start_time": start_time,
        "end_time": end_time,
        "duration_sec": duration_sec,
        "token_usage": token_usage,
        "log_path": log_path,
    }


# ============================================================
# 示例调用
# ============================================================
def chat_example():
    config = ModelConfig()  # 使用默认配置，可按需修改

    system_prompt = load_prompt("system_prompt.txt")
    user_prompt = load_prompt("user_prompt.txt")

    result = call_model(config, system_prompt, user_prompt)

    print(f"模型     : {result['model']}")
    print(f"耗时     : {result['duration_sec']:.2f} 秒")
    print(f"Token    : 输入={result['token_usage']['input_tokens']}, ")
    print(f"输出={result['token_usage']['output_tokens']}, ")
    print(f"总计={result['token_usage']['total_tokens']}")
    print(f"输出     : {result['output']}")
    print(f"日志文件 : {result['log_path']}")


def main():
    try:
        chat_example()
    except KeyboardInterrupt:
        print("\n\n程序中断")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
