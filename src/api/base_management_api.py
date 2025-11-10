#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
浏览器管理API基础类
提供通用的浏览器实例管理界面
"""

import asyncio
from datetime import datetime
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from loguru import logger

class CreateInstanceRequest(BaseModel):
    """创建实例请求"""
    name: str


class InstanceResponse(BaseModel):
    """实例响应"""
    instance_id: str
    name: str
    status: str
    created_at: str
    last_used: str = None
    error_message: str = None
    is_busy: bool = False


def create_management_app(service_name: str, service_title: str, api_port: int, browser_manager) -> FastAPI:
    """创建浏览器管理API应用"""
    
    # 浏览器管理API应用
    management_app = FastAPI(
        title=f"{service_title} 浏览器管理",
        description=f"管理{service_name}多个浏览器实例",
        version="1.0.0"
    )

    @management_app.get("/", response_class=HTMLResponse)
    async def get_management_page():
        """获取管理页面"""
        html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{service_title} 浏览器管理</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 300;
        }}
        
        .header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        
        .stats {{
            display: flex;
            justify-content: space-around;
            padding: 20px;
            background: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
        }}
        
        .stat-item {{
            text-align: center;
            padding: 15px;
        }}
        
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            color: #4facfe;
        }}
        
        .stat-label {{
            color: #6c757d;
            margin-top: 5px;
        }}
        
        .controls {{
            padding: 30px;
            border-bottom: 1px solid #e9ecef;
        }}
        
        .create-form {{
            display: flex;
            gap: 15px;
            align-items: end;
            margin-bottom: 20px;
        }}
        
        .form-group {{
            flex: 1;
        }}
        
        .form-group label {{
            display: block;
            margin-bottom: 5px;
            font-weight: 500;
            color: #495057;
        }}
        
        .form-group input {{
            width: 100%;
            padding: 12px;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s;
        }}
        
        .form-group input:focus {{
            outline: none;
            border-color: #4facfe;
        }}
        
        .btn {{
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s;
            text-decoration: none;
            display: inline-block;
            text-align: center;
        }}
        
        .btn-primary {{
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
        }}
        
        .btn-primary:hover {{
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(79, 172, 254, 0.4);
        }}
        
        .btn-success {{
            background: #28a745;
            color: white;
        }}
        
        .btn-danger {{
            background: #dc3545;
            color: white;
        }}
        
        .btn-warning {{
            background: #ffc107;
            color: #212529;
        }}
        
        .btn-secondary {{
            background: #6c757d;
            color: white;
        }}
        
        .btn:hover {{
            transform: translateY(-1px);
            box-shadow: 0 3px 10px rgba(0,0,0,0.2);
        }}
        
        .btn:disabled {{
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }}
        
        .instances-list {{
            padding: 30px;
        }}
        
        .instance-card {{
            background: white;
            border: 2px solid #e9ecef;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            transition: all 0.3s;
        }}
        
        .instance-card:hover {{
            border-color: #4facfe;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}
        
        .instance-header {{
            display: flex;
            justify-content: between;
            align-items: center;
            margin-bottom: 15px;
        }}
        
        .instance-info {{
            flex: 1;
        }}
        
        .instance-name {{
            font-size: 1.3em;
            font-weight: 600;
            color: #212529;
            margin-bottom: 5px;
        }}
        
        .instance-id {{
            font-family: monospace;
            color: #6c757d;
            font-size: 0.9em;
        }}
        
        .instance-status {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin: 10px 0;
        }}
        
        .status-badge {{
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 500;
        }}
        
        .status-running {{
            background: #d4edda;
            color: #155724;
        }}
        
        .status-stopped {{
            background: #f8d7da;
            color: #721c24;
        }}
        
        .status-starting {{
            background: #fff3cd;
            color: #856404;
        }}
        
        .status-error {{
            background: #f5c6cb;
            color: #721c24;
        }}
        
        .instance-actions {{
            display: flex;
            gap: 10px;
            margin-top: 15px;
        }}
        
        .instance-meta {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 15px 0;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
        }}
        
        .meta-item {{
            display: flex;
            flex-direction: column;
        }}
        
        .meta-label {{
            font-size: 0.85em;
            color: #6c757d;
            margin-bottom: 3px;
        }}
        
        .meta-value {{
            font-weight: 500;
            color: #212529;
        }}
        
        .loading {{
            text-align: center;
            padding: 40px;
            color: #6c757d;
        }}
        
        .error-message {{
            background: #f8d7da;
            color: #721c24;
            padding: 10px;
            border-radius: 5px;
            margin-top: 10px;
            font-size: 0.9em;
        }}
        
        .refresh-btn {{
            position: fixed;
            bottom: 30px;
            right: 30px;
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            border: none;
            font-size: 24px;
            cursor: pointer;
            box-shadow: 0 5px 15px rgba(79, 172, 254, 0.4);
            transition: all 0.3s;
        }}
        
        .refresh-btn:hover {{
            transform: scale(1.1);
        }}
        
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        
        .spinning {{
            animation: spin 1s linear infinite;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 {service_title} 浏览器管理</h1>
            <p>管理多个浏览器实例，支持并发图片生成</p>
        </div>
        
        <div class="stats">
            <div class="stat-item">
                <div class="stat-number" id="total-instances">0</div>
                <div class="stat-label">总实例数</div>
            </div>
            <div class="stat-item">
                <div class="stat-number" id="running-instances">0</div>
                <div class="stat-label">运行中</div>
            </div>
            <div class="stat-item">
                <div class="stat-number" id="available-instances">0</div>
                <div class="stat-label">可用实例</div>
            </div>
            <div class="stat-item">
                <div class="stat-number" id="concurrency-count">0</div>
                <div class="stat-label">并发能力</div>
            </div>
        </div>
        
        <div class="controls">
            <div class="create-form">
                <div class="form-group">
                    <label for="instance-name">实例名称</label>
                    <input type="text" id="instance-name" placeholder="输入浏览器实例名称">
                </div>
                <button class="btn btn-primary" onclick="createInstance()">
                    ➕ 创建实例
                </button>
            </div>
        </div>
        
        <div class="instances-list">
            <div id="instances-container" class="loading">
                正在加载浏览器实例...
            </div>
        </div>
    </div>
    
    <button class="refresh-btn" onclick="loadInstances()" title="刷新">
        🔄
    </button>

    <script>
        let instances = [];
        
        // 页面加载时获取实例列表
        document.addEventListener('DOMContentLoaded', function() {{
            loadInstances();
            // 每30秒自动刷新
            setInterval(loadInstances, 30000);
        }});
        
        // 加载实例列表
        async function loadInstances() {{
            try {{
                const response = await fetch('/api/instances');
                const data = await response.json();
                instances = data.instances;
                renderInstances();
                updateStats();
            }} catch (error) {{
                console.error('加载实例失败:', error);
                document.getElementById('instances-container').innerHTML = 
                    '<div class="error-message">加载实例失败: ' + error.message + '</div>';
            }}
        }}
        
        // 渲染实例列表
        function renderInstances() {{
            const container = document.getElementById('instances-container');
            
            if (instances.length === 0) {{
                container.innerHTML = `
                    <div style="text-align: center; padding: 40px; color: #6c757d;">
                        <h3>暂无浏览器实例</h3>
                        <p>点击上方"创建实例"按钮来创建第一个浏览器实例</p>
                    </div>
                `;
                return;
            }}
            
            container.innerHTML = instances.map(instance => `
                <div class="instance-card">
                    <div class="instance-header">
                        <div class="instance-info">
                            <div class="instance-name">${{instance.name}}</div>
                            <div class="instance-id">ID: ${{instance.instance_id}}</div>
                        </div>
                    </div>
                    
                    <div class="instance-status">
                        <span class="status-badge status-${{instance.status}}">${{getStatusText(instance.status)}}</span>
                        ${{instance.is_busy ? '<span class="status-badge" style="background: #ffeaa7; color: #2d3436;">忙碌中</span>' : ''}}
                    </div>
                    
                    <div class="instance-meta">
                        <div class="meta-item">
                            <div class="meta-label">创建时间</div>
                            <div class="meta-value">${{formatDateTime(instance.created_at)}}</div>
                        </div>
                        <div class="meta-item">
                            <div class="meta-label">最后使用</div>
                            <div class="meta-value">${{instance.last_used ? formatDateTime(instance.last_used) : '从未使用'}}</div>
                        </div>
                    </div>
                    
                    ${{instance.error_message ? `<div class="error-message">错误: ${{instance.error_message}}</div>` : ''}}
                    
                    <div class="instance-actions">
                        ${{getActionButtons(instance)}}
                    </div>
                </div>
            `).join('');
        }}
        
        // 获取状态文本
        function getStatusText(status) {{
            const statusMap = {{
                'running': '运行中',
                'stopped': '已停止',
                'starting': '启动中',
                'error': '错误'
            }};
            return statusMap[status] || status;
        }}
        
        // 获取操作按钮
        function getActionButtons(instance) {{
            if (instance.status === 'running') {{
                return `
                    <button class="btn btn-danger" onclick="stopInstance('${{instance.instance_id}}')">
                        ⏹️ 停止
                    </button>
                `;
            }} else if (instance.status === 'stopped' || instance.status === 'error') {{
                return `
                    <button class="btn btn-success" onclick="startInstance('${{instance.instance_id}}')">
                        ▶️ 启动
                    </button>
                    <button class="btn btn-danger" onclick="deleteInstance('${{instance.instance_id}}')">
                        🗑️ 删除
                    </button>
                `;
            }} else if (instance.status === 'starting') {{
                return `
                    <button class="btn btn-secondary" disabled>
                        ⏳ 启动中...
                    </button>
                `;
            }}
            return '';
        }}
        
        // 更新统计信息
        function updateStats() {{
            const total = instances.length;
            const running = instances.filter(i => i.status === 'running').length;
            const available = instances.filter(i => i.status === 'running' && !i.is_busy).length;
            
            document.getElementById('total-instances').textContent = total;
            document.getElementById('running-instances').textContent = running;
            document.getElementById('available-instances').textContent = available;
            document.getElementById('concurrency-count').textContent = running;
        }}
        
        // 格式化日期时间
        function formatDateTime(dateStr) {{
            if (!dateStr) return '';
            const date = new Date(dateStr);
            return date.toLocaleString('zh-CN');
        }}
        
        // 创建实例
        async function createInstance() {{
            const nameInput = document.getElementById('instance-name');
            const name = nameInput.value.trim();
            
            if (!name) {{
                alert('请输入实例名称');
                return;
            }}
            
            try {{
                const response = await fetch('/api/instances', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify({{ name }})
                }});
                
                if (response.ok) {{
                    nameInput.value = '';
                    loadInstances();
                }} else {{
                    const error = await response.json();
                    alert('创建实例失败: ' + error.detail);
                }}
            }} catch (error) {{
                alert('创建实例失败: ' + error.message);
            }}
        }}
        
        // 启动实例
        async function startInstance(instanceId) {{
            try {{
                const response = await fetch(`/api/instances/${{instanceId}}/start`, {{
                    method: 'POST'
                }});
                
                if (response.ok) {{
                    loadInstances();
                }} else {{
                    const error = await response.json();
                    alert('启动实例失败: ' + error.detail);
                }}
            }} catch (error) {{
                alert('启动实例失败: ' + error.message);
            }}
        }}
        
        // 停止实例
        async function stopInstance(instanceId) {{
            if (!confirm('确定要停止这个实例吗？')) {{
                return;
            }}
            
            try {{
                const response = await fetch(`/api/instances/${{instanceId}}/stop`, {{
                    method: 'POST'
                }});
                
                if (response.ok) {{
                    loadInstances();
                }} else {{
                    const error = await response.json();
                    alert('停止实例失败: ' + error.detail);
                }}
            }} catch (error) {{
                alert('停止实例失败: ' + error.message);
            }}
        }}
        
        // 删除实例
        async function deleteInstance(instanceId) {{
            if (!confirm('确定要删除这个实例吗？此操作不可恢复！')) {{
                return;
            }}
            
            try {{
                const response = await fetch(`/api/instances/${{instanceId}}`, {{
                    method: 'DELETE'
                }});
                
                if (response.ok) {{
                    loadInstances();
                }} else {{
                    const error = await response.json();
                    alert('删除实例失败: ' + error.detail);
                }}
            }} catch (error) {{
                alert('删除实例失败: ' + error.message);
            }}
        }}
        
        // 回车键创建实例
        document.getElementById('instance-name').addEventListener('keypress', function(e) {{
            if (e.key === 'Enter') {{
                createInstance();
            }}
        }});
    </script>
</body>
</html>
        """
        return HTMLResponse(content=html_content)

    @management_app.get("/api/instances")
    async def list_instances():
        """获取所有实例列表"""
        try:
            instances = browser_manager.list_instances()
            concurrency = browser_manager.get_concurrency_count()
            
            return {
                "success": True,
                "instances": instances,
                "concurrency_count": concurrency,
                "total_count": len(instances)
            }
        except Exception as e:
            logger.error(f"获取实例列表失败: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @management_app.post("/api/instances")
    async def create_instance(request: CreateInstanceRequest):
        """创建新实例"""
        try:
            instance_id = browser_manager.create_instance(request.name)
            return {
                "success": True,
                "instance_id": instance_id,
                "message": "实例创建成功"
            }
        except Exception as e:
            logger.error(f"创建实例失败: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @management_app.post("/api/instances/{instance_id}/start")
    async def start_instance(instance_id: str):
        """启动实例"""
        try:
            success = await browser_manager.start_instance(instance_id)
            if success:
                return {"success": True, "message": "实例启动成功"}
            else:
                raise HTTPException(status_code=400, detail="实例启动失败")
        except Exception as e:
            logger.error(f"启动实例失败: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @management_app.post("/api/instances/{instance_id}/stop")
    async def stop_instance(instance_id: str):
        """停止实例"""
        try:
            success = await browser_manager.stop_instance(instance_id)
            if success:
                return {"success": True, "message": "实例停止成功"}
            else:
                raise HTTPException(status_code=400, detail="实例停止失败")
        except Exception as e:
            logger.error(f"停止实例失败: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @management_app.delete("/api/instances/{instance_id}")
    async def delete_instance(instance_id: str):
        """删除实例"""
        try:
            success = await browser_manager.delete_instance(instance_id)
            if success:
                return {"success": True, "message": "实例删除成功"}
            else:
                raise HTTPException(status_code=400, detail="实例删除失败")
        except Exception as e:
            logger.error(f"删除实例失败: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @management_app.get("/api/instances/{instance_id}")
    async def get_instance(instance_id: str):
        """获取单个实例信息"""
        try:
            instance = browser_manager.get_instance(instance_id)
            if instance:
                return {"success": True, "instance": instance.to_dict()}
            else:
                raise HTTPException(status_code=404, detail="实例不存在")
        except Exception as e:
            logger.error(f"获取实例信息失败: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @management_app.get("/api/stats")
    async def get_stats():
        """获取统计信息"""
        try:
            instances = browser_manager.list_instances()
            running_instances = browser_manager.get_running_instances()
            available_count = len([i for i in running_instances if not i.is_busy])
            
            return {
                "success": True,
                "stats": {
                    "total_instances": len(instances),
                    "running_instances": len(running_instances),
                    "available_instances": available_count,
                    "concurrency_count": len(running_instances)
                }
            }
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    return management_app
