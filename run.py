#!/usr/bin/env python3
"""
运行脚本
"""
import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    # 从环境变量获取端口，默认为5000
    port = int(os.environ.get('PORT', 5000))
    
    # 运行应用
    app.run(
        host='0.0.0.0',
        port=port,
        debug=app.config.get('DEBUG', False)
    )