#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实验 9-4：模拟流式语音感知（Streaming Speech Perception）

书中原实验用 Qwen2-Audio 做"分块输入模拟流式处理"，把连续音频切成小块，
每块连同此前累积的音频上下文一起送入模型，逐步产出文本，并测量每块的延迟；
用来演示"过早分块导致误识别 / 缺失上下文"与"等完整音频再识别"之间的
延迟 vs 准确率权衡。

Qwen2-Audio 当前没有可直接调用的 key/endpoint，本 demo 用 OpenAI Whisper
（whisper-1）作为**可用的 ASR 替代**来演示同一现象：Whisper 同样是"整段输入
的非流式模型"（它的编码器需要一整段音频才能开始工作），因此把音频按递增长度
切块、每块单独识别，正好复现"过早决策的代价"。

流程：
  1) 用 OpenAI TTS（tts-1）合成一句中文测试音频——句子含时间信息（"两点半"），
     且前半句在被截断时会产生歧义/不完整，随着音频增长逐步收敛到正确文本。
  2) 用 ffmpeg 把音频按递增长度（每 CHUNK_STEP 秒增长一次）切出"到目前为止
     收到的全部音频"，模拟流式：t=0.5s、1.0s、1.5s ...
  3) 每个前缀块调用 Whisper 得到"当前部分识别结果"，记录识别文本与到达延迟。
  4) 对比：只在结尾对整段音频识别一次的结果与延迟。
  5) 打印逐块识别表 + 整段识别对照，量化"首个可用识别"的延迟与整段延迟的权衡。

依赖：openai（Python SDK）、本机 ffmpeg/ffprobe。
环境变量：OPENAI_API_KEY（见 env.example）。
"""

import os
import sys
import time
import shutil
import subprocess
import tempfile
from pathlib import Path

# 从同目录 .env 读取 OPENAI_API_KEY（若安装了 python-dotenv）
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

# ----------------------------- 可调参数 -----------------------------

# 测试句子：含时间信息"两点半"，前半句被截断时容易识别不全 / 产生歧义，
# 后半句补充上下文后收敛。TTS 合成语速适中，整句约 5~6 秒，可切出 10+ 个块。
TEST_SENTENCE = "麻烦你帮我把明天下午的会议改到两点半，地点还是在三号会议室，别忘了通知大家。"

CHUNK_STEP = 0.5            # 每次增长的音频长度（秒），模拟流式分块粒度
TTS_MODEL = "tts-1"        # OpenAI 语音合成模型
TTS_VOICE = "alloy"        # 语音音色
ASR_MODEL = "whisper-1"    # OpenAI ASR 模型
ASR_LANGUAGE = "zh"        # 提示 Whisper 目标语言为中文

AUDIO_DIR = Path(__file__).parent / "audio"   # 音频输出目录
FULL_AUDIO = AUDIO_DIR / "sentence.wav"        # 合成的整段音频

# ----------------------------- 工具函数 -----------------------------


def die(msg: str) -> None:
    print(f"\n[错误] {msg}", file=sys.stderr)
    sys.exit(1)


def check_prereqs():
    """检查 ffmpeg / ffprobe / API key 是否就绪。"""
    for tool in ("ffmpeg", "ffprobe"):
        if shutil.which(tool) is None:
            die(f"未找到 {tool}，请先安装 ffmpeg（brew install ffmpeg）。")
    if not os.getenv("OPENAI_API_KEY"):
        die("未设置 OPENAI_API_KEY。请复制 env.example 为 .env 并填入，或直接 export。")


def get_client():
    from openai import OpenAI
    return OpenAI()  # 自动读取 OPENAI_API_KEY


def synth_audio(client) -> None:
    """用 OpenAI TTS 合成整段测试音频，保存为 wav（便于 ffmpeg 精确切块）。"""
    AUDIO_DIR.mkdir(exist_ok=True)
    print(f"[1/4] 合成测试音频（TTS={TTS_MODEL}, voice={TTS_VOICE}）...")
    print(f"      句子：{TEST_SENTENCE}")
    with client.audio.speech.with_streaming_response.create(
        model=TTS_MODEL,
        voice=TTS_VOICE,
        input=TEST_SENTENCE,
        response_format="wav",
    ) as resp:
        resp.stream_to_file(str(FULL_AUDIO))
    print(f"      已保存：{FULL_AUDIO}")


def audio_duration(path: Path) -> float:
    """用 ffprobe 读取音频时长（秒）。"""
    out = subprocess.check_output(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(path),
        ],
        text=True,
    )
    return float(out.strip())


def cut_prefix(src: Path, end_sec: float, dst: Path) -> None:
    """用 ffmpeg 切出 [0, end_sec] 的前缀音频，模拟"到目前为止收到的全部音频"。"""
    subprocess.run(
        [
            "ffmpeg", "-y", "-loglevel", "error",
            "-i", str(src),
            "-t", f"{end_sec:.3f}",
            "-c", "copy" if src.suffix == dst.suffix else "pcm_s16le",
            str(dst),
        ],
        check=True,
    )


def transcribe(client, path: Path) -> str:
    """调用 Whisper 识别一段音频，返回文本。"""
    with open(path, "rb") as f:
        resp = client.audio.transcriptions.create(
            model=ASR_MODEL,
            file=f,
            language=ASR_LANGUAGE,
        )
    return resp.text.strip()


# ----------------------------- 主流程 -----------------------------


def main():
    check_prereqs()
    client = get_client()

    # 1) 合成音频
    synth_audio(client)
    total = audio_duration(FULL_AUDIO)
    print(f"      整段时长：{total:.2f} 秒\n")

    # 2)+3) 流式模拟：按递增前缀长度切块并逐块识别
    print(f"[2/4] 流式模拟：每 {CHUNK_STEP}s 增长一次，逐块调用 Whisper 识别当前累积音频")
    print("      （Whisper 编码器非增量，每块都对累积音频从头识别——这正是「模拟流式」的代价）\n")

    # 生成分块的结束时间点：0.5, 1.0, ... 直到覆盖整段
    endpoints = []
    t = CHUNK_STEP
    while t < total:
        endpoints.append(round(t, 3))
        t += CHUNK_STEP
    endpoints.append(round(total, 3))  # 最后一块 = 完整音频

    tmpdir = Path(tempfile.mkdtemp(prefix="stream_chunks_"))
    rows = []
    first_usable_latency = None  # 首个"非空"识别结果的累计延迟
    stream_start = time.perf_counter()
    try:
        for i, end in enumerate(endpoints, 1):
            chunk_path = tmpdir / f"chunk_{i:02d}.wav"
            cut_prefix(FULL_AUDIO, end, chunk_path)
            t0 = time.perf_counter()
            text = transcribe(client, chunk_path)
            latency = time.perf_counter() - t0          # 单块识别延迟
            arrival = time.perf_counter() - stream_start  # 从流式开始的累计到达延迟
            if first_usable_latency is None and text:
                first_usable_latency = arrival
            rows.append((end, latency, arrival, text))
            print(f"  块#{i:02d}  音频前缀 {end:>4.1f}s  单块延迟 {latency:5.2f}s  "
                  f"累计 {arrival:6.2f}s | 识别：{text or '(空)'}")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    # 4) 对照：只在结尾对整段音频识别一次
    print(f"\n[3/4] 对照方案：等完整音频到齐后，只识别整段一次")
    t0 = time.perf_counter()
    full_text = transcribe(client, FULL_AUDIO)
    full_latency = time.perf_counter() - t0
    print(f"      整段识别延迟 {full_latency:.2f}s | 识别：{full_text}")

    # 5) 汇总：延迟 vs 准确率权衡
    print(f"\n[4/4] 对照小结（延迟 vs 准确率权衡）")
    print(f"  原始句子           ：{TEST_SENTENCE}")
    print(f"  整段识别结果       ：{full_text}")
    print(f"  整段识别需等待音频 ：{total:.2f}s（录完）+ {full_latency:.2f}s（推理）")
    if first_usable_latency is not None:
        print(f"  流式首个可用识别   ：仅需约 {endpoints[0]:.1f}s 音频即产出部分结果，"
              f"比整段提前 {total - endpoints[0]:.1f}s 拿到第一版")
    # 展示早期分块与最终结果的差异
    early = rows[0][3] if rows else ""
    print(f"\n  过早分块的代价：")
    print(f"    最早分块（{endpoints[0]:.1f}s）识别 →  {early or '(空/不完整)'}")
    print(f"    随音频增长收敛 →              {rows[-1][3]}")
    print(f"    对比整段一次识别 →            {full_text}")
    print(f"\n  结论：流式分块能极早给出'部分结果'（低首包延迟），但早期块因缺少后半句"
          f"上下文，识别可能不完整/出错（如时间、数字被截断误判）；随着音频累积逐步"
          f"收敛。整段识别最准，但必须等到整句说完+推理，首字延迟最高。这正是流式"
          f"语音感知的延迟/准确率权衡。")


if __name__ == "__main__":
    main()
