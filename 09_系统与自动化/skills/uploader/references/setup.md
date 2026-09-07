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

`OSS_PREFIX` 可选。脚本启动时会自动读取项目根目录中被 Git 忽略的 `.env`，已导出的系统环境变量优先。密钥值不得输出到日志。

拍摄人员建议使用只能写入该前缀的 RAM 账号，制作人员使用只读 RAM 账号。存储细节见 [storage-schema.md](storage-schema.md)。
