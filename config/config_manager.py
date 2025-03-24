# -*- coding: utf-8 -*-
"""
统一配置管理模块，负责所有配置的加载、保存和访问。
"""
import json
import os
from typing import Any, Dict, List, Optional


class ConfigSection:
    """配置节基类，提供基本的配置加载和保存功能"""
    
    def __init__(self, file_path: str, default_config: Dict[str, Any]):
        """
        初始化配置节
        
        Args:
            file_path: 配置文件路径
            default_config: 默认配置
        """
        self.file_path = file_path
        self.default_config = default_config
        self.config = default_config.copy()
        self.load()
    
    def load(self) -> None:
        """从文件加载配置"""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # 更新配置，保留默认值
                    for key, value in loaded_config.items():
                        if key in self.config:
                            self.config[key] = value
            except json.JSONDecodeError:
                print(f"警告: 配置文件 {self.file_path} 格式错误，将使用默认配置")
    
    def save(self) -> None:
        """保存配置到文件"""
        # 确保目录存在
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """设置配置项"""
        self.config[key] = value
    
    def update(self, config_dict: Dict[str, Any]) -> None:
        """批量更新配置"""
        for key, value in config_dict.items():
            if key in self.config:
                self.config[key] = value
        self.save()
    
    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self.config.copy()


class ApiKeyConfig(ConfigSection):
    """API密钥配置管理"""
    
    def __init__(self, file_path: str = "config/api_keys.json"):
        super().__init__(file_path, {})
    
    def add_key(self, service_name: str, api_key: str) -> None:
        """添加或更新API密钥"""
        self.config[service_name] = api_key
        self.save()
    
    def get_key(self, service_name: str) -> Optional[str]:
        """获取指定服务的API密钥"""
        return self.config.get(service_name)
    
    def list_services(self) -> List[str]:
        """列出所有已配置的服务名称"""
        return list(self.config.keys())
    
    def delete_key(self, service_name: str) -> bool:
        """删除指定服务的API密钥"""
        if service_name in self.config:
            del self.config[service_name]
            self.save()
            return True
        return False


class EmailConfig(ConfigSection):
    """邮件配置管理"""
    
    def __init__(self, file_path: str = "config/email_config.json"):
        default_config = {
            "email_from": "",
            "email_to": "",
            "email_password": "",
            "smtp_server": "smtp.qq.com",
            "smtp_port": 465,
            "send_each": True,
            "send_final": True,
            "custom_email_content": ""
        }
        super().__init__(file_path, default_config)


class ScenarioConfig(ConfigSection):
    """测试场景配置管理"""
    
    def __init__(self, file_path: str = "config/test_scenarios.json"):
        default_scenarios = [
            {
                "name": "默认场景",
                "input_len": 50,
                "output_len": 1024,
                "concurrency": 4,
                "num_prompts": 20,
                "range_ratio": 1.0,
                "prefix_len": 0
            }
        ]
        super().__init__(file_path, {"scenarios": default_scenarios})
    
    def get_scenarios(self) -> List[Dict[str, Any]]:
        """获取所有测试场景"""
        return self.config.get("scenarios", [])
    
    def add_scenario(self, scenario: Dict[str, Any]) -> None:
        """添加测试场景"""
        if "scenarios" not in self.config:
            self.config["scenarios"] = []
        self.config["scenarios"].append(scenario)
        self.save()
    
    def update_scenario(self, index: int, scenario: Dict[str, Any]) -> bool:
        """更新测试场景"""
        scenarios = self.get_scenarios()
        if 0 <= index < len(scenarios):
            scenarios[index] = scenario
            self.config["scenarios"] = scenarios
            self.save()
            return True
        return False
    
    def delete_scenario(self, index: int) -> bool:
        """删除测试场景"""
        scenarios = self.get_scenarios()
        if 0 <= index < len(scenarios):
            del scenarios[index]
            self.config["scenarios"] = scenarios
            self.save()
            return True
        return False


class AppConfig(ConfigSection):
    """应用程序配置管理"""
    
    def __init__(self, file_path: str = "config/app_config.json"):
        default_config = {
            "base_url": "http://127.0.0.1:8000",
            "model": "test",
            "tokenizer": "",
            "backend": "openai",
            "endpoint": "/v1/completions",
            "theme": "light",
            "last_log_dir": "",
            "window_size": (900, 700)
        }
        super().__init__(file_path, default_config)


class ConfigManager:
    """统一配置管理器，管理所有配置节"""
    
    def __init__(self, config_dir: str = "config"):
        """
        初始化配置管理器
        
        Args:
            config_dir: 配置文件目录
        """
        self.config_dir = config_dir
        os.makedirs(config_dir, exist_ok=True)
        
        # 初始化各配置节
        self.api_keys = ApiKeyConfig(os.path.join(config_dir, "api_keys.json"))
        self.email = EmailConfig(os.path.join(config_dir, "email_config.json"))
        self.scenarios = ScenarioConfig(os.path.join(config_dir, "test_scenarios.json"))
        self.app = AppConfig(os.path.join(config_dir, "app_config.json"))
    
    def save_all(self) -> None:
        """保存所有配置"""
        self.api_keys.save()
        self.email.save()
        self.scenarios.save()
        self.app.save() 