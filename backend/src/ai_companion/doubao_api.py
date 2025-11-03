"""
豆包大模型API集成
用于高级AI分析学习内容和摄像头画面
"""

import requests
import base64
from typing import Dict, List, Optional
import json


class DoubaoAPI:
    """豆包大模型API客户端"""

    def __init__(self, api_key: str):
        """
        初始化豆包API客户端

        Args:
            api_key: API密钥
        """
        self.api_key = api_key
        self.base_url = "https://ark.cn-beijing.volces.com/api/v3"
        self.model = "doubao-seed-1-6-251015"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

    def analyze_image(self, image_data: str, question: str,
                     reasoning_effort: str = "medium") -> Dict:
        """
        分析图片内容

        Args:
            image_data: Base64编码的图片数据或图片URL
            question: 要问的问题
            reasoning_effort: 推理强度 (low, medium, high)

        Returns:
            API响应字典
        """
        # 判断是URL还是Base64数据
        if image_data.startswith('http'):
            image_url = image_data
        else:
            # 如果是Base64，确保格式正确
            if ',' in image_data:
                image_url = image_data
            else:
                image_url = f"data:image/jpeg;base64,{image_data}"

        payload = {
            "model": self.model,
            "max_completion_tokens": 65535,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url
                            }
                        },
                        {
                            "type": "text",
                            "text": question
                        }
                    ]
                }
            ],
            "reasoning_effort": reasoning_effort
        }

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                "error": str(e),
                "success": False
            }

    def analyze_learning_content(self, image_data: str) -> Dict:
        """
        分析学习内容
        识别学生正在学习的具体内容、难度、学科等

        Args:
            image_data: 摄像头捕获的Base64图片数据

        Returns:
            分析结果
        """
        question = """请详细分析这张学习场景图片：
1. 学生正在学习什么学科和具体内容？
2. 识别书本、笔记或屏幕上的文字内容
3. 判断学习内容的难度级别（小学/初中/高中/大学）
4. 识别当前正在处理的具体问题或概念
5. 评估学习材料的类型（教材/练习册/笔记/电子设备等）

请用JSON格式返回结果，包含：subject（学科）、topic（具体主题）、difficulty（难度）、content_type（内容类型）、detected_text（识别的文字）、learning_stage（学习阶段：预习/学习/练习/复习）"""

        result = self.analyze_image(image_data, question, reasoning_effort="high")

        if "error" in result:
            return result

        try:
            # 提取AI的回答
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                return {
                    "success": True,
                    "analysis": content,
                    "raw_response": result
                }
            else:
                return {
                    "success": False,
                    "error": "无法解析响应"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"处理响应失败: {str(e)}"
            }

    def analyze_posture_and_state(self, image_data: str) -> Dict:
        """
        分析学习姿势和状态

        Args:
            image_data: 摄像头捕获的Base64图片数据

        Returns:
            姿势和状态分析结果
        """
        question = """请分析学生的学习状态：
1. 坐姿是否正确？（距离书本/屏幕的距离，头部角度，背部姿势）
2. 精神状态如何？（专注/疲劳/困惑/分心）
3. 是否有不良学习习惯？（托腮/趴着/距离过近等）
4. 情绪状态？（积极/沮丧/焦虑/平静）
5. 是否在认真学习还是在做其他事情？

请用JSON格式返回，包含：posture_score（姿势评分0-100）、attention_level（专注度0-100）、emotional_state（情绪状态）、suggestions（改进建议）"""

        result = self.analyze_image(image_data, question, reasoning_effort="medium")

        if "error" in result:
            return result

        try:
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                return {
                    "success": True,
                    "analysis": content,
                    "raw_response": result
                }
            else:
                return {
                    "success": False,
                    "error": "无法解析响应"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"处理响应失败: {str(e)}"
            }

    def generate_learning_summary(self, session_data: Dict) -> Dict:
        """
        生成学习总结
        根据整个学习会话的数据生成详细总结

        Args:
            session_data: 包含学习会话信息的字典
                - duration: 学习时长
                - topics: 学习的主题列表
                - focus_level: 平均专注度
                - posture_scores: 姿势评分列表
                - detected_content: 识别到的学习内容

        Returns:
            学习总结
        """
        # 构建提示
        prompt = f"""请根据以下学习数据生成详细的学习总结报告：

学习时长: {session_data.get('duration', 0)} 分钟
学习主题: {', '.join(session_data.get('topics', ['未识别']))}
平均专注度: {session_data.get('focus_level', 0)}%
平均姿势评分: {sum(session_data.get('posture_scores', [0])) / max(len(session_data.get('posture_scores', [1])), 1):.1f}
学习内容: {session_data.get('detected_content', '未识别')}

请生成包含以下内容的学习总结：
1. 学习效果评估（优秀/良好/一般/需改进）
2. 专注度分析和改进建议
3. 学习姿势健康提醒
4. 学习内容掌握情况推测
5. 下次学习的具体建议
6. 鼓励和激励的话语

请用友好、鼓励的语气，像一个关心学生的AI伙伴。"""

        payload = {
            "model": self.model,
            "max_completion_tokens": 65535,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "reasoning_effort": "medium"
        }

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()

            if "choices" in result and len(result["choices"]) > 0:
                summary = result["choices"][0]["message"]["content"]
                return {
                    "success": True,
                    "summary": summary,
                    "raw_response": result
                }
            else:
                return {
                    "success": False,
                    "error": "无法生成总结"
                }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e)
            }

    def chat(self, message: str, history: List[Dict] = None) -> Dict:
        """
        对话功能

        Args:
            message: 用户消息
            history: 对话历史 [{"role": "user", "content": "..."}, ...]

        Returns:
            AI回复
        """
        messages = history or []
        messages.append({
            "role": "user",
            "content": message
        })

        payload = {
            "model": self.model,
            "max_completion_tokens": 65535,
            "messages": messages,
            "reasoning_effort": "medium"
        }

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()

            if "choices" in result and len(result["choices"]) > 0:
                reply = result["choices"][0]["message"]["content"]
                return {
                    "success": True,
                    "reply": reply,
                    "raw_response": result
                }
            else:
                return {
                    "success": False,
                    "error": "无法获取回复"
                }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e)
            }


# 全局实例（使用环境变量或配置文件中的API密钥）
# 用户可以替换为自己的API密钥
DEFAULT_API_KEY = "d0f9bb92-cfa9-4261-912c-621c3fc6d509"
doubao_client = DoubaoAPI(DEFAULT_API_KEY)


if __name__ == "__main__":
    print("=" * 60)
    print("豆包大模型API测试")
    print("=" * 60)

    # 测试文本对话
    result = doubao_client.chat("你好，请介绍一下你自己")
    if result.get("success"):
        print(f"✓ 对话成功: {result['reply'][:100]}...")
    else:
        print(f"✗ 对话失败: {result.get('error')}")

    print("\n豆包API模块就绪！")
