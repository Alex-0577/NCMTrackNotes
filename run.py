#!/usr/bin/env python3
'''run.py
应用运行入口文件
该文件是Flask应用的主运行脚本，负责启动应用服务器。
它创建Flask应用实例，配置服务器运行参数（主机、端口、调试模式），并启动应用。
'''
import os
from app import create_app

app = create_app()      # Flask 应用实例

if __name__ == '__main__':
    # 从环境变量获取端口，默认为5000
    port = int(os.environ.get('PORT', 5000))
    
    # 运行应用
    app.run(
        host='0.0.0.0',
        port=port,
        debug=app.config.get('DEBUG', False)
    )