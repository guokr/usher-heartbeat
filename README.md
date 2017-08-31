## 心跳脚本主要功能

- 检测服务存活
- 注册
- 向网关发送心跳

## 安装

## 使用方式

- 取得端口
```
root@ubuntu:~$ . pick_port && gunicorn -w 2 manage:app -b 0.0.0.0:${SERVER_PORT}
```

- 保持心跳
```
root@ubuntu:~$ heartbeat
```

## 需要的环境变量

- PROJECT 项目名
- SERVICE 服务名
- TOKEN 注册口令
- API_TYPE 服务类型
- YAML yaml文档路径
- USHER_ADDR 注册心跳地址
- SERVER_PORT 服务端口
