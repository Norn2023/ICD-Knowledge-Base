#!/usr/bin/env python3
"""
Obsidian 知识库健康检查工具
定期检查知识库的健康状况并提供优化建议
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HealthChecker:
    SKIP_DIRS = {'.obsidian', '.agents', '.claude', '.claudian', '.git', '__pycache__'}

    def _should_skip(self, path: Path) -> bool:
        for part in path.parts:
            if part in self.SKIP_DIRS:
                return True
        return False

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.issues: List[Dict] = []
        self.suggestions: List[Dict] = []
        self.stats: Dict = {}
        
    def run_full_check(self):
        """执行完整健康检查"""
        logger.info("开始知识库健康检查...")
        
        # 1. 基础统计
        self._collect_statistics()
        
        # 2. 文件结构检查
        self._check_file_structure()
        
        # 3. 链接完整性检查
        self._check_link_integrity()
        
        # 4. 内容质量检查
        self._check_content_quality()
        
        # 5. 标签系统检查
        self._check_tag_system()
        
        # 6. 性能优化检查
        self._check_performance()
        
        # 7. 生成报告
        report = self._generate_report()
        
        logger.info("健康检查完成!")
        return report
        
    def _collect_statistics(self):
        """收集基础统计信息"""
        logger.info("收集统计信息...")
        
        files = list(self.vault_path.rglob("*.md"))
        total_size = sum(f.stat().st_size for f in files)
        
        self.stats = {
            'total_files': len(files),
            'total_size_mb': total_size / (1024 * 1024),
            'avg_file_size_kb': (total_size / len(files)) / 1024 if files else 0,
            'file_types': defaultdict(int),
            'directory_depth': defaultdict(int),
            'recent_files': [],
            'large_files': [],
            'small_files': []
        }
        
        # 统计文件类型和大小
        for f in files:
            if self._should_skip(f):
                continue
                
            # 文件类型统计
            ext = f.suffix.lower()
            self.stats['file_types'][ext] += 1
            
            # 目录深度统计
            rel_path = f.relative_to(self.vault_path)
            depth = len(rel_path.parts) - 1
            self.stats['directory_depth'][f"深度 {depth}"] += 1
            
            # 文件大小分类
            size_kb = f.stat().st_size / 1024
            if size_kb < 1:
                self.stats['small_files'].append(str(rel_path))
            elif size_kb > 100:
                self.stats['large_files'].append(str(rel_path))
                
            # 最近修改的文件
            mtime = datetime.fromtimestamp(f.stat().st_mtime)
            if mtime > datetime.now() - timedelta(days=7):
                self.stats['recent_files'].append({
                    'path': str(rel_path),
                    'modified': mtime.isoformat()
                })
                
    def _check_file_structure(self):
        """检查文件结构"""
        logger.info("检查文件结构...")
        
        # 检查必需的目录和文件
        required_dirs = ['ICD10-疾病诊断', 'ICD9-手术操作', 'DRG-分组', 'DIP-病种', '速查手册']
        required_files = ['欢迎.md']
        
        for dir_name in required_dirs:
            if not (self.vault_path / dir_name).exists():
                self.issues.append({
                    'type': 'missing_directory',
                    'severity': 'high',
                    'message': f'缺少必需目录: {dir_name}',
                    'suggestion': f'创建目录: {dir_name}'
                })
                
        for file_name in required_files:
            if not (self.vault_path / file_name).exists():
                self.issues.append({
                    'type': 'missing_file',
                    'severity': 'medium',
                    'message': f'缺少文件: {file_name}',
                    'suggestion': f'创建文件: {file_name}'
                })
                
        # 检查文件命名规范
        for f in self.vault_path.rglob("*.md"):
            if self._should_skip(f):
                continue
                
            name = f.stem
            # 检查是否有特殊字符
            if re.search(r'[<>:"/\\|?*]', name):
                self.issues.append({
                    'type': 'invalid_filename',
                    'severity': 'medium',
                    'message': f'文件名包含特殊字符: {f.name}',
                    'suggestion': f'重命名文件: {f.name}'
                })
                
    def _check_link_integrity(self):
        """检查链接完整性"""
        logger.info("检查链接完整性...")
        
        broken_links = 0
        total_links = 0
        
        for f in self.vault_path.rglob("*.md"):
            if self._should_skip(f):
                continue
                
            try:
                with open(f, 'r', encoding='utf-8') as file:
                    content = file.read()
                    
                # 查找所有 wikilinks
                links = re.findall(r'\[\[([^\]]+)\]\]', content)
                total_links += len(links)
                
                for link in links:
                    # 清理链接
                    link_path = link.split('|')[0].split('#')[0]
                    
                    if link_path and not self._link_exists(link_path):
                        broken_links += 1
                        self.issues.append({
                            'type': 'broken_link',
                            'severity': 'medium',
                            'message': f'断开的链接: [[{link}]] 在文件 {f.name}',
                            'suggestion': f'修复链接: [[{link}]]'
                        })
                        
            except Exception as e:
                logger.error(f"读取文件 {f.name} 时出错: {e}")
                
        self.stats['total_links'] = total_links
        self.stats['broken_links'] = broken_links
        self.stats['link_integrity'] = (total_links - broken_links) / total_links * 100 if total_links > 0 else 100
        
    def _link_exists(self, link_path: str) -> bool:
        """检查链接是否存在"""
        possible_paths = [
            self.vault_path / link_path,
            self.vault_path / (link_path + '.md'),
            self.vault_path / link_path / '_index.md',
        ]
        
        for path in possible_paths:
            if path.exists():
                return True
                
        return False
        
    def _check_content_quality(self):
        """检查内容质量"""
        logger.info("检查内容质量...")
        
        for f in self.vault_path.rglob("*.md"):
            if self._should_skip(f):
                continue
                
            try:
                with open(f, 'r', encoding='utf-8') as file:
                    content = file.read()
                    
                # 检查 frontmatter
                if not content.startswith('---'):
                    self.issues.append({
                        'type': 'missing_frontmatter',
                        'severity': 'low',
                        'message': f'文件缺少 frontmatter: {f.name}',
                        'suggestion': f'为文件添加 frontmatter'
                    })
                    
                # 检查内容长度
                if len(content.strip()) < 100:
                    self.suggestions.append({
                        'type': 'short_content',
                        'message': f'文件内容较短: {f.name} ({len(content)} 字符)',
                        'suggestion': f'考虑扩展内容或合并到其他文件'
                    })
                    
                # 检查是否有孤立的代码块
                if '```' in content:
                    code_blocks = re.findall(r'```(\w*)\n(.*?)```', content, re.DOTALL)
                    for lang, block in code_blocks:
                        if not lang and len(block.strip()) > 100:
                            self.suggestions.append({
                                'type': 'unspecified_language',
                                'message': f'未指定语言的代码块: {f.name}',
                                'suggestion': f'为代码块指定语言以提高可读性'
                            })
                            
            except Exception as e:
                logger.error(f"检查文件 {f.name} 内容时出错: {e}")
                
    def _check_tag_system(self):
        """检查标签系统"""
        logger.info("检查标签系统...")
        
        tag_usage = defaultdict(int)
        
        for f in self.vault_path.rglob("*.md"):
            if self._should_skip(f):
                continue
                
            try:
                with open(f, 'r', encoding='utf-8') as file:
                    content = file.read()
                    
                # 提取标签
                tags = re.findall(r'#([a-zA-Z0-9_-]+)', content)
                for tag in set(tags):
                    tag_usage[tag] += 1
                    
            except Exception as e:
                logger.error(f"检查文件 {f.name} 标签时出错: {e}")
                
        self.stats['tag_usage'] = dict(tag_usage)
        
        # 检查标签规范性
        for tag, count in tag_usage.items():
            if count == 1:
                self.suggestions.append({
                    'type': 'rare_tag',
                    'message': f'罕见标签: #{tag} (仅使用 {count} 次)',
                    'suggestion': f'考虑合并或重命名标签'
                })
                
            if len(tag) > 20:
                self.suggestions.append({
                    'type': 'long_tag',
                    'message': f'过长标签: #{tag} ({len(tag)} 字符)',
                    'suggestion': f'考虑使用更简洁的标签名'
                })
                
    def _check_performance(self):
        """检查性能优化"""
        logger.info("检查性能优化...")
        
        # 检查大文件
        for f in self.vault_path.rglob("*.md"):
            if self._should_skip(f):
                continue
                
            size_kb = f.stat().st_size / 1024
            if size_kb > 500:  # 大于 500KB
                self.suggestions.append({
                    'type': 'large_file',
                    'message': f'大文件: {f.name} ({size_kb:.1f} KB)',
                    'suggestion': f'考虑拆分大文件以提高加载速度'
                })
                
            # 检查文件中的链接数量
            try:
                with open(f, 'r', encoding='utf-8') as file:
                    content = file.read()
                    
                links = re.findall(r'\[\[([^\]]+)\]\]', content)
                if len(links) > 50:
                    self.suggestions.append({
                        'type': 'too_many_links',
                        'message': f'过多链接: {f.name} ({len(links)} 个链接)',
                        'suggestion': f'考虑重构内容以减少链接数量'
                    })
                    
            except Exception as e:
                logger.error(f"检查文件 {f.name} 性能时出错: {e}")
                
    def _generate_report(self) -> Dict:
        """生成健康检查报告"""
        # 计算健康分数
        total_issues = len(self.issues)
        high_severity = len([i for i in self.issues if i['severity'] == 'high'])
        medium_severity = len([i for i in self.issues if i['severity'] == 'medium'])
        low_severity = len([i for i in self.issues if i['severity'] == 'low'])
        
        # 健康分数计算（满分 100）
        health_score = 100
        health_score -= high_severity * 10
        health_score -= medium_severity * 5
        health_score -= low_severity * 2
        health_score -= len(self.suggestions) * 0.5
        
        health_score = max(0, health_score)
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'health_score': round(health_score, 1),
            'statistics': self.stats,
            'issues': {
                'total': total_issues,
                'high_severity': high_severity,
                'medium_severity': medium_severity,
                'low_severity': low_severity,
                'details': self.issues
            },
            'suggestions': {
                'total': len(self.suggestions),
                'details': self.suggestions
            },
            'recommendations': self._generate_recommendations()
        }
        
        return report
        
    def _generate_recommendations(self) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        # 基于问题的建议
        if int(self.stats.get('broken_links', 0)) > 10:
            recommendations.append("修复断开的链接以改善导航体验")
            
        if len(self.stats.get('small_files', [])) > 20:
            recommendations.append("合并小文件以减少文件数量")
            
        if len(self.stats.get('large_files', [])) > 5:
            recommendations.append("拆分大文件以提高加载性能")
            
        # 基于统计的建议
        if self.stats.get('total_files', 0) > 1000:
            recommendations.append("考虑使用文件夹组织来管理大型知识库")
            
        if self.stats.get('avg_file_size_kb', 0) > 50:
            recommendations.append("优化文件大小以提高搜索性能")
            
        # 通用建议
        recommendations.extend([
            "定期备份知识库",
            "使用一致的命名规范",
            "建立清晰的标签体系",
            "维护链接完整性"
        ])
        
        return recommendations

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Obsidian 知识库健康检查工具')
    parser.add_argument('--vault-path', default='.', help='Vault 路径')
    parser.add_argument('--output', default='health_report.json', help='报告输出文件')
    parser.add_argument('--verbose', action='store_true', help='详细输出')
    
    args = parser.parse_args()
    
    # 配置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        
    # 初始化健康检查器
    checker = HealthChecker(args.vault_path)
    
    # 执行完整检查
    report = checker.run_full_check()
    
    # 保存报告
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
        
    # 打印摘要
    summary = (
        "\n" + "="*60 + "\n"
        "[结果] 知识库健康检查报告\n"
        + "="*60 + "\n"
        f"  检查时间: {report['timestamp']}\n"
        f"  健康分数: {report['health_score']}/100\n"
        f"  总文件数: {report['statistics']['total_files']}\n"
        f"  总大小: {report['statistics']['total_size_mb']:.2f} MB\n"
        f"  链接完整性: {report['statistics'].get('link_integrity', 0):.1f}%\n"
        f"  问题数量: {report['issues']['total']} "
        f"(高:{report['issues']['high_severity']} "
        f"中:{report['issues']['medium_severity']} "
        f"低:{report['issues']['low_severity']})\n"
        f"  优化建议: {report['suggestions']['total']}\n"
        "\n主要建议:\n"
    )
    for i, rec in enumerate(report['recommendations'][:5], 1):
        summary += f"  {i}. {rec}\n"
    summary += "="*60 + "\n"
    summary += f"完整报告已保存到: {args.output}\n"
    summary += "="*60
    print(summary)

if __name__ == '__main__':
    main()