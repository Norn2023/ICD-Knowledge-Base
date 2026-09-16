#!/usr/bin/env python3
"""
Obsidian 链接检查和修复工具 v2.0
修复: 正确处理Markdown表格中的转义管道符 \|、忽略非vault目录
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 需要跳过的目录（非 vault 内容）
SKIP_DIRS = {'.obsidian', '.agents', '.claude', '.claudian', '.git', '__pycache__'}

class LinkChecker:
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path).resolve()
        self.broken_links: List[Dict] = []
        self.valid_links: List[Dict] = []
        self.all_files: Set[str] = set()
        # 匹配 [[...]]，但排除其中的 \| 被误识别
        self.link_pattern = re.compile(r'\[\[([^\]]+)\]\]')
        
    def _should_skip(self, path: Path) -> bool:
        """判断文件是否在需要跳过的目录中"""
        for part in path.parts:
            if part in SKIP_DIRS:
                return True
        return False

    def scan_files(self):
        """扫描所有 Markdown 文件"""
        logger.info("扫描 vault 中的文件...")
        
        for md_file in self.vault_path.rglob("*.md"):
            if self._should_skip(md_file):
                continue
                
            relative_path = md_file.relative_to(self.vault_path)
            self.all_files.add(str(relative_path))
            
        logger.info(f"找到 {len(self.all_files)} 个 Markdown 文件（已排除配置目录）")

    def _parse_link_path(self, link: str) -> str:
        """
        从 wiki-link 中提取真实路径。
        处理:
          - [[path]] -> path
          - [[path|display]] -> path（| 为分隔符）
          - [[path\|display]] -> path（\| 是表格中转义的 |，Obsidian 视同 |）
          - [[path#anchor]] -> path
          - [[—]] 模板占位符 -> 返回空字符串
        """
        # 模板占位符
        if link.strip() == '—':
            return ''
        
        # 先处理 \| 为表格中转义的 |（Obsidian 将其视同普通分隔符 |）
        # 把 \| 统一替换为 | 以便统一分割
        normalized = link.replace('\\|', '|')
        
        # 按 | 分割，取第一部分作为路径
        parts = normalized.split('|', maxsplit=1)
        link_path = parts[0]
        
        # 移除锚点 #anchor
        if '#' in link_path:
            link_path = link_path.split('#')[0]
            
        return link_path.strip()

    def _file_exists(self, link_path: str) -> bool:
        """检查链接目标文件是否存在"""
        # 空路径视为有效（如模板占位符）
        if not link_path:
            return True
            
        # 尝试多种路径解析方式
        possible_paths = [
            self.vault_path / link_path,          # 直接路径
            self.vault_path / (link_path + '.md'), # + .md 后缀
            self.vault_path / link_path / '_index.md',  # 目录下的 _index.md
        ]
        
        for path in possible_paths:
            if path.exists():
                return True
                
        # 在文件列表中模糊匹配（处理路径分隔符差异）
        norm_link = link_path.replace('\\', '/').lower()
        for existing_file in self.all_files:
            norm_existing = existing_file.replace('\\', '/').lower()
            # 去掉 .md 比较
            if norm_existing == norm_link or norm_existing == norm_link + '.md':
                return True
            # 检查 _index.md
            if norm_existing == norm_link + '/_index.md':
                return True
                
        return False

    def check_links(self):
        """检查所有链接"""
        logger.info("检查链接完整性...")
        
        for file_path in self.all_files:
            full_path = self.vault_path / file_path
            
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # 查找所有 wikilinks
                links = self.link_pattern.findall(content)
                
                for link in links:
                    link_path = self._parse_link_path(link)
                    
                    if not link_path:
                        continue  # 模板占位符，跳过
                        
                    if not self._file_exists(link_path):
                        self.broken_links.append({
                            'source_file': file_path,
                            'broken_link': link,
                            'expected_path': link_path
                        })
                    else:
                        self.valid_links.append({
                            'source_file': file_path,
                            'valid_link': link,
                            'target_path': link_path
                        })
                        
            except Exception as e:
                logger.error(f"读取文件 {file_path} 时出错: {e}")
                
    def generate_report(self) -> Dict:
        """生成检查报告"""
        total = len(self.valid_links) + len(self.broken_links)
        report = {
            'total_files': len(self.all_files),
            'total_links_checked': total,
            'valid_links': len(self.valid_links),
            'broken_links': len(self.broken_links),
            'broken_links_details': self.broken_links,
            'success_rate': len(self.valid_links) / max(1, total) * 100
        }
        return report

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Obsidian 链接检查和修复工具 v2.0')
    parser.add_argument('--vault-path', default='.', help='Vault 路径')
    parser.add_argument('--output', default='link_check_report.json', help='报告输出文件')
    parser.add_argument('--no-save', action='store_true', help='不保存报告文件，只打印到控制台')
    
    args = parser.parse_args()
    
    checker = LinkChecker(args.vault_path)
    checker.scan_files()
    checker.check_links()
    
    report = checker.generate_report()
    
    if not args.no_save:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        logger.info(f"报告已保存到: {args.output}")
    
    print(f"\n{'='*60}")
    print(f"[结果] 链接检查完成")
    print(f"{'='*60}")
    print(f"  总文件数: {report['total_files']}")
    print(f"  总链接数: {report['total_links_checked']}")
    print(f"  有效链接: {report['valid_links']}")
    print(f"  断开链接: {report['broken_links']}")
    print(f"  成功率: {report['success_rate']:.1f}%")
    
    if report['broken_links'] > 0:
        print(f"\n[警告] 断开的链接详情:")
        for bl in report['broken_links_details']:
            source = bl['source_file']
            b_link = bl['broken_link']
            print(f"  - 文件: {source}")
            print(f"    链接: [[{b_link}]]")
            print()
    else:
        print(f"\n[信息] 所有链接正常！")
    
    print(f"{'='*60}")

if __name__ == '__main__':
    main()
