# PyrogramX 重构路线图

> 目标：完全重构 Pyrogram 底层，保持用户 API 100% 兼容，性能全面提升。
> 参考：`pyrogram-master/pyrogram/`
> 已完成：`raw/` 层（高性能 TL 编译器 + 运行时）

---

## 目录结构

```
pyrogramX/
├── __init__.py              # 包入口，导出 Client, idle, compose, 信号异常
├── client.py                # Client 类（继承 Methods）
├── dispatcher.py            # Update 分发器
├── filters.py               # 过滤器系统
├── utils.py                 # 工具函数（peer 转换、密码计算等）
├── file_id.py               # Bot API file_id 编解码
├── mime_types.py             # MIME 类型映射
├── emoji.py                 # Emoji 常量
│
├── raw/                     # ✅ 已完成 — 高性能 TL 层
│   ├── core/                #   手写核心类型 + 优化原语
│   ├── types/               #   编译器生成
│   ├── functions/           #   编译器生成
│   ├── base/                #   编译器生成
│   └── all.py               #   惰性加载注册表
│
├── errors/                  # RPC 错误处理
│   ├── __init__.py          #   导出 + 手写异常基类
│   ├── rpc_error.py         #   RPCError 基类 + 错误分发
│   └── exceptions/          #   编译器从 TSV 生成
│       ├── __init__.py
│       ├── all.py           #   错误码 → 异常类映射
│       ├── bad_request.py
│       ├── flood.py
│       ├── ...
│       └── not_acceptable.py
│
├── enums/                   # 枚举类型（全部手写）
│   ├── __init__.py          #   汇总导出
│   ├── auto_name.py         #   AutoName 基类
│   ├── chat_type.py         #   手写
│   └── ...                  #   手写
│
├── types/                   # 高级类型封装
│   ├── __init__.py          #   汇总导出
│   ├── object.py            #   Object 基类
│   ├── update.py            #   Update mixin
│   ├── list.py              #   List 子类
│   ├── authorization/       #   SentCode, TermsOfService
│   ├── bots_and_keyboards/  #   CallbackQuery, InlineKeyboard 等
│   ├── inline_mode/         #   InlineQuery, InlineQueryResult 等
│   ├── input_media/         #   InputMediaPhoto, InputMediaVideo 等
│   ├── input_message_content/
│   ├── messages_and_media/  #   Message, Photo, Video, Sticker 等
│   └── user_and_chats/      #   User, Chat, Dialog, ChatMember 等
│
├── methods/                 # 客户端方法（mixin 模式）
│   ├── __init__.py          #   Methods 聚合类
│   ├── advanced/            #   invoke, resolve_peer, save_file
│   ├── auth/                #   登录、登出、2FA
│   ├── bots/                #   Bot API 操作
│   ├── chats/               #   群组/频道管理
│   ├── contacts/            #   联系人
│   ├── decorators/          #   @on_message 等装饰器
│   ├── invite_links/        #   邀请链接管理
│   ├── messages/            #   发送、编辑、删除、下载
│   ├── password/            #   云密码
│   ├── users/               #   用户信息
│   └── utilities/           #   start, stop, run, idle
│
├── handlers/                # 事件处理器
│   ├── __init__.py
│   ├── handler.py           #   Handler 基类
│   ├── message_handler.py
│   ├── callback_query_handler.py
│   └── ...                  #   12 种处理器
│
├── session/                 # MTProto 会话
│   ├── __init__.py
│   ├── session.py           #   会话管理、加密通信
│   ├── auth.py              #   DH 密钥交换
│   └── internals/           #   DataCenter, MsgId, MsgFactory
│
├── connection/              # 传输层
│   ├── __init__.py
│   ├── connection.py        #   连接管理
│   └── transport/
│       └── tcp/             #   TCPAbridged, TCPFull 等
│
├── crypto/                  # 加密
│   ├── __init__.py
│   ├── aes.py               #   AES-IGE/CTR
│   ├── mtproto.py           #   MTProto 2.0 加解密
│   ├── prime.py             #   PQ 分解
│   └── rsa.py               #   RSA 公钥
│
├── storage/                 # 会话存储
│   ├── __init__.py
│   ├── storage.py           #   抽象基类
│   ├── sqlite_storage.py    #   SQLite 实现
│   ├── file_storage.py      #   文件存储
│   └── memory_storage.py    #   内存存储
│
└── parser/                  # 消息格式化
    ├── __init__.py
    ├── parser.py            #   HTML/Markdown 分发
    ├── html.py              #   HTML 解析器
    ├── markdown.py          #   Markdown 解析器
    └── utils.py             #   SMP 字符偏移修正
```

```
compiler/
├── __main__.py              # 统一入口：python -m compiler
├── api/                     # ✅ 已完成 — TL schema → raw/
│   ├── __init__.py
│   └── compiler.py
├── errors/                  # TSV → errors/exceptions/
│   ├── __init__.py
│   ├── compiler.py
│   ├── source/
│   │   ├── 400_BAD_REQUEST.tsv
│   │   ├── 401_UNAUTHORIZED.tsv
│   │   ├── 403_FORBIDDEN.tsv
│   │   ├── 406_NOT_ACCEPTABLE.tsv
│   │   ├── 420_FLOOD.tsv
│   │   └── 500_INTERNAL_SERVER_ERROR.tsv
│   └── template/
│       ├── class.txt
│       └── sub_class.txt
└── scheme/
    ├── api.tl               # Layer 224
    └── mtproto.tl
```

---

## 实施阶段

### Phase 0：编译器整合

> 把散落的编译器统一到 `compiler/`，一键生成所有代码。

| 步骤 | 内容 | 文件 |
|------|------|------|
| 0.1 | 移植 error 编译器 | 从 `pyrogram-master/compiler/errors/` 移植，适配路径 |
| 0.2 | 统一入口 | `compiler/__main__.py` 调用 api + errors 两个编译器 |
| 0.3 | 验证 | `python -m compiler` 一键生成 `raw/` + `errors/exceptions/` |

---

### Phase 1：基础设施（零业务逻辑）

> 这些模块不依赖任何高级类型，是所有其他模块的基础。

| 步骤 | 内容 | 从 Pyrogram 移植 | 改动点 |
|------|------|-----------------|--------|
| 1.1 | `crypto/` | 直接移植 4 个文件 | `pyrogram` → `pyrogramX` |
| 1.2 | `connection/` | 直接移植 | 同上 |
| 1.3 | `session/` | 直接移植 | 同上；`asyncio.get_event_loop()` → `asyncio.get_running_loop()` |
| 1.4 | `storage/` | 直接移植 | 同上；移除 `inspect.stack()` hack，用显式参数 |
| 1.5 | `errors/` | 手写基类 + 编译器生成 exceptions | Phase 0.2 的产物 + `rpc_error.py` |
| 1.6 | `file_id.py` | 直接移植 | 命名空间替换 |
| 1.7 | `mime_types.py` | 直接复制 | 无改动 |
| 1.8 | `emoji.py` | 直接复制 | 无改动 |

完成标志：`from pyrogramX.session import Session` 可以导入。

---

### Phase 2：类型系统

> 高级类型封装，每个类型的 `_parse()` 方法把 raw 类型转换为用户友好的对象。

| 步骤 | 内容 | 文件数 | 改动点 |
|------|------|--------|--------|
| 2.1 | 基类 | `types/object.py`, `types/update.py`, `types/list.py` | 命名空间替换 |
| 2.2 | `enums/` | `enums/auto_name.py` + 手写枚举文件 | 从 Pyrogram 移植，命名空间替换 |
| 2.3 | `user_and_chats/` | ~23 个文件 | `pyrogram` → `pyrogramX`，`raw.types.` 引用不变 |
| 2.4 | `messages_and_media/` | ~23 个文件 | 同上，这是最核心的类型 |
| 2.5 | `bots_and_keyboards/` | ~25 个文件 | 同上 |
| 2.6 | `authorization/` | 2 个文件 | 同上 |
| 2.7 | `inline_mode/` | ~20 个文件 | 同上 |
| 2.8 | `input_media/` | ~7 个文件 | 同上 |
| 2.9 | `input_message_content/` | 2 个文件 | 同上 |
| 2.10 | `types/__init__.py` | 汇总导出 | 同上 |

完成标志：`from pyrogramX.types import Message, User, Chat` 可以导入。

---

### Phase 3：核心引擎

> 过滤器、处理器、分发器 — 事件驱动的核心。

| 步骤 | 内容 | 改动点 |
|------|------|--------|
| 3.1 | `filters.py` | 命名空间替换 |
| 3.2 | `handlers/` | 移植 12 个处理器 + 基类 |
| 3.3 | `parser/` | 移植 HTML/Markdown 解析器 |
| 3.4 | `dispatcher.py` | 命名空间替换；`asyncio.get_event_loop()` → `asyncio.get_running_loop()` |
| 3.5 | `utils.py` | 命名空间替换 |

完成标志：Dispatcher 可以实例化，filters 可以组合。

---

### Phase 4：方法层

> 所有 Client 方法，mixin 模式逐目录移植。

| 步骤 | 内容 | 方法数 | 优先级 |
|------|------|--------|--------|
| 4.1 | `methods/advanced/` | 3 | 最高 — invoke/resolve_peer 是一切的基础 |
| 4.2 | `methods/auth/` | 15 | 高 — 登录流程 |
| 4.3 | `methods/utilities/` | 8 | 高 — start/stop/run |
| 4.4 | `methods/users/` | 13 | 中 |
| 4.5 | `methods/messages/` | 49 | 中 — 最大的一组 |
| 4.6 | `methods/chats/` | 39 | 中 |
| 4.7 | `methods/bots/` | 16 | 中 |
| 4.8 | `methods/contacts/` | 5 | 低 |
| 4.9 | `methods/invite_links/` | 17 | 低 |
| 4.10 | `methods/password/` | 3 | 低 |
| 4.11 | `methods/decorators/` | 12 | 中 — 装饰器 |
| 4.12 | `methods/__init__.py` | Methods 聚合类 | 最后 |

完成标志：所有 180+ 方法可通过 `Client` 访问。

---

### Phase 5：Client 组装

> 把所有模块连接成完整的 Client。

| 步骤 | 内容 |
|------|------|
| 5.1 | `client.py` — 移植 Client 类，继承 Methods，组装 Session/Dispatcher/Storage/Parser |
| 5.2 | `__init__.py` — 包入口，导出 Client, idle, compose, StopPropagation 等 |

完成标志：

```python
import asyncio
from pyrogramX import Client, filters

app = Client("my_account", api_id=..., api_hash="...")

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("Hello!")

async def main():
    await app.start()
    await idle()
    await app.stop()

asyncio.run(main())
```

---

### Phase 6：验证与优化

| 步骤 | 内容 |
|------|------|
| 6.1 | 登录测试 — 手机号/bot token 登录 |
| 6.2 | 收发消息测试 |
| 6.3 | 文件上传/下载测试 |
| 6.4 | 所有 handler 类型测试 |
| 6.5 | `pyproject.toml` 补全依赖 |
| 6.6 | GitHub Action — scheme 更新自动重新编译 |

---

## 已知需改进的 Pyrogram 问题

移植时顺手修复，不额外增加工作量：

| 问题 | 位置 | 修复方案 |
|------|------|---------|
| `asyncio.get_event_loop()` 已弃用 | `client.py`, `dispatcher.py` | → `asyncio.get_running_loop()` |
| `inspect.stack()` hack | `storage/sqlite_storage.py` | 用显式列名参数替代 |
| 硬编码 TCPAbridged | `connection/connection.py` | 加 `transport` 参数（默认 TCPAbridged） |

---

## 依赖关系图

```
                    raw/ (✅ 已完成)
                      │
         ┌────────────┼────────────┐
         │            │            │
      crypto/    errors/       enums/
         │            │            │
    connection/       │            │
         │            │            │
      session/        │            │
         │            │            │
         └─────┬──────┘            │
               │                   │
            types/ ←───────────────┘
               │
         ┌─────┼──────┐
         │     │      │
    filters  handlers  parser/
         │     │      │
         └─────┼──────┘
               │
          dispatcher
               │
          methods/
               │
           client.py
               │
         __init__.py
```

> 从下往上实现，每一层只依赖已完成的层。

---

## 移植原则

1. **逐文件移植** — 不要一次性复制整个目录，逐个文件处理，确保每个文件的导入都正确
2. **只改命名空间** — 大部分文件只需 `pyrogram` → `pyrogramX`，不改业务逻辑
3. **每阶段可验证** — 每个 Phase 结束后有明确的验证标准
4. **不增不减** — 不添加新功能，不删减现有功能，保持 API 完全兼容
5. **顺手修 bug** — 上表列出的已知问题在移植时修复，不单独开工
