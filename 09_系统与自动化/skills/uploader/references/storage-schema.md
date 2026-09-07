# OSS 存储模型

```text
material-library/v1/
├── objects/sha256/<first-2>/<full-sha256>
├── catalog/<first-2>/<full-sha256>.json
└── batches/<deterministic-batch-id>.json
```

`objects` 存原始字节，以 SHA-256 为唯一标识；改名不会复制存储。`catalog` 每个 hash 一个 JSON，记录正式分类、大小、Content-Type 和对象键。Catalog 存在即表示该内容已完成上传和分类。

`batches` 记录一次用户给出的目录视图：主题、日期、原相对路径、hash 和分类，不复制原始文件。
