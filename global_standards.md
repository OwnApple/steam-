# 推荐系统课设：全局工程与技术规范说明书 (Global Standards)

## 1. 技术栈选型 (Tech Stack)
为了高效实现基于Steam游戏数据的推荐系统，并构建完整的Web应用链条，项目规定采用以下技术方案：
- **后端架构**：**Python 3.x** + **Flask**。开发工具建议使用 **PyCharm Enterprise 版** 或 **VSCode**，必须配置好虚拟开发环境 (`venv`) 以隔离包版本体系。
- **前端页面**：直接使用 **Jinja2** 模板引擎渲染 HTML。为避免原生样式编写繁琐，引入 **Bootstrap V4** 外部 CSS 组件库以快速搭建现代化按钮及响应式表单。
- **数据库系统**：推荐接入 **MySQL (版本8.0以上注意防踩 `caching_sha2_password` 坑)**，且在 Python 环境中使用 `pymysql` 进行交互开发。并加入对重点频查列 (`比如 user_id`) 映射 DB 索引。
- **算法与数据模型库**：
  - 数据处理工具：`Pandas`, `NumPy`
  - 传统推荐（CF协同过滤等）：`Scikit-Learn`, `Surprise`
  - 深度推荐模型（如DSSM）：`TensorFlow/Keras` 或 `PyTorch`
- **开发与包管理工具**：配置 `requirements.txt` 及使用本地IDE（如 `VSCode`）进行核心开发。

## 2. 目录骨架构建 (Directory Structure)
规范化工程结构是“系统框架合理、具备可扩展性”打分的关键要求。拒绝一份代码干一件事相互挤压，所有目录务必遵循职责分离：
```text
Steam_Recommendation_System/
├── models/                  # 模型存放空间
│   └── DSSM-fixed.keras     # 预训练并剥离好的深度学习双塔模型，切勿运行时训练
├── static/                  # 静态资源，存放图像、CSS及JS文件 (引用的同时须使用 url_for 进行包裹以防相对路径失效)
├── templates/               # 前端页面渲染层。包含父基类(base.html) 及继承了基础页面的各子页面。
├── utils.py                 # 工具层。包含读写模型、清洗算法或与数据库交互的组件包。
├── models.py                # 后端面向对象表定义。负责创建 User类、算法调用方法并与 DB 进行存储。
├── app.py                   # Flask主程序的驱动与视图控制器 (路由分配器)
├── requirements.txt         # Pip依赖声明文件 (可通过 pip install -r 解决虚拟环境依赖)
└── /data /docs 等外部脚本... # (用于数据导入进 DB 及创建索引加速的Python清洗脚本)
```

## 3. 代码开发与命名规范 (Code Standards)
### 3.1 Python 全局规范 (基于 PEP8)
- **缩进与排版**：所有代码严格使用 4 个空格进行行缩进，禁止混杂或错位使用TAB。
- **命名规范策略**：
  - **包、模块 (Module)**：全小写，需要语义分割时用下划线关联（如 `collab_filter`）。
  - **类名 (Class)**：大驼峰命名法则（如 `GameRecommender`, `UserModel`）。
  - **函数名与变量名 (Function & Variable)**：小写字母拼接下划线 `snake_case`（如 `get_user_history`, `game_id`），做到“见名知意”。
  - **静态常数 (Constant)**：字母全大写并以下划线分割（如 `MAX_RECOMMEND_COUNT`, `DEFAULT_DB_PATH`）。
- **注释及代码可读性要求**：
  - 各个独立的算法逻辑函数和业务接口，**必须带有明确的文档注释（Docstring）**，必须说明该模块函数的输入参数、输出内容、变量类型及其对应业务流程原理。
  - 对于业务里不易理解的数据转换、特征生成切片、运算公式等地方，保留单行注释或块注释。

### 3.2 数据库规范 (Database Standards)
- **表字段设计规则**：数据库名称、表命名、以及所有数据列名均建议使用小写加下划线命名（例如 `user_logs`, `game_info`, `item_id`）。
- **完整性及约束**：涉及用户行为追踪时确保诸如 `user_id` 和 `game_id` 在相关表中具有正确的数据索引(Index)及可能的级联外键逻辑。

### 3.3 路由与模板基建规范
- **HTTP 动词与请求**：只拉取页面及展现使用 `GET` 请求。提交表单（登录、注册、对游戏评分打卡等数据落库行为），务必校验 `POST` 数据表单。
- **全局会话及 Hooks 钩子**：为了确保状态流转安全，必须配置 Flask `secret_key` 以防 Session 被窃取篡改。应用系统应该在每次请求前添加 `@app.before_request` 钩子检查会话（识别当前是否登录并存入全局变量 `g.user`），利用基于身份的重定向流（`redirect`、`url_for`）防御越权访问。
- **安全密码加密落库**：不允许使用明文密码保存用户信息；使用 `Werkzeug` 内置的 `generate_password_hash` & `check_password_hash` 进行库表读写的哈希加密操作。

## 4. 容错性与健壮保障 (Error Handling)
- **交互侧输入法制化防线**：所有接受前端参数的路由及逻辑入口处必须校验空值并处理类型错误。诸如用户注册时用户名长度不可越界、特殊字符进行封堵以防御攻击；界面应对错误输入返回明确并友好的前置提示面板（如Toast、Alert），而非直接抛出后台运行原生白屏错误导致前端失联 (Traceback)。
- **算法弹性降级**：考虑到诸如“冷启动”（新用户注册初始无日志记录），以及高维稀疏矩阵计算导致的推荐失败情况。业务流中必须内置容错机制，如果某推荐算法生成不出来结果集，系统应拥有自动填充随机热门游戏、默认最高评级作品展示的策略与备选方案。