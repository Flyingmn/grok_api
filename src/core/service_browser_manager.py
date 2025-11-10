#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务专用浏览器实例管理器
支持不同服务的独立浏览器实例管理
"""

import asyncio
import json
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Type
from loguru import logger


class ServiceBrowserInstance:
    """服务浏览器实例基类"""
    
    def __init__(self, instance_id: str, name: str = None, service_type: str = "unknown"):
        self.instance_id = instance_id
        self.name = name or f"{service_type}_{instance_id[:8]}"
        self.service_type = service_type
        self.client = None
        self.status = "stopped"  # stopped, starting, running, error
        self.created_at = datetime.now().isoformat()
        self.last_used = None
        self.error_message = None
        self.is_busy = False  # 是否正在执行任务
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "instance_id": self.instance_id,
            "name": self.name,
            "service_type": self.service_type,
            "status": self.status,
            "created_at": self.created_at,
            "last_used": self.last_used,
            "error_message": self.error_message,
            "is_busy": self.is_busy
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ServiceBrowserInstance':
        """从字典创建实例"""
        instance = cls(
            data["instance_id"], 
            data.get("name"), 
            data.get("service_type", "unknown")
        )
        instance.status = data.get("status", "stopped")
        instance.created_at = data.get("created_at")
        instance.last_used = data.get("last_used")
        instance.error_message = data.get("error_message")
        instance.is_busy = data.get("is_busy", False)
        return instance


class ServiceBrowserManager(ABC):
    """服务浏览器管理器基类"""
    
    def __init__(self, service_name: str, client_class: Type):
        self.service_name = service_name
        self.client_class = client_class
        self.instances: Dict[str, ServiceBrowserInstance] = {}
        self.data_file = Path(f"data/{service_name.lower()}_browser_instances.json")
        self.data_file.parent.mkdir(exist_ok=True)
        self.load_instances()
    
    def load_instances(self):
        """从文件加载实例数据"""
        try:
            if self.data_file.exists():
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for instance_data in data.get("instances", []):
                    instance = ServiceBrowserInstance.from_dict(instance_data)
                    # 启动时所有实例都是停止状态
                    instance.status = "stopped"
                    instance.is_busy = False
                    self.instances[instance.instance_id] = instance
                
                logger.info(f"加载了 {len(self.instances)} 个{self.service_name}浏览器实例配置")
            else:
                logger.info(f"未找到{self.service_name}浏览器实例配置文件，将创建新的")
                
        except Exception as e:
            logger.error(f"加载{self.service_name}浏览器实例配置失败: {e}")
    
    def save_instances(self):
        """保存实例数据到文件"""
        try:
            data = {
                "service_name": self.service_name,
                "instances": [instance.to_dict() for instance in self.instances.values()],
                "updated_at": datetime.now().isoformat()
            }
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            logger.debug(f"{self.service_name}浏览器实例配置已保存")
            
        except Exception as e:
            logger.error(f"保存{self.service_name}浏览器实例配置失败: {e}")
    
    def create_instance(self, name: str = None) -> str:
        """创建新的浏览器实例"""
        instance_id = str(uuid.uuid4())
        instance = ServiceBrowserInstance(instance_id, name, self.service_name)
        self.instances[instance_id] = instance
        self.save_instances()
        
        logger.info(f"创建新的{self.service_name}浏览器实例: {instance.name} ({instance_id})")
        return instance_id
    
    async def start_instance(self, instance_id: str) -> bool:
        """启动浏览器实例"""
        if instance_id not in self.instances:
            logger.error(f"{self.service_name}浏览器实例不存在: {instance_id}")
            return False
        
        instance = self.instances[instance_id]
        
        if instance.status == "running":
            logger.warning(f"{self.service_name}浏览器实例已在运行: {instance.name}")
            return True
        
        try:
            logger.info(f"启动{self.service_name}浏览器实例: {instance.name}")
            instance.status = "starting"
            instance.error_message = None
            self.save_instances()
            
            # 创建服务专用客户端
            client = self.client_class()
            client.instance_id = f"{self.service_name.lower()}_{instance_id}"
            
            # 初始化客户端
            logger.info(f"开始初始化{self.service_name}客户端...")
            init_result = await self._initialize_client(client)
            if not init_result:
                error_msg = f"{self.service_name}客户端初始化失败"
                logger.error(error_msg)
                raise Exception(error_msg)
            logger.success(f"{self.service_name}客户端初始化成功")
            
            instance.client = client
            instance.status = "running"
            instance.last_used = datetime.now().isoformat()
            self.save_instances()
            
            logger.success(f"{self.service_name}浏览器实例启动成功: {instance.name}")
            return True
            
        except Exception as e:
            logger.error(f"启动{self.service_name}浏览器实例失败: {instance.name} - {e}")
            instance.status = "error"
            instance.error_message = str(e)
            instance.client = None
            self.save_instances()
            return False
    
    @abstractmethod
    async def _initialize_client(self, client) -> bool:
        """初始化客户端（子类实现）"""
        pass
    
    async def stop_instance(self, instance_id: str) -> bool:
        """停止浏览器实例"""
        if instance_id not in self.instances:
            logger.error(f"{self.service_name}浏览器实例不存在: {instance_id}")
            return False
        
        instance = self.instances[instance_id]
        
        try:
            logger.info(f"停止{self.service_name}浏览器实例: {instance.name}")
            
            if instance.client:
                try:
                    # 确保完全清理浏览器资源
                    await instance.client.cleanup()
                    logger.info(f"已清理{self.service_name}浏览器客户端: {instance.name}")
                except Exception as e:
                    logger.warning(f"清理{self.service_name}浏览器客户端时出错: {instance.name} - {e}")
                finally:
                    instance.client = None
            
            instance.status = "stopped"
            instance.is_busy = False
            instance.error_message = None
            self.save_instances()
            
            logger.success(f"{self.service_name}浏览器实例已停止: {instance.name}")
            return True
            
        except Exception as e:
            logger.error(f"停止{self.service_name}浏览器实例失败: {instance.name} - {e}")
            instance.status = "error"
            instance.error_message = str(e)
            instance.client = None  # 确保清理引用
            self.save_instances()
            return False
    
    async def delete_instance(self, instance_id: str) -> bool:
        """删除浏览器实例"""
        if instance_id not in self.instances:
            logger.error(f"{self.service_name}浏览器实例不存在: {instance_id}")
            return False
        
        instance = self.instances[instance_id]
        
        # 如果实例正在运行，先强制停止它
        if instance.status == "running":
            logger.warning(f"{self.service_name}实例正在运行，强制停止后删除: {instance.name}")
            await self.stop_instance(instance_id)
        
        # 确保清理客户端资源
        if instance.client:
            try:
                await instance.client.cleanup()
                logger.info(f"已清理{self.service_name}实例客户端资源: {instance.name}")
            except Exception as e:
                logger.warning(f"清理{self.service_name}实例客户端资源失败: {instance.name} - {e}")
            instance.client = None
        
        del self.instances[instance_id]
        self.save_instances()
        
        logger.info(f"{self.service_name}浏览器实例已删除: {instance.name}")
        return True
    
    def get_instance(self, instance_id: str) -> Optional[ServiceBrowserInstance]:
        """获取浏览器实例"""
        return self.instances.get(instance_id)
    
    def list_instances(self) -> List[Dict[str, Any]]:
        """列出所有浏览器实例"""
        return [instance.to_dict() for instance in self.instances.values()]
    
    def get_running_instances(self) -> List[ServiceBrowserInstance]:
        """获取所有运行中的实例"""
        return [instance for instance in self.instances.values() 
                if instance.status == "running"]
    
    def get_available_instance(self) -> Optional[ServiceBrowserInstance]:
        """获取一个可用的（运行中且不忙碌的）实例"""
        for instance in self.instances.values():
            if instance.status == "running" and not instance.is_busy:
                return instance
        return None
    
    def set_instance_busy(self, instance_id: str, busy: bool = True):
        """设置实例忙碌状态"""
        if instance_id in self.instances:
            self.instances[instance_id].is_busy = busy
            self.instances[instance_id].last_used = datetime.now().isoformat()
            self.save_instances()
    
    def get_concurrency_count(self) -> int:
        """获取当前可并发数量（运行中的实例数量）"""
        return len(self.get_running_instances())
    
    async def cleanup_all(self):
        """清理所有实例"""
        logger.info(f"清理所有{self.service_name}浏览器实例...")
        
        for instance in self.instances.values():
            if instance.client:
                try:
                    await instance.client.cleanup()
                except Exception as e:
                    logger.error(f"清理{self.service_name}实例失败 {instance.name}: {e}")
                
                instance.client = None
                instance.status = "stopped"
                instance.is_busy = False
        
        self.save_instances()
        logger.success(f"所有{self.service_name}浏览器实例已清理")


class AIStudioBrowserManager(ServiceBrowserManager):
    """AI Studio浏览器管理器"""
    
    def __init__(self):
        from .interactive_ai_studio import AIStudioInteractiveClient
        super().__init__("AI_Studio", AIStudioInteractiveClient)
    
    async def _initialize_client(self, client) -> bool:
        """初始化AI Studio客户端"""
        try:
            # 初始化
            logger.info("开始初始化AI Studio客户端...")
            if not await client.setup():
                logger.error("AI Studio客户端setup失败")
                return False
            
            # 导航到AI Studio
            logger.info("导航到AI Studio页面...")
            if not await client.navigate_to_ai_studio():
                logger.error("导航到AI Studio失败")
                return False
            
            logger.success("AI Studio页面导航成功")
            
            # 查找输入元素
            logger.info("查找AI Studio输入元素...")
            if not await client.find_input_elements():
                logger.warning("未找到输入元素，但实例已启动")
            else:
                logger.success("AI Studio输入元素查找成功")
            
            return True
        except Exception as e:
            logger.error(f"初始化AI Studio客户端失败: {e}")
            return False


class DoubaoBrowserManager(ServiceBrowserManager):
    """豆包浏览器管理器"""
    
    def __init__(self):
        from .interactive_doubao_image import DoubaoImageInteractiveClient
        super().__init__("Doubao", DoubaoImageInteractiveClient)
    
    async def _initialize_client(self, client) -> bool:
        """初始化豆包客户端"""
        try:
            # 初始化
            logger.info("开始初始化豆包客户端...")
            if not await client.setup():
                logger.error("豆包客户端setup失败")
                return False
            
            # 导航到豆包
            logger.info("导航到豆包页面...")
            if not await client.navigate_to_doubao():
                logger.error("导航到豆包失败")
                return False
            
            logger.success("豆包页面导航成功")
            
            # 确保图像技能就绪
            logger.info("设置豆包图像技能...")
            if not await client.ensure_image_skill_ready():
                logger.warning("图像技能设置失败，但实例已启动")
            else:
                logger.success("豆包图像技能设置成功")
            
            return True
        except Exception as e:
            logger.error(f"初始化豆包客户端失败: {e}")
            return False


# 创建服务专用的管理器实例
ai_studio_browser_manager = AIStudioBrowserManager()
doubao_browser_manager = DoubaoBrowserManager()
