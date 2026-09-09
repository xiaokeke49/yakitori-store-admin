---
name: uploader
description: Manage and inspect the yakitori shop's Aliyun OSS media library. Use to see inventory and category statistics, search remote assets, identify already-uploaded versus new media from a supplied directory, visually classify new files, upload idempotently, or pull classified batches. Do not use for publishing or deleting remote assets.
---

# Uploader（OSS 素材库）

接收用户给出的任意素材目录。目录可以全部已上传、部分已上传或全部未上传。始终用文件内容 SHA-256 与 OSS 索引对比，不用文件名、本地路径、日期或单机状态判断是否上传过。

用户需要整体使用方法时，读 [使用说明.md](使用说明.md)。

## 查看素材库

用户问“素材库有什么”、“各分类有多少”、“某类素材有哪些”或“帮我找某个素材”时，运行只读 `inventory`。不需要扫描本地目录，不下载原文件。

```bash
python3 scripts/oss_materials.py inventory
python3 scripts/oss_materials.py inventory --category "烧烤食材展示"
python3 scripts/oss_materials.py inventory --search "湖边"
python3 scripts/oss_materials.py inventory --json
```

默认回答应包含：唯一素材数、总大小、批次数和各分类数量。按分类或关键词查询时，再列出文件名和大小。查看操作不得写入、删除或下载 OSS 对象。

## 处理用户给的目录

1. 用 [scripts/oss_materials.py](scripts/oss_materials.py) 扫描整个目录，递归识别支持的图片、视频和音频。
2. `scan` 为每个文件计算 SHA-256，查询 OSS `catalog/<hash>.json`，然后生成计划：
   - `already_uploaded: true`：不重新分类，直接使用远程正式分类。
   - `already_uploaded: false`：只对这些新内容做视觉分类。
3. 查看每个新图片；对新视频抽取能覆盖主要场景的代表帧。路径只能当候选分类，不能代替看画面。
4. 确认新文件的 `category` 后将 `reviewed` 改为 `true`。不确定时放入“其他待判断”，不硬猜。
5. 新素材入库名称统一为 `YYYYMMDD_分类_内容_两位序号.扩展名`；日期无法确认时用“日期待确认”，内容无法确认时用“素材”。只修改计划中的 `original_name` 和 `relative_path`，不改动用户的原始文件。
6. 先运行上传预览，报告总数、已存在数、待上传数和各分类数量。只有用户明确要上传且范围一致时，才加 `--execute`。

```bash
python3 scripts/oss_materials.py scan --source "/absolute/path/to/supplied-folder" --topic "湖边晚风"
python3 scripts/oss_materials.py upload --plan "/absolute/path/to/generated-plan.json"
python3 scripts/oss_materials.py upload --plan "/absolute/path/to/generated-plan.json" --execute
```

## 分类

正式分类只有：店内环境宣传、后湖湖边茶饮、后湖落日湖景、烧烤成品特写、烧烤烤制过程、烧烤食材展示、冰箱展示、晚霞、烧鸟烤串、卖花素材、生串、其他待判断。

已有 hash 的远程分类是正式来源。如果本次计划与远程分类冲突，停止并报告，不自动覆盖。

## 入库命名

- 格式：`YYYYMMDD_分类_内容_两位序号.扩展名`。
- 同一批次内序号从 `01` 开始，名称必须唯一。
- 原图、透明抠图、截图等衍生类型写入“内容”。
- 不根据画面猜测菜名、人物姓名或日期；无法确认时使用中性描述。
- 原始素材默认只读。规范名称写入上传计划和 OSS 索引，下载时使用规范名称。

## 幂等规则

- 原始内容存在 `objects/sha256/<hash>`，相同内容只存一份，改名或换目录也不重传。
- 分类存在 `catalog/<hash>.json`，新 hash 才新建分类。
- 批次 ID 由目录中的 hash 和相对路径稳定生成，相同目录内容重复执行得到同一批次。
- 上传时再次查询远程，防止扫描之后其他同学已上传造成重复。
- 禁止自动删除、覆盖原始内容或覆盖已有分类。

## 拉取

`pull` 默认拉取本机未见过的批次，首次只拉最近 3 个。下载结构为：

```text
output/OSS素材库/已同步素材/<分类>/<拍摄日期>/<批次主题>/<原相对路径>
```

本地相同内容跳过；同名不同内容不覆盖，另存 `.remote-<hash>` 版本。

## 配置

需要 `OSS_ACCESS_KEY_ID`、`OSS_ACCESS_KEY_SECRET`、`OSS_BUCKET` 和 `OSS_ENDPOINT`。凭据只从环境读取，不写入项目、日志、清单或 Git。缺少配置时读 [references/setup.md](references/setup.md)，不要让用户在对话中粘贴密钥。
