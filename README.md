# Recomind 智能推荐系统

**基于自然语言处理与机器学习的智能推荐系统设计与实现**（本科毕业设计项目）

本项目实现了一个电影智能推荐系统：使用中文分词（jieba）与 TF-IDF 提取电影文本特征，
结合**基于内容的推荐**、**基于物品的协同过滤**与**混合推荐**算法，
通过 PyQt5 桌面界面提供个性化的电影推荐，并使用 MySQL 存储业务数据。

---

## 一、功能特性

- 用户注册 / 登录（密码 SHA-256 加盐哈希存储）
- **个性推荐**：融合内容推荐 + 协同过滤的混合推荐
- **关键词推荐**：输入兴趣描述，按文本相似度推荐电影
- **电影浏览 / 搜索**：按片名、导演、关键词搜索，按类型筛选
- **电影详情**：查看简介、平均评分，提交评分与评语，展示相似电影
- **数据管理**：电影增删改查、用户管理、评分数据查看与统计

## 二、技术栈

| 层次 | 技术 |
| --- | --- |
| 开发语言 | Python 3.8+ |
| 桌面界面 | PyQt5 |
| 数据库 | MySQL 8.0（PyMySQL 驱动） |
| 中文分词 | jieba |
| 机器学习 | scikit-learn（TF-IDF、余弦相似度） |
| 数值计算 | numpy |

## 三、项目结构

```
Recomind/
├── main.py                  # 程序入口
├── config.py                # 全局配置（数据库、路径、推荐参数）
├── requirements.txt         # 依赖清单
├── db/                      # 数据库层
│   ├── connection.py        #   连接管理与通用增删改查
│   ├── models.py            #   建表 DDL 与数据实体
│   └── init_db.py           #   建库建表初始化
├── nlp/                     # NLP 层
│   ├── text_processor.py    #   文本清洗、jieba 分词、停用词过滤
│   └── feature.py           #   TF-IDF 向量化与余弦相似度
├── recommender/             # 推荐算法层
│   ├── content_based.py     #   基于内容的推荐
│   ├── collaborative.py     #   基于物品的协同过滤
│   └── hybrid.py            #   混合推荐
├── services/                # 业务服务层
│   ├── user_service.py      #   用户注册登录
│   ├── movie_service.py      #   电影增删改查
│   ├── rating_service.py    #   评分与统计
│   ├── history_service.py   #   浏览历史
│   └── recommend_service.py #   推荐编排
├── data/                    # 数据层
│   ├── sample_data.py       #   示例电影/用户/评分
│   ├── seed_data.py         #   数据导入脚本
│   └── stopwords.txt        #   停用词表
├── ui/                      # 界面层
│   ├── main_window.py       #   主窗口
│   ├── login_dialog.py      #   登录注册
│   ├── recommend_page.py    #   个性推荐页
│   ├── search_page.py       #   电影浏览搜索页
│   ├── detail_dialog.py     #   电影详情与评分
│   ├── manage_page.py       #   数据管理页
│   ├── widgets.py           #   通用组件（电影卡片、星级评分）
│   └── styles.py            #   全局样式
├── scripts/
│   ├── init_database.sql    #   数据库初始化 SQL
│   └── init_database.bat    #   一键初始化脚本（Windows）
└── README.md
```

## 四、环境要求

1. **Python 3.8 及以上**（开发环境为 3.12）
2. **MySQL 8.0**（本地已安装并启动，服务名通常为 `MySQL80`）
3. Windows 操作系统（也兼容 macOS / Linux，需自行安装 PyQt5）

## 五、安装与运行

### 1. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

> 本项目已附带 `vendor/` 目录，内含 scikit-learn、scipy、cryptography 等第三方依赖，
> 程序启动时会自动加载（见 `main.py` 顶部的路径引导）。因此即使跳过上面的安装命令，
> 只要已安装 PyQt5 / jieba / numpy / PyMySQL，也可直接运行。
> 若你已用 `pip install -r requirements.txt` 装好全部依赖，可删除 `vendor/` 目录以节省空间。

### 1.1 系统自检（可选）

运行自检脚本，验证 NLP、推荐算法与数据库集成是否正常：

```bash
python tests/test_system.py          # 基础自检
python tests/test_system.py --reset  # 重置示例数据后再自检
```

### 2. 配置数据库

打开项目根目录下的 `config.py`，将 `DB_CONFIG` 中的 `password` 改为你本机 MySQL 的密码：

```python
DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "你的MySQL密码",   # ← 修改这里
    "charset": "utf8mb4",
    "database": "recomind",
}
```

> 数据库 `recomind` 会在程序启动时自动创建，无需手动建库。

### 3. 运行程序

```bash
python main.py
```

首次启动会自动：建库建表 → 导入示例数据 → 弹出登录窗口。

### 4. 拉取 TMDB 真实片库与海报（推荐）

电影数据默认来自 `data/sample_data.py` 的离线示例。接入 TMDB 后可获得真实片库、导演、类型、简介、评分与影评：

1. 在 https://www.themoviedb.org/settings/api 免费申请 API Key（v3）；
2. 打开 `config.py`，把 Key 填入 `TMDB_API_KEY`；
3. 拉取真实片库（会重建电影数据并生成演示评分）：

   ```bash
   python -m scripts.fetch_movies --pages 3
   ```

4. 如需单独补充/更新海报：

   ```bash
   python -m scripts.fetch_posters --force
   ```

采集内容：高分榜 + 热门榜的真实电影（自动过滤冷门/未上映）、导演、制片公司、类型、简介、海报、TMDB 评分与评分人数、真实影评；
同时为演示用户生成模拟评分用于协同过滤。无网络或未配置 Key 时，程序仍可用离线示例数据运行。

## 六、使用说明

### 登录 / 注册

- 直接使用演示账号登录：

  | 账号 | 密码 | 偏好 |
  | --- | --- | --- |
  | alice | 123456 | 文学 |
  | carol | 123456 | 计算机 |
  | erin | 123456 | 历史 |

- 也可切换到「注册」页自行注册新账号。

### 个性推荐

登录后默认进入「个性推荐」页，系统会：
1. 基于你高分评价的电影，用 TF-IDF + 余弦相似度做**内容推荐**；
2. 基于全体用户评分矩阵做**协同过滤**；
3. 二者按权重融合为**混合推荐**结果。

新用户（无评分、无浏览）会退化为**热门电影推荐**。

也可以在输入框输入兴趣描述（如“科幻 宇宙”“机器学习 编程”），点击「智能推荐」按文本相似度推荐。

### 电影浏览与搜索

- 输入片名/导演/关键词搜索；
- 下拉框按类型筛选；
- 点击电影卡片查看详情。

### 评分

在电影详情页点击星星选择 1~5 分，可填写评语后提交；提交后平均分实时更新，并影响后续推荐。

### 数据管理

「数据管理」页包含三个标签：
- **电影管理**：新增、编辑、删除电影；
- **用户管理**：查看与删除用户；
- **评分数据**：查看全部评分明细。

## 七、数据库手动初始化（可选）

程序启动时会自动初始化，如需手动执行：

- 命令行：`mysql -u root -p < scripts/init_database.sql`
- 或双击 `scripts/init_database.bat`

## 八、常见问题

1. **启动报“数据库初始化失败”**
   - 确认 MySQL 服务已启动（服务名 `MySQL80`）；
   - 确认 `config.py` 中密码正确；
   - 确认已安装 `cryptography` 包（MySQL 8 密码认证需要）。

2. **`ModuleNotFoundError: PyQt5` 等**
   - 执行 `pip install -r requirements.txt`。

3. **界面中文乱码**
   - 脚本与数据文件均为 UTF-8 编码，请保持默认编码不变。

## 九、算法说明（答辩要点）

- **内容推荐**：对电影文本（片名+导演+类型+简介）做 jieba 分词、去停用词，用 TF-IDF 构造特征向量，余弦相似度衡量电影间相似程度；
- **协同过滤**：基于用户评分矩阵做物品相似度计算（评分均值中心化 + 余弦相似度），为用户预测未评分电影的兴趣分；
- **混合推荐**：将两类推荐分数分别归一化后按权重加权融合（默认内容 0.6、协同 0.4）；
- **冷启动**：无历史数据的新用户退化为热门推荐或基于浏览历史的推荐。
