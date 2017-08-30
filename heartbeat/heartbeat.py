#!/bin/env python
# -*- coding: utf-8 -*-

from json import dumps
from os import environ as env
import os
import sys
from time import sleep
import traceback
from uuid import uuid4

from requests import get, post
import yaml

from expand import expand

"""
监控gunicorn启动的web server
监控指标如下：
    - 端口占用情况 ss -lnt | grep 5000
    - supervisord 监听事件发送来的 event info
    - 如果web服务有健康检查 定时请求 /heath API 检查存活
    - 如果是异步任务 检测PID是否存在
监控到 server instance 挂掉的反应:
    - 停止发送心跳包
    - 全局变量 is_alive 设置为 False 直到服务启动
服务重新启动后 重新发送注册请求和心跳包 is_alive 设置为 True
"""


class UsherClientConfig(object):

    # 项目名
    PROJECT = env.get("PROJECT", "guokrplus")
    # 服务名
    SERVICE = env.get("SERVICE", "auth")
    # 注册口令
    TOKEN = env.get("TOKEN", "")
    # API 类型
    API_TYPE = env.get("API_TYPE", "restful")
    # 外部请求访问端口 在宿主机上 如果是异步任务的话就用uuid代替
    if API_TYPE == "async":
        PORT = str(uuid4().int)
    else:
        PORT = env.get("SERVER_PORT", "5000")
    # 网关地址
    USHER_ADDR = env.get("USHER_ADDR", "http://localhost:8888")
    # yaml 文件的位置
    YAML = env.get("YAML", "")
    # 服务版本
    VERSION = env.get("VERSION", "")

    def __init__(self):
        with open(self.YAML) as f:
            yaml_file = dumps(yaml.load(f))

        self.api_origin_spec = dumps(yaml.load(yaml_file))

        self.api_spec = dumps(expand(yaml.load(yaml_file)))

    @property
    def register_url(self):
        return self.USHER_ADDR + '/usher/register'

    @property
    def heartbeat_url(self):
        return self.USHER_ADDR + '/usher/heartbeat'


class MonitorAndHeartbeat():

    def __init__(self):
        self.config_params = UsherClientConfig()

    def check_port_listen(self, port):
        """
        检查端口占用情况
        ss -lnt | grep ':5000' | wc -l
        """
        import socket

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ret = False

        try:
            s.bind(("0.0.0.0", int(self.config_params.PORT)))
        except socket.error as e:
            if e.errno == 98:
                ret = True
        else:
            s.close()

        return ret

    def check_api_health(self, api_url):
        """
        检查健康API是否还在工作
        """
        ret = get(api_url)
        if ret.ok:
            return True
        return False

    def check_supervisor_event(self):
        """
        supervisor 事件推送
        """
        pass

    def check_process_id(self):
        """
        检查pid是否存在
        """
        try:
            with open("/tmp/asynx.pid") as pid_file:
                pid = int(pid_file.read())
                assert pid > 0
        except:
            # 文件版本不存在 或者pid异常
            return False

        try:
            os.kill(pid, 0)
        except OSError as error:
            if error.errno == 3:
                # No Such Process
                return False
            # 可能是权限问题(errno==1) 但是进程号是确实存在的
            return True
        else:
            return True

    def register(self):
        body = {
            "project": self.config_params.PROJECT,
            "service": self.config_params.SERVICE,
            "version": self.config_params.VERSION,
            "port": self.config_params.PORT,
            "api_spec": self.config_params.api_spec,
            "api_origin_spec": self.config_params.api_origin_spec,
        }
        ret = post(
            self.config_params.register_url,
            headers={
                "Authorization": self.config_params.TOKEN,
            },
            json=body,
            timeout=(1, 3),
        )
        if ret.ok:
            return True
        return False

    def heartbeat(self):
        body = {
            "project": self.config_params.PROJECT,
            "service": self.config_params.SERVICE,
            "port": self.config_params.PORT,
            "version": self.config_params.VERSION,
        }
        ret = post(self.config_params.heartbeat_url, json=body, timeout=(3, 5))
        if ret.ok:
            return True
        return False

    def start_work(self):
        is_registered = False
        while 1:
            try:
                if self.config_params.API_TYPE == "async":
                    assert self.check_process_id()
                else:
                    assert self.check_port_listen(self.config_params.PORT)

                if not is_registered:
                    if self.register():
                        is_registered = True
                    else:
                        is_registered = False
                else:
                    if self.heartbeat():
                        is_registered = True
                    else:
                        is_registered = False
            except:
                is_registered = False
                traceback.print_exc(file=sys.stdout)

            sleep(15)

if __name__ == "__main__":
    monitor = MonitorAndHeartbeat()
    monitor.start_work()
