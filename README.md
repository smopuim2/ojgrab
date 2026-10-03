# ojgrab
把OJ里的题目扒下来，然后喂给LLM！

## 启动

```
pip install quart uvicorn openai playwright markdown-it-py mdit-py-plugins
notepad config.py
mkdir data
uvicorn main:app --port 5000
```

## 访问

`127.0.0.1:5000`

## 注意

本项目最初为校内平台（[Lyrio](/lyrio-dev/lyrio)魔改）制作，未在其它 OJ 验证。
不同的 OJ 有不同的架构。如果发现题目抓取功能无法使用，可以检查 `grab.py` 。
