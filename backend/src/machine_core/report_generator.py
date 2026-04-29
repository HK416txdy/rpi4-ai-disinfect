"""
报告生成器模块
生成消毒报告和分析文档
"""
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import json


class ReportGenerator:
    """消毒报告生成器"""
    
    def __init__(self, report_dir: Optional[Path] = None):
        self.report_dir = report_dir or Path(__file__).parent.parent.parent / 'reports'
        self.report_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_disinfection_report(
        self,
        machine_id: int,
        machine_name: str,
        disinfection_params: Dict[str, Any],
        detection_result: Dict[str, Any],
        timestamp: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """生成单次消毒报告"""
        
        timestamp = timestamp or datetime.now()
        
        report = {
            'report_id': f'RPT_{machine_id}_{timestamp.strftime("%Y%m%d_%H%M%S")}',
            'machine_id': machine_id,
            'machine_name': machine_name,
            'timestamp': timestamp.isoformat(),
            
            # 检测信息
            'detection': {
                'pollution_grayscale': detection_result.get('mean_grayscale', 0),
                'stain_count': detection_result.get('stain_count', 0),
                'pollution_level': detection_result.get('pollution_level', 0),
                'severity_description': detection_result.get('severity_description', '')
            },
            
            # 消毒参数
            'disinfection': disinfection_params,
            
            # 报告摘要
            'summary': self._generate_summary(machine_name, disinfection_params, detection_result)
        }
        
        # 保存报告
        self._save_report(report)
        
        return report
    
    def generate_machine_summary_report(
        self,
        machine_id: int,
        machine_name: str,
        statistics: Dict[str, Any],
        recent_records: Optional[List] = None
    ) -> Dict[str, Any]:
        """生成机器汇总报告"""
        
        report = {
            'report_type': 'machine_summary',
            'machine_id': machine_id,
            'machine_name': machine_name,
            'generated_at': datetime.now().isoformat(),
            
            # 统计数据
            'statistics': statistics,
            
            # 最近记录（如果有）
            'recent_records': recent_records[:10] if recent_records else [],
            
            # 分析建议
            'recommendations': self._generate_recommendations(statistics)
        }
        
        # 保存报告
        self._save_report(report)
        
        return report
    
    def generate_llm_report_prompt(
        self,
        machine_id: int,
        machine_name: str,
        location: str,
        status: str,
        enabled: bool,
        disinfected_count: int,
        runtime_hours: float,
        statistics: Dict[str, Any]
    ) -> str:
        """生成用于大模型分析的提示词"""
        
        prompt = f"""你是一位专业的消毒设备维护分析师。请根据以下消毒机数据生成一份详细的设备运行报告。

## 设备基本信息
- 设备名称: {machine_name}
- 设备ID: {machine_id}
- 安装位置: {location}
- 当前状态: {status}
- 运行状态: {'已启用' if enabled else '未启用'}
- 累计消毒次数: {disinfected_count}
- 累计运行时长: {runtime_hours:.2f} 小时

## 运行统计数据
- 平均节能率: {statistics.get('avg_energy_saving', 0):.2f}%
- 平均灭菌率: {statistics.get('avg_sterilization_rate', 0):.4f}%
- 总运行时长: {statistics.get('total_runtime_hours', 0):.2f} 小时

## 报告要求
请生成一份包含以下内容的报告：

1. **设备概况总结** - 简要描述设备的整体运行情况
2. **运行效率分析** - 基于消毒次数和运行时间分析设备效率
3. **状态评估** - 评估当前设备状态，是否存在潜在问题
4. **维护建议** - 提供具体的维护和保养建议
5. **寿命预测** - 基于运行数据预测设备剩余使用寿命
6. **优化建议** - 如何提高设备使用效率的建议

请用专业的语气撰写，报告要简洁明了，突出重点。使用Markdown格式输出。
"""
        
        return prompt
    
    def _generate_summary(
        self,
        machine_name: str,
        disinfection_params: Dict[str, Any],
        detection_result: Dict[str, Any]
    ) -> str:
        """生成报告摘要"""
        
        pollution_level = detection_result.get('pollution_level', 0)
        mode_name = disinfection_params.get('mode_name', '')
        energy_saving = disinfection_params.get('energy_saving_rate', 0)
        sterilization = disinfection_params.get('sterilization_rate', 0) * 100
        
        summary = (
            f"消毒机 {machine_name} 完成一次消毒作业。\n"
            f"污染等级: {pollution_level}级\n"
            f"消毒模式: {mode_name}\n"
            f"节能率: {energy_saving}%\n"
            f"灭菌率: {sterilization:.4f}%"
        )
        
        return summary
    
    def _generate_recommendations(self, statistics: Dict[str, Any]) -> List[str]:
        """生成维护建议"""
        recommendations = []
        
        total_disinfections = statistics.get('total_disinfections', 0)
        avg_energy_saving = statistics.get('avg_energy_saving', 0)
        runtime_hours = statistics.get('total_runtime_hours', 0)
        
        # 基于消毒次数的建议
        if total_disinfections > 1000:
            recommendations.append("设备已运行超过1000次，建议进行全面检查和维护")
        
        # 基于节能率的建议
        if avg_energy_saving < 20:
            recommendations.append("节能率较低，建议优化消毒参数或检查设备状态")
        elif avg_energy_saving > 40:
            recommendations.append("节能率优秀，继续保持当前运行策略")
        
        # 基于运行时长的建议
        if runtime_hours > 500:
            recommendations.append("设备累计运行超过500小时，建议进行深度保养")
        
        if not recommendations:
            recommendations.append("设备运行正常，按照常规维护计划执行即可")
        
        return recommendations
    
    def _save_report(self, report: Dict[str, Any]):
        """保存报告到文件"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_id = report.get('report_id', f'report_{timestamp}')
        
        report_file = self.report_dir / f'{report_id}.json'
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"📄 报告已保存: {report_file}")
    
    def load_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        """加载报告"""
        report_file = self.report_dir / f'{report_id}.json'
        
        if not report_file.exists():
            return None
        
        try:
            with open(report_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ 加载报告失败: {e}")
            return None
    
    def list_reports(self, machine_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """列出报告"""
        reports = []
        
        for report_file in sorted(self.report_dir.glob('*.json')):
            try:
                with open(report_file, 'r', encoding='utf-8') as f:
                    report = json.load(f)
                    
                    # 如果指定了machine_id，过滤报告
                    if machine_id is None or report.get('machine_id') == machine_id:
                        reports.append({
                            'report_id': report.get('report_id', ''),
                            'timestamp': report.get('timestamp', ''),
                            'report_type': report.get('report_type', 'disinfection')
                        })
            except Exception as e:
                print(f"❌ 读取报告失败 {report_file}: {e}")
        
        return reports
