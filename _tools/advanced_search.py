#!/usr/bin/env python3
"""
Obsidian 高级搜索工具
提供模糊搜索、语义搜索和高级查询功能
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict
from difflib import SequenceMatcher
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AdvancedSearch:
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.files: Dict[str, Dict] = {}
        self.index: Dict[str, Set[str]] = defaultdict(set)  # 倒排索引
        self.tags: Dict[str, Set[str]] = defaultdict(set)
        self.links: Dict[str, Set[str]] = defaultdict(set)
        
    def build_index(self):
        """构建搜索索引"""
        logger.info("构建搜索索引...")
        
        for md_file in self.vault_path.rglob("*.md"):
            if ".obsidian" in md_file.parts:
                continue
                
            file_id = str(md_file.relative_to(self.vault_path))
            
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # 存储文件信息
                self.files[file_id] = {
                    'path': file_id,
                    'name': md_file.stem,
                    'size': len(content),
                    'content': content,
                    'lines': content.split('\n')
                }
                
                # 构建倒排索引
                self._build_inverted_index(file_id, content)
                
                # 提取标签
                self._extract_tags(file_id, content)
                
                # 提取链接
                self._extract_links(file_id, content)
                
            except Exception as e:
                logger.error(f"索引文件 {file_id} 时出错: {e}")
                
        logger.info(f"索引构建完成: {len(self.files)} 个文件")
        
    def _build_inverted_index(self, file_id: str, content: str):
        """构建倒排索引"""
        # 分词（简单实现）
        words = re.findall(r'[\w\u4e00-\u9fff]+', content.lower())
        
        for word in words:
            if len(word) > 1:  # 忽略单字符
                self.index[word].add(file_id)
                
    def _extract_tags(self, file_id: str, content: str):
        """提取标签"""
        tags = re.findall(r'#([a-zA-Z0-9_-]+)', content)
        
        for tag in set(tags):
            self.tags[tag].add(file_id)
            self.index[tag].add(file_id)  # 标签也加入索引
            
    def _extract_links(self, file_id: str, content: str):
        """提取链接"""
        links = re.findall(r'\[\[([^\]]+)\]\]', content)
        
        for link in links:
            # 清理链接
            clean_link = link.split('|')[0].split('#')[0]
            if clean_link:
                self.links[file_id].add(clean_link)
                self.index[clean_link].add(file_id)
                
    def search(self, query: str, search_type: str = 'fuzzy', limit: int = 20) -> List[Dict]:
        """执行搜索"""
        logger.info(f"执行搜索: {query} (类型: {search_type})")
        
        if search_type == 'exact':
            return self._exact_search(query, limit)
        elif search_type == 'fuzzy':
            return self._fuzzy_search(query, limit)
        elif search_type == 'semantic':
            return self._semantic_search(query, limit)
        elif search_type == 'tag':
            return self._tag_search(query, limit)
        elif search_type == 'link':
            return self._link_search(query, limit)
        elif search_type == 'content':
            return self._content_search(query, limit)
        else:
            return self._fuzzy_search(query, limit)
            
    def _exact_search(self, query: str, limit: int) -> List[Dict]:
        """精确搜索"""
        results = []
        
        # 搜索文件名
        for file_id, file_info in self.files.items():
            if query.lower() in file_info['name'].lower():
                results.append({
                    'file': file_id,
                    'score': 1.0,
                    'match_type': 'filename',
                    'preview': self._get_preview(file_id, query)
                })
                
        # 搜索内容
        for file_id, file_info in self.files.items():
            if query.lower() in file_info['content'].lower():
                score = 0.8
                results.append({
                    'file': file_id,
                    'score': score,
                    'match_type': 'content',
                    'preview': self._get_preview(file_id, query)
                })
                
        return self._rank_results(results)[:limit]
        
    def _fuzzy_search(self, query: str, limit: int) -> List[Dict]:
        """模糊搜索"""
        results = []
        
        for file_id, file_info in self.files.items():
            # 计算与文件名的相似度
            name_similarity = SequenceMatcher(None, query.lower(), file_info['name'].lower()).ratio()
            
            # 计算与内容的相似度
            content_words = re.findall(r'[\w\u4e00-\u9fff]+', file_info['content'].lower())
            query_words = query.lower().split()
            
            content_matches = 0
            for q_word in query_words:
                for c_word in content_words:
                    if SequenceMatcher(None, q_word, c_word).ratio() > 0.7:
                        content_matches += 1
                        break
                        
            content_similarity = content_matches / max(1, len(query_words))
            
            # 综合分数
            score = name_similarity * 0.4 + content_similarity * 0.6
            
            if score > 0.1:  # 阈值
                results.append({
                    'file': file_id,
                    'score': score,
                    'match_type': 'fuzzy',
                    'preview': self._get_preview(file_id, query)
                })
                
        return self._rank_results(results)[:limit]
        
    def _semantic_search(self, query: str, limit: int) -> List[Dict]:
        """语义搜索（基于同义词和相关词）"""
        # 简单的同义词扩展
        synonyms = {
            '心肌梗死': ['心梗', '心脏梗死', '冠心病', '心绞痛'],
            '糖尿病': ['血糖高', '高血糖', '糖代谢异常'],
            '高血压': ['血压高', '高血压病', '血压升高'],
            '肺炎': ['肺部感染', '肺部炎症', '呼吸道感染'],
            '肿瘤': ['癌症', '肿块', '新生物', '恶性肿瘤'],
            '手术': ['外科手术', '手术治疗', '外科治疗']
        }
        
        # 扩展查询词
        expanded_queries = [query]
        for key, values in synonyms.items():
            if query in values or query == key:
                expanded_queries.extend(values)
                expanded_queries.append(key)
                
        # 使用扩展查询搜索
        all_results = []
        for q in set(expanded_queries):
            results = self._fuzzy_search(q, limit)
            all_results.extend(results)
            
        return self._rank_results(all_results)[:limit]
        
    def _tag_search(self, tag: str, limit: int) -> List[Dict]:
        """标签搜索"""
        results = []
        
        # 移除 # 前缀
        clean_tag = tag.lstrip('#')
        
        # 搜索标签
        for file_id in self.tags.get(clean_tag, set()):
            results.append({
                'file': file_id,
                'score': 1.0,
                'match_type': 'tag',
                'preview': self._get_preview(file_id, f"#{clean_tag}")
            })
            
        return self._rank_results(results)[:limit]
        
    def _link_search(self, link: str, limit: int) -> List[Dict]:
        """链接搜索"""
        results = []
        
        # 搜索链接到指定文件的文件
        for file_id, file_links in self.links.items():
            if link in file_links:
                results.append({
                    'file': file_id,
                    'score': 0.9,
                    'match_type': 'link',
                    'preview': self._get_preview(file_id, f"[[{link}]]")
                })
                
        return self._rank_results(results)[:limit]
        
    def _content_search(self, query: str, limit: int) -> List[Dict]:
        """内容搜索（支持正则表达式）"""
        results = []
        
        try:
            pattern = re.compile(query, re.IGNORECASE)
            
            for file_id, file_info in self.files.items():
                matches = pattern.findall(file_info['content'])
                if matches:
                    score = min(1.0, len(matches) * 0.2)
                    results.append({
                        'file': file_id,
                        'score': score,
                        'match_type': 'content_regex',
                        'preview': self._get_preview(file_id, query),
                        'match_count': len(matches)
                    })
                    
        except re.error:
            # 如果正则表达式无效，使用普通搜索
            return self._exact_search(query, limit)
            
        return self._rank_results(results)[:limit]
        
    def _rank_results(self, results: List[Dict]) -> List[Dict]:
        """对结果排序"""
        # 去重
        seen = set()
        unique_results = []
        
        for result in results:
            if result['file'] not in seen:
                seen.add(result['file'])
                unique_results.append(result)
                
        # 按分数排序
        return sorted(unique_results, key=lambda x: x['score'], reverse=True)
        
    def _get_preview(self, file_id: str, query: str, context_chars: int = 100) -> str:
        """获取搜索结果预览"""
        if file_id not in self.files:
            return ""
            
        content = self.files[file_id]['content']
        
        # 查找查询词位置
        pos = content.lower().find(query.lower())
        
        if pos == -1:
            # 如果找不到，返回开头
            return content[:context_chars] + "..." if len(content) > context_chars else content
            
        # 获取上下文
        start = max(0, pos - context_chars // 2)
        end = min(len(content), pos + len(query) + context_chars // 2)
        
        preview = content[start:end]
        
        # 添加省略号
        if start > 0:
            preview = "..." + preview
        if end < len(content):
            preview = preview + "..."
            
        return preview
        
    def advanced_query(self, query_params: Dict) -> List[Dict]:
        """高级查询"""
        results = []
        
        # 支持的查询参数
        file_pattern = query_params.get('file', None)
        content_pattern = query_params.get('content', None)
        tag_pattern = query_params.get('tag', None)
        link_pattern = query_params.get('link', None)
        min_size = query_params.get('min_size', 0)
        max_size = query_params.get('max_size', float('inf'))
        
        # 过滤文件
        for file_id, file_info in self.files.items():
            score = 0
            match_reasons = []
            
            # 检查文件名
            if file_pattern and re.search(file_pattern, file_info['name'], re.IGNORECASE):
                score += 0.3
                match_reasons.append('filename')
                
            # 检查内容
            if content_pattern and re.search(content_pattern, file_info['content'], re.IGNORECASE):
                score += 0.5
                match_reasons.append('content')
                
            # 检查标签
            if tag_pattern:
                clean_tag = tag_pattern.lstrip('#')
                if clean_tag in self.tags and file_id in self.tags[clean_tag]:
                    score += 0.4
                    match_reasons.append('tag')
                    
            # 检查链接
            if link_pattern:
                if file_id in self.links and link_pattern in self.links[file_id]:
                    score += 0.4
                    match_reasons.append('link')
                    
            # 检查文件大小
            if file_info['size'] < min_size or file_info['size'] > max_size:
                continue
                
            if score > 0:
                results.append({
                    'file': file_id,
                    'score': score,
                    'match_type': 'advanced',
                    'match_reasons': match_reasons,
                    'preview': self._get_preview(file_id, content_pattern or file_pattern or '')
                })
                
        return self._rank_results(results)
        
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        stats = {
            'total_files': len(self.files),
            'total_tags': len(self.tags),
            'total_indexed_words': len(self.index),
            'tag_distribution': {tag: len(files) for tag, files in self.tags.items()},
            'file_size_distribution': {
                'small (<1KB)': 0,
                'medium (1KB-10KB)': 0,
                'large (>10KB)': 0
            }
        }
        
        # 文件大小分布
        for file_info in self.files.values():
            size_kb = file_info['size'] / 1024
            if size_kb < 1:
                stats['file_size_distribution']['small (<1KB)'] += 1
            elif size_kb < 10:
                stats['file_size_distribution']['medium (1KB-10KB)'] += 1
            else:
                stats['file_size_distribution']['large (>10KB)'] += 1
                
        return stats

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Obsidian 高级搜索工具')
    parser.add_argument('--vault-path', default='.', help='Vault 路径')
    parser.add_argument('--query', required=True, help='搜索查询')
    parser.add_argument('--type', choices=['exact', 'fuzzy', 'semantic', 'tag', 'link', 'content'], 
                       default='fuzzy', help='搜索类型')
    parser.add_argument('--limit', type=int, default=20, help='结果数量限制')
    parser.add_argument('--output', help='输出文件')
    parser.add_argument('--stats', action='store_true', help='显示统计信息')
    
    args = parser.parse_args()
    
    # 初始化搜索工具
    search = AdvancedSearch(args.vault_path)
    
    # 构建索引
    search.build_index()
    
    # 显示统计信息
    if args.stats:
        stats = search.get_statistics()
        print("\n📊 搜索索引统计:")
        print(f"  总文件数: {stats['total_files']}")
        print(f"  总标签数: {stats['total_tags']}")
        print(f"  索引词数: {stats['total_indexed_words']}")
        print(f"  文件大小分布: {stats['file_size_distribution']}")
        return
        
    # 执行搜索
    results = search.search(args.query, args.type, args.limit)
    
    # 输出结果
    print(f"\n🔍 搜索结果: '{args.query}' (类型: {args.type})")
    print(f"找到 {len(results)} 个结果:\n")
    
    for i, result in enumerate(results, 1):
        print(f"{i}. 📄 {result['file']}")
        print(f"   分数: {result['score']:.2f} | 匹配类型: {result['match_type']}")
        print(f"   预览: {result['preview'][:100]}...")
        print()
        
    # 保存结果
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"结果已保存到: {args.output}")

if __name__ == '__main__':
    main()