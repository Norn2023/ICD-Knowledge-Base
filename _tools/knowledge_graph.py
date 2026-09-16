#!/usr/bin/env python3
"""
Obsidian 知识图谱生成工具
用于生成知识库的可视化图谱
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KnowledgeGraph:
    SKIP_DIRS = {'.obsidian', '.agents', '.claude', '.claudian', '.git', '__pycache__'}

    def _should_skip(self, path: Path) -> bool:
        for part in path.parts:
            if part in self.SKIP_DIRS:
                return True
        return False

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.nodes: Dict[str, Dict] = {}
        self.edges: List[Dict] = []
        self.link_pattern = re.compile(r'\[\[([^\]]+)\]\]')
        self.tag_pattern = re.compile(r'#([a-zA-Z0-9_-]+)')
        
    def scan_vault(self):
        """扫描 vault 构建知识图谱"""
        logger.info("扫描 vault 构建知识图谱...")
        
        # 扫描所有文件
        for md_file in self.vault_path.rglob("*.md"):
            if self._should_skip(md_file):
                continue
                
            file_id = str(md_file.relative_to(self.vault_path))
            self._add_node(file_id, {
                'type': 'file',
                'name': md_file.stem,
                'path': file_id
            })
            
            # 读取文件内容
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # 提取 frontmatter
                self._extract_frontmatter(file_id, content)
                
                # 提取链接
                self._extract_links(file_id, content)
                
                # 提取标签
                self._extract_tags(file_id, content)
                
            except Exception as e:
                logger.error(f"读取文件 {file_id} 时出错: {e}")
                
        # 分析目录结构
        self._analyze_structure()
        
        logger.info(f"图谱构建完成: {len(self.nodes)} 个节点, {len(self.edges)} 条边")
        
    def _add_node(self, node_id: str, properties: Dict):
        """添加节点"""
        if node_id not in self.nodes:
            self.nodes[node_id] = properties
        else:
            self.nodes[node_id].update(properties)
            
    def _add_edge(self, source: str, target: str, edge_type: str, properties: Dict = None):
        """添加边"""
        edge = {
            'source': source,
            'target': target,
            'type': edge_type,
            'properties': properties or {}
        }
        self.edges.append(edge)
        
    def _extract_frontmatter(self, file_id: str, content: str):
        """提取 frontmatter 信息"""
        # 简单的 frontmatter 提取
        if content.startswith('---'):
            try:
                end_idx = content.index('---', 3)
                frontmatter = content[3:end_idx].strip()
                
                # 提取 tags
                tags_match = re.search(r'tags:\s*\n((?:\s*-\s*[^\n]+\n)+)', frontmatter)
                if tags_match:
                    tags = re.findall(r'-\s*([^\n]+)', tags_match.group(1))
                    for tag in tags:
                        self._add_edge(file_id, f"tag:{tag.strip()}", 'has_tag')
                        
            except ValueError:
                pass
                
    def _extract_links(self, file_id: str, content: str):
        """提取链接"""
        links = self.link_pattern.findall(content)
        
        for link in links:
            # 处理带有显示文本的链接（以及表格中的 \| 转义）
            link_normalized = link.replace('\\|', '|')
            if '|' in link_normalized:
                link_path = link_normalized.split('|')[0]
            else:
                link_path = link
                
            # 移除锚点
            if '#' in link_path:
                link_path = link_path.split('#')[0]
                
            if link_path:
                self._add_edge(file_id, link_path, 'links_to')
                
    def _extract_tags(self, file_id: str, content: str):
        """提取标签"""
        tags = self.tag_pattern.findall(content)
        
        for tag in set(tags):
            self._add_edge(file_id, f"tag:{tag}", 'has_tag')
            
    def _analyze_structure(self):
        """分析目录结构"""
        # 按目录分组
        directories = defaultdict(list)
        
        for node_id in self.nodes:
            if node_id.endswith('.md'):
                parts = Path(node_id).parts
                if len(parts) > 1:
                    dir_path = str(Path(*parts[:-1]))
                    directories[dir_path].append(node_id)
                    
        # 创建目录节点和边
        for dir_path, files in directories.items():
            self._add_node(f"dir:{dir_path}", {
                'type': 'directory',
                'name': Path(dir_path).name,
                'path': dir_path
            })
            
            for file_id in files:
                self._add_edge(f"dir:{dir_path}", file_id, 'contains')
                
    def generate_mermaid(self, output_file: str = "knowledge_graph.md"):
        """生成 Mermaid 格式的图谱"""
        logger.info(f"生成 Mermaid 图谱: {output_file}")
        
        # 限制节点数量以保持可读性
        max_nodes = 100
        nodes_to_show = list(self.nodes.keys())[:max_nodes]
        
        # 生成 Mermaid 代码
        mermaid_lines = ["```mermaid", "graph TB"]
        
        # 添加节点
        for node_id in nodes_to_show:
            node = self.nodes[node_id]
            
            if node['type'] == 'file':
                # 文件节点
                label = node['name'][:20] + "..." if len(node['name']) > 20 else node['name']
                mermaid_lines.append(f"    {self._sanitize_id(node_id)}[\"{label}\"]")
                
            elif node['type'] == 'directory':
                # 目录节点
                mermaid_lines.append(f"    {self._sanitize_id(node_id)}[\"📁 {node['name']}\"]")
                
            elif node_id.startswith('tag:'):
                # 标签节点
                tag_name = node_id[4:]
                mermaid_lines.append(f"    {self._sanitize_id(node_id)}[\"🏷️ {tag_name}\"]")
                
        # 添加边
        for edge in self.edges:
            if edge['source'] in nodes_to_show and edge['target'] in nodes_to_show:
                source_id = self._sanitize_id(edge['source'])
                target_id = self._sanitize_id(edge['target'])
                
                if edge['type'] == 'links_to':
                    mermaid_lines.append(f"    {source_id} -->|链接| {target_id}")
                elif edge['type'] == 'has_tag':
                    mermaid_lines.append(f"    {source_id} -->|标签| {target_id}")
                elif edge['type'] == 'contains':
                    mermaid_lines.append(f"    {source_id} -->|包含| {target_id}")
                    
        mermaid_lines.append("```")
        
        # 写入文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# 知识库图谱\n\n")
            f.write("\n".join(mermaid_lines))
            
        logger.info(f"图谱已保存到: {output_file}")
        
    def _sanitize_id(self, node_id: str) -> str:
        """清理节点 ID 用于 Mermaid"""
        # 替换特殊字符
        return re.sub(r'[^a-zA-Z0-9]', '_', node_id)
        
    def generate_statistics(self) -> Dict:
        """生成统计信息"""
        stats = {
            'total_nodes': len(self.nodes),
            'total_edges': len(self.edges),
            'node_types': defaultdict(int),
            'edge_types': defaultdict(int),
            'most_connected_nodes': [],
            'tag_distribution': defaultdict(int),
            'directory_structure': defaultdict(int)
        }
        
        # 统计节点类型
        for node in self.nodes.values():
            stats['node_types'][node['type']] += 1
            
        # 统计边类型
        for edge in self.edges:
            stats['edge_types'][edge['type']] += 1
            
        # 统计标签分布
        for edge in self.edges:
            if edge['type'] == 'has_tag':
                tag = edge['target'][4:]  # 移除 'tag:' 前缀
                stats['tag_distribution'][tag] += 1
                
        # 统计目录结构
        for node_id in self.nodes:
            if node_id.startswith('dir:'):
                dir_path = node_id[4:]
                depth = len(Path(dir_path).parts)
                stats['directory_structure'][f"深度 {depth}"] += 1
                
        # 计算连接最多的节点
        node_connections = defaultdict(int)
        for edge in self.edges:
            node_connections[edge['source']] += 1
            node_connections[edge['target']] += 1
            
        stats['most_connected_nodes'] = sorted(
            node_connections.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        return stats
        
    def export_json(self, output_file: str = "knowledge_graph.json"):
        """导出 JSON 格式的图谱"""
        logger.info(f"导出 JSON 图谱: {output_file}")
        
        graph_data = {
            'nodes': [
                {
                    'id': node_id,
                    **properties
                }
                for node_id, properties in self.nodes.items()
            ],
            'edges': self.edges,
            'statistics': self.generate_statistics()
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(graph_data, f, ensure_ascii=False, indent=2)
            
        logger.info(f"图谱已导出到: {output_file}")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Obsidian 知识图谱生成工具')
    parser.add_argument('--vault-path', default='.', help='Vault 路径')
    parser.add_argument('--output', default='knowledge_graph', help='输出文件名（不含扩展名）')
    parser.add_argument('--format', choices=['mermaid', 'json', 'both'], default='both', help='输出格式')
    
    args = parser.parse_args()
    
    # 初始化图谱生成器
    graph = KnowledgeGraph(args.vault_path)
    
    # 扫描 vault
    graph.scan_vault()
    
    # 生成输出
    if args.format in ['mermaid', 'both']:
        graph.generate_mermaid(f"{args.output}.md")
        
    if args.format in ['json', 'both']:
        graph.export_json(f"{args.output}.json")
        
    # 打印统计信息
    stats = graph.generate_statistics()
    print("\n[结果] 知识库统计:")
    print(f"  节点总数: {stats['total_nodes']}")
    print(f"  边总数: {stats['total_edges']}")
    print(f"  节点类型: {dict(stats['node_types'])}")
    print(f"  边类型: {dict(stats['edge_types'])}")
    print(f"  标签数量: {len(stats['tag_distribution'])}")
    print(f"  最多连接的节点: {stats['most_connected_nodes'][:3]}")

if __name__ == '__main__':
    main()