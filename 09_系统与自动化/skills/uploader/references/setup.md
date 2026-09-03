# 本地配置

```bash
python3 -m pip install oss2
```

在本机密钥管理方式或被 Git 忽略的 `.env` 中设置：

```text
OSS_ACCESS_KEY_ID=...
OSS_ACCESS_KEY_SECRET=...
OSS_BUCKET=...
OSS_ENDPOINT=https://oss-cn-<region>.aliyuncs.com
OSS_PREFIX=material-library/v1
```

`OSS_PREFIX` 可选。拍摄人员建议使用只能写入该前缀的 RAM 账号，制作人员使用只读 RAM 账号。存储细节见 [storage-schema.md](storage-schema.md)。
