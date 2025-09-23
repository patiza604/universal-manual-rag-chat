# training/scripts/validation_report.py
import os
import json
import pickle
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, Counter
import matplotlib.pyplot as plt
# import seaborn as sns
from datetime import datetime
# import pandas as pd

# Add project root to path
import sys
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

class ValidationReportGenerator:
    """Generate comprehensive validation reports for enhanced chunking pipeline"""
    
    def __init__(self, 
                 jsonl_file: Optional[str] = None,
                 vector_dir: Optional[str] = None,
                 output_dir: str = "training/output/reports"):
        
        self.jsonl_file = Path(jsonl_file) if jsonl_file else None
        self.vector_dir = Path(vector_dir) if vector_dir else None
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Report data
        self.chunks_data = []
        self.vector_stats = {}
        self.validation_results = {}
        
        # Report files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.report_file = self.output_dir / f"validation_report_{timestamp}.html"
        self.summary_file = self.output_dir / f"validation_summary_{timestamp}.json"
        self.charts_dir = self.output_dir / f"charts_{timestamp}"
        self.charts_dir.mkdir(exist_ok=True)
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report"""
        
        print("📊 Generating comprehensive validation report...")
        
        # Load data
        if self.jsonl_file:
            self._load_jsonl_data()
        
        if self.vector_dir:
            self._load_vector_data()
        
        if not self.chunks_data and not self.vector_stats:
            raise ValueError("No data loaded. Provide either JSONL file or vector directory.")
        
        # Run validation analyses
        self._validate_chunk_quality()
        self._validate_content_distribution()
        self._validate_classification_accuracy()
        self._validate_group_structure()
        self._validate_metadata_completeness()
        self._analyze_token_efficiency()
        self._check_embedding_quality()
        
        # Generate visualizations
        self._generate_charts()
        
        # Create HTML report
        self._generate_html_report()
        
        # Save summary
        self._save_summary()
        
        print(f"✅ Comprehensive report generated: {self.report_file}")
        
        return self.validation_results
    
    def _load_jsonl_data(self):
        """Load data from JSONL file"""
        
        print(f"📥 Loading JSONL data from {self.jsonl_file}")
        
        if not self.jsonl_file.exists():
            print(f"⚠️ JSONL file not found: {self.jsonl_file}")
            return
        
        with open(self.jsonl_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    chunk = json.loads(line)
                    self.chunks_data.append(chunk)
                except json.JSONDecodeError as e:
                    print(f"⚠️ JSON error at line {line_num}: {e}")
                    continue
        
        print(f"✅ Loaded {len(self.chunks_data)} chunks from JSONL")
    
    def _load_vector_data(self):
        """Load data from vector directory"""
        
        print(f"📥 Loading vector data from {self.vector_dir}")
        
        if not self.vector_dir.exists():
            print(f"⚠️ Vector directory not found: {self.vector_dir}")
            return
        
        # Load vector statistics if available
        stats_file = self.vector_dir / "vector_stats_enhanced.json"
        if stats_file.exists():
            with open(stats_file, 'r', encoding='utf-8') as f:
                self.vector_stats = json.load(f)
            print(f"✅ Loaded vector statistics")
        
        # Load metadata if available
        metadata_file = self.vector_dir / "metadata_enhanced.pkl"
        if metadata_file.exists():
            with open(metadata_file, 'rb') as f:
                metadata_list = pickle.load(f)
            
            # Convert metadata to chunks format for analysis
            for i, metadata in enumerate(metadata_list):
                chunk = {
                    'id': metadata.get('id', f'chunk_{i}'),
                    'content': metadata.get('content_preview', ''),
                    'metadata': metadata
                }
                self.chunks_data.append(chunk)
            
            print(f"✅ Loaded {len(metadata_list)} chunks from vector metadata")
    
    def _validate_chunk_quality(self):
        """Validate overall chunk quality"""
        
        print("🔍 Validating chunk quality...")
        
        if not self.chunks_data:
            return
        
        quality_metrics = {
            'total_chunks': len(self.chunks_data),
            'empty_content': 0,
            'very_short_content': 0,
            'very_long_content': 0,
            'missing_embeddings': 0,
            'invalid_metadata': 0,
            'completeness_scores': [],
            'token_efficiencies': [],
            'quality_flags': defaultdict(int),
            'needs_review_count': 0
        }
        
        for chunk in self.chunks_data:
            content = chunk.get('content', '').strip()
            metadata = chunk.get('metadata', {})
            
            # Content validation
            if not content:
                quality_metrics['empty_content'] += 1
            elif len(content) < 50:
                quality_metrics['very_short_content'] += 1
            elif len(content) > 8000:
                quality_metrics['very_long_content'] += 1
            
            # Embedding validation
            embedding = chunk.get('embedding')
            if not embedding or not isinstance(embedding, list):
                quality_metrics['missing_embeddings'] += 1
            
            # Metadata validation
            if not isinstance(metadata, dict):
                quality_metrics['invalid_metadata'] += 1
                continue
            
            # Quality metrics
            completeness = metadata.get('completeness_score', 0.0)
            if isinstance(completeness, (int, float)):
                quality_metrics['completeness_scores'].append(float(completeness))
            
            efficiency = metadata.get('token_efficiency', 0.0)
            if isinstance(efficiency, (int, float)):
                quality_metrics['token_efficiencies'].append(float(efficiency))
            
            quality_flag = metadata.get('quality_flag', 'unknown')
            quality_metrics['quality_flags'][quality_flag] += 1
            
            if metadata.get('needs_review', False):
                quality_metrics['needs_review_count'] += 1
        
        # Calculate statistics
        if quality_metrics['completeness_scores']:
            quality_metrics['avg_completeness'] = np.mean(quality_metrics['completeness_scores'])
            quality_metrics['median_completeness'] = np.median(quality_metrics['completeness_scores'])
            quality_metrics['std_completeness'] = np.std(quality_metrics['completeness_scores'])
        
        if quality_metrics['token_efficiencies']:
            quality_metrics['avg_token_efficiency'] = np.mean(quality_metrics['token_efficiencies'])
            quality_metrics['median_token_efficiency'] = np.median(quality_metrics['token_efficiencies'])
            quality_metrics['std_token_efficiency'] = np.std(quality_metrics['token_efficiencies'])
        
        # Calculate quality score
        total = quality_metrics['total_chunks']
        if total > 0:
            issues = (quality_metrics['empty_content'] + 
                     quality_metrics['very_short_content'] + 
                     quality_metrics['missing_embeddings'] + 
                     quality_metrics['invalid_metadata'])
            quality_metrics['overall_quality_score'] = max(0, (total - issues) / total * 100)
        
        self.validation_results['chunk_quality'] = quality_metrics
    
    def _validate_content_distribution(self):
        """Validate content type and role distribution"""
        
        print("📊 Validating content distribution...")
        
        distribution_metrics = {
            'content_types': defaultdict(int),
            'semantic_roles': defaultdict(int),
            'levels': defaultdict(int),
            'sections': defaultdict(int),
            'languages': defaultdict(int),
            'source_types': defaultdict(int)
        }
        
        for chunk in self.chunks_data:
            metadata = chunk.get('metadata', {})
            
            distribution_metrics['content_types'][metadata.get('content_type', 'unknown')] += 1
            distribution_metrics['semantic_roles'][metadata.get('semantic_role', 'unknown')] += 1
            distribution_metrics['levels'][metadata.get('level', 'unknown')] += 1
            distribution_metrics['sections'][metadata.get('section_id', 'unknown')] += 1
            distribution_metrics['languages'][metadata.get('language', 'unknown')] += 1
            distribution_metrics['source_types'][metadata.get('source_type', 'unknown')] += 1
        
        # Convert to regular dicts
        for key in distribution_metrics:
            distribution_metrics[key] = dict(distribution_metrics[key])
        
        # Calculate diversity metrics
        total_chunks = len(self.chunks_data)
        if total_chunks > 0:
            distribution_metrics['content_type_diversity'] = len(distribution_metrics['content_types'])
            distribution_metrics['semantic_role_diversity'] = len(distribution_metrics['semantic_roles'])
            distribution_metrics['section_diversity'] = len(distribution_metrics['sections'])
        
        self.validation_results['content_distribution'] = distribution_metrics
    
    def _validate_classification_accuracy(self):
        """Validate classification method accuracy and confidence"""
        
        print("🧠 Validating classification accuracy...")
        
        classification_metrics = {
            'methods': defaultdict(int),
            'confidence_scores': [],
            'low_confidence_chunks': 0,
            'method_confidence': defaultdict(list),
            'content_type_confidence': defaultdict(list)
        }
        
        for chunk in self.chunks_data:
            metadata = chunk.get('metadata', {})
            
            method = metadata.get('classification_method', 'unknown')
            classification_metrics['methods'][method] += 1
            
            confidence = metadata.get('classification_confidence', 0.0)
            if isinstance(confidence, (int, float)):
                classification_metrics['confidence_scores'].append(float(confidence))
                classification_metrics['method_confidence'][method].append(float(confidence))
                
                content_type = metadata.get('content_type', 'unknown')
                classification_metrics['content_type_confidence'][content_type].append(float(confidence))
                
                if confidence < 0.7:
                    classification_metrics['low_confidence_chunks'] += 1
        
        # Calculate confidence statistics
        if classification_metrics['confidence_scores']:
            classification_metrics['avg_confidence'] = np.mean(classification_metrics['confidence_scores'])
            classification_metrics['median_confidence'] = np.median(classification_metrics['confidence_scores'])
            classification_metrics['std_confidence'] = np.std(classification_metrics['confidence_scores'])
        
        # Calculate method-specific confidence
        for method, scores in classification_metrics['method_confidence'].items():
            if scores:
                classification_metrics[f'{method}_avg_confidence'] = np.mean(scores)
        
        # Convert defaultdicts to regular dicts
        classification_metrics['methods'] = dict(classification_metrics['methods'])
        classification_metrics['method_confidence'] = {k: list(v) for k, v in classification_metrics['method_confidence'].items()}
        classification_metrics['content_type_confidence'] = {k: list(v) for k, v in classification_metrics['content_type_confidence'].items()}
        
        self.validation_results['classification_accuracy'] = classification_metrics
    
    def _validate_group_structure(self):
        """Validate group structure and relationships"""
        
        print("🔗 Validating group structure...")
        
        group_metrics = {
            'total_groups': 0,
            'group_sizes': [],
            'orphaned_chunks': 0,
            'broken_sequences': 0,
            'group_types': defaultdict(int),
            'navigation_errors': 0
        }
        
        # Group chunks by group_id
        groups = defaultdict(list)
        ungrouped_chunks = []
        
        for chunk in self.chunks_data:
            metadata = chunk.get('metadata', {})
            group_id = metadata.get('group_id')
            
            if group_id:
                groups[group_id].append(chunk)
            else:
                ungrouped_chunks.append(chunk)
        
        group_metrics['total_groups'] = len(groups)
        group_metrics['orphaned_chunks'] = len(ungrouped_chunks)
        
        # Analyze each group
        for group_id, group_chunks in groups.items():
            group_size = len(group_chunks)
            group_metrics['group_sizes'].append(group_size)
            
            # Determine group type
            content_types = [chunk.get('metadata', {}).get('content_type', '') for chunk in group_chunks]
            if 'procedure' in content_types:
                group_metrics['group_types']['procedure'] += 1
            elif 'safety_alert' in content_types:
                group_metrics['group_types']['safety'] += 1
            else:
                group_metrics['group_types']['other'] += 1
            
            # Validate sequence if procedural
            if any('procedure' in ct for ct in content_types):
                positions = []
                for chunk in group_chunks:
                    metadata = chunk.get('metadata', {})
                    pos = metadata.get('group_position')
                    if pos:
                        positions.append(pos)
                
                if positions:
                    expected_positions = list(range(1, len(positions) + 1))
                    if sorted(positions) != expected_positions:
                        group_metrics['broken_sequences'] += 1
        
        # Calculate group statistics
        if group_metrics['group_sizes']:
            group_metrics['avg_group_size'] = np.mean(group_metrics['group_sizes'])
            group_metrics['median_group_size'] = np.median(group_metrics['group_sizes'])
            group_metrics['max_group_size'] = max(group_metrics['group_sizes'])
        
        group_metrics['group_types'] = dict(group_metrics['group_types'])
        
        self.validation_results['group_structure'] = group_metrics
    
    def _validate_metadata_completeness(self):
        """Validate metadata completeness and consistency"""
        
        print("📋 Validating metadata completeness...")
        
        metadata_metrics = {
            'required_fields': ['id', 'content_type', 'semantic_role', 'level'],
            'optional_fields': ['group_id', 'summary', 'keywords', 'image_gcs_uri'],
            'field_completeness': {},
            'missing_required': 0,
            'incomplete_chunks': []
        }
        
        all_fields = metadata_metrics['required_fields'] + metadata_metrics['optional_fields']
        field_counts = {field: 0 for field in all_fields}
        
        for chunk in self.chunks_data:
            chunk_id = chunk.get('id', 'unknown')
            metadata = chunk.get('metadata', {})
            
            missing_required = []
            
            for field in all_fields:
                if field in metadata and metadata[field] not in [None, '', [], {}]:
                    field_counts[field] += 1
                elif field in metadata_metrics['required_fields']:
                    missing_required.append(field)
            
            if missing_required:
                metadata_metrics['missing_required'] += 1
                metadata_metrics['incomplete_chunks'].append({
                    'id': chunk_id,
                    'missing_fields': missing_required
                })
        
        # Calculate completeness percentages
        total_chunks = len(self.chunks_data)
        if total_chunks > 0:
            for field in all_fields:
                completeness = (field_counts[field] / total_chunks) * 100
                metadata_metrics['field_completeness'][field] = completeness
        
        # Calculate overall completeness score
        required_completeness = []
        for field in metadata_metrics['required_fields']:
            if field in metadata_metrics['field_completeness']:
                required_completeness.append(metadata_metrics['field_completeness'][field])
        
        if required_completeness:
            metadata_metrics['overall_completeness'] = np.mean(required_completeness)
        
        self.validation_results['metadata_completeness'] = metadata_metrics
    
    def _analyze_token_efficiency(self):
        """Analyze token efficiency and content density"""
        
        print("🎯 Analyzing token efficiency...")
        
        efficiency_metrics = {
            'token_counts': [],
            'efficiencies': [],
            'content_lengths': [],
            'tokens_per_char': [],
            'low_efficiency_chunks': 0,
            'efficiency_by_type': defaultdict(list),
            'efficiency_by_level': defaultdict(list)
        }
        
        for chunk in self.chunks_data:
            content = chunk.get('content', '')
            metadata = chunk.get('metadata', {})
            
            # Token metrics
            token_count = metadata.get('token_count', 0)
            if token_count > 0:
                efficiency_metrics['token_counts'].append(token_count)
            
            # Efficiency metrics
            efficiency = metadata.get('token_efficiency', 0.0)
            if isinstance(efficiency, (int, float)):
                efficiency_metrics['efficiencies'].append(float(efficiency))
                
                if efficiency < 1.5:  # Low efficiency threshold
                    efficiency_metrics['low_efficiency_chunks'] += 1
                
                # Group by content type
                content_type = metadata.get('content_type', 'unknown')
                efficiency_metrics['efficiency_by_type'][content_type].append(float(efficiency))
                
                # Group by level
                level = metadata.get('level', 'unknown')
                efficiency_metrics['efficiency_by_level'][level].append(float(efficiency))
            
            # Content length
            content_length = len(content)
            efficiency_metrics['content_lengths'].append(content_length)
            
            # Tokens per character ratio
            if token_count > 0 and content_length > 0:
                ratio = token_count / content_length
                efficiency_metrics['tokens_per_char'].append(ratio)
        
        # Calculate statistics
        for metric_list in ['token_counts', 'efficiencies', 'content_lengths', 'tokens_per_char']:
            data = efficiency_metrics[metric_list]
            if data:
                efficiency_metrics[f'avg_{metric_list}'] = np.mean(data)
                efficiency_metrics[f'median_{metric_list}'] = np.median(data)
                efficiency_metrics[f'std_{metric_list}'] = np.std(data)
        
        # Calculate efficiency by category
        for category in ['efficiency_by_type', 'efficiency_by_level']:
            category_stats = {}
            for key, values in efficiency_metrics[category].items():
                if values:
                    category_stats[key] = {
                        'avg': np.mean(values),
                        'count': len(values)
                    }
            efficiency_metrics[f'{category}_stats'] = category_stats
        
        self.validation_results['token_efficiency'] = efficiency_metrics
    
    def _check_embedding_quality(self):
        """Check embedding quality and dimensionality"""
        
        print("🔢 Checking embedding quality...")
        
        embedding_metrics = {
            'total_embeddings': 0,
            'missing_embeddings': 0,
            'invalid_embeddings': 0,
            'dimension_consistency': True,
            'dimensions': [],
            'zero_embeddings': 0,
            'nan_embeddings': 0
        }
        
        expected_dimension = None
        
        for chunk in self.chunks_data:
            embedding = chunk.get('embedding')
            
            if not embedding:
                embedding_metrics['missing_embeddings'] += 1
                continue
            
            if not isinstance(embedding, list):
                embedding_metrics['invalid_embeddings'] += 1
                continue
            
            embedding_metrics['total_embeddings'] += 1
            
            # Check dimension
            dimension = len(embedding)
            embedding_metrics['dimensions'].append(dimension)
            
            if expected_dimension is None:
                expected_dimension = dimension
            elif dimension != expected_dimension:
                embedding_metrics['dimension_consistency'] = False
            
            # Check for problematic embeddings
            try:
                embedding_array = np.array(embedding, dtype='float32')
                
                if np.all(embedding_array == 0):
                    embedding_metrics['zero_embeddings'] += 1
                
                if np.any(np.isnan(embedding_array)):
                    embedding_metrics['nan_embeddings'] += 1
                    
            except (ValueError, TypeError):
                embedding_metrics['invalid_embeddings'] += 1
        
        # Calculate statistics
        if embedding_metrics['dimensions']:
            embedding_metrics['most_common_dimension'] = Counter(embedding_metrics['dimensions']).most_common(1)[0][0]
            embedding_metrics['unique_dimensions'] = len(set(embedding_metrics['dimensions']))
        
        # Include vector stats if available
        if self.vector_stats:
            embedding_metrics['vector_stats'] = self.vector_stats
        
        self.validation_results['embedding_quality'] = embedding_metrics
    
    def _generate_charts(self):
        """Generate visualization charts"""
        
        print("📈 Generating visualization charts...")
        
        # Set style
        plt.style.use('default')
        if 'seaborn' in plt.style.available:
            plt.style.use('seaborn-v0_8')
        
        try:
            # Quality distribution chart
            self._create_quality_distribution_chart()
            
            # Content type distribution
            self._create_content_distribution_chart()
            
            # Token efficiency distribution
            self._create_token_efficiency_chart()
            
            # Classification confidence chart
            self._create_classification_confidence_chart()
            
        except Exception as e:
            print(f"⚠️ Error generating charts: {e}")
    
    def _create_quality_distribution_chart(self):
        """Create quality flag distribution chart"""
        
        quality_data = self.validation_results.get('chunk_quality', {}).get('quality_flags', {})
        
        if not quality_data:
            return
        
        plt.figure(figsize=(10, 6))
        
        # Create pie chart
        labels = list(quality_data.keys())
        sizes = list(quality_data.values())
        colors = ['#2ecc71', '#f39c12', '#e74c3c']  # green, orange, red
        
        plt.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors, startangle=90)
        plt.title('Quality Flag Distribution', fontsize=16, fontweight='bold')
        plt.axis('equal')
        
        chart_file = self.charts_dir / "quality_distribution.png"
        plt.savefig(chart_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"📊 Created quality distribution chart: {chart_file}")
    
    def _create_content_distribution_chart(self):
        """Create content type distribution chart"""
        
        content_data = self.validation_results.get('content_distribution', {}).get('content_types', {})
        
        if not content_data:
            return
        
        plt.figure(figsize=(12, 8))
        
        # Create horizontal bar chart
        items = list(content_data.items())
        items.sort(key=lambda x: x[1], reverse=True)
        
        labels = [item[0] for item in items]
        values = [item[1] for item in items]
        
        bars = plt.barh(labels, values)
        plt.title('Content Type Distribution', fontsize=16, fontweight='bold')
        plt.xlabel('Number of Chunks')
        
        # Add value labels on bars
        for bar, value in zip(bars, values):
            plt.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2, 
                    str(value), ha='left', va='center')
        
        plt.tight_layout()
        
        chart_file = self.charts_dir / "content_distribution.png"
        plt.savefig(chart_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"📊 Created content distribution chart: {chart_file}")
    
    def _create_token_efficiency_chart(self):
        """Create token efficiency distribution chart"""
        
        efficiency_data = self.validation_results.get('token_efficiency', {}).get('efficiencies', [])
        
        if not efficiency_data:
            return
        
        plt.figure(figsize=(10, 6))
        
        # Create histogram
        plt.hist(efficiency_data, bins=30, alpha=0.7, color='skyblue', edgecolor='black')
        plt.title('Token Efficiency Distribution', fontsize=16, fontweight='bold')
        plt.xlabel('Token Efficiency Score')
        plt.ylabel('Number of Chunks')
        
        # Add vertical line for average
        mean_efficiency = np.mean(efficiency_data)
        plt.axvline(mean_efficiency, color='red', linestyle='--', 
                   label=f'Mean: {mean_efficiency:.2f}')
        plt.legend()
        
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        chart_file = self.charts_dir / "token_efficiency.png"
        plt.savefig(chart_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"📊 Created token efficiency chart: {chart_file}")
    
    def _create_classification_confidence_chart(self):
        """Create classification confidence chart"""
        
        confidence_data = self.validation_results.get('classification_accuracy', {}).get('confidence_scores', [])
        
        if not confidence_data:
            return
        
        plt.figure(figsize=(10, 6))
        
        # Create histogram
        plt.hist(confidence_data, bins=20, alpha=0.7, color='lightgreen', edgecolor='black')
        plt.title('Classification Confidence Distribution', fontsize=16, fontweight='bold')
        plt.xlabel('Confidence Score')
        plt.ylabel('Number of Chunks')
        
        # Add vertical line for threshold
        plt.axvline(0.7, color='red', linestyle='--', 
                   label='Confidence Threshold (0.7)')
        plt.legend()
        
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        chart_file = self.charts_dir / "classification_confidence.png"
        plt.savefig(chart_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"📊 Created classification confidence chart: {chart_file}")
    
    def _generate_html_report(self):
        """Generate comprehensive HTML report"""
        
        print("📄 Generating HTML report...")
        
        html_content = self._build_html_content()
        
        with open(self.report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ HTML report generated: {self.report_file}")
    
    def _build_html_content(self) -> str:
        """Build HTML content for the report"""
        
        # Calculate overall scores
        overall_score = self._calculate_overall_score()
        
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enhanced RAG Chunking Validation Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            border-bottom: 3px solid #3498db;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            color: #2c3e50;
            margin: 0;
            font-size: 2.5em;
        }}
        .header p {{
            color: #7f8c8d;
            font-size: 1.1em;
            margin: 10px 0 0 0;
        }}
        .score-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 30px;
        }}
        .score-card h2 {{
            margin: 0;
            font-size: 2em;
        }}
        .score-card p {{
            margin: 10px 0 0 0;
            font-size: 1.2em;
        }}
        .section {{
            margin-bottom: 40px;
            padding: 20px;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
        }}
        .section h2 {{
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }}
        .metric-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        .metric-card {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #3498db;
        }}
        .metric-card h4 {{
            margin: 0 0 10px 0;
            color: #2c3e50;
        }}
        .metric-value {{
            font-size: 1.5em;
            font-weight: bold;
            color: #27ae60;
        }}
        .warning {{
            color: #e74c3c;
        }}
        .good {{
            color: #27ae60;
        }}
        .recommendations {{
            background-color: #e8f4fd;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #3498db;
        }}
        .recommendations h3 {{
            color: #2c3e50;
            margin-top: 0;
        }}
        .recommendations ul {{
            padding-left: 20px;
        }}
        .recommendations li {{
            margin-bottom: 8px;
        }}
        .footer {{
            text-align: center;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
            color: #7f8c8d;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Enhanced RAG Chunking Validation Report</h1>
            <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="score-card">
            <h2>{overall_score:.1f}/100</h2>
            <p>Overall Quality Score</p>
        </div>
        
        {self._build_chunk_quality_section()}
        {self._build_content_distribution_section()}
        {self._build_classification_section()}
        {self._build_metadata_section()}
        {self._build_recommendations_section()}
        
        <div class="footer">
            <p>Report generated by Enhanced RAG Chunking Validation System</p>
        </div>
    </div>
</body>
</html>
"""
        
        return html_content
    
    def _calculate_overall_score(self) -> float:
        """Calculate overall quality score"""
        
        scores = []
        
        # Chunk quality score (30% weight)
        chunk_quality = self.validation_results.get('chunk_quality', {})
        if 'overall_quality_score' in chunk_quality:
            scores.append(chunk_quality['overall_quality_score'] * 0.3)
        
        # Metadata completeness (25% weight)
        metadata_completeness = self.validation_results.get('metadata_completeness', {})
        if 'overall_completeness' in metadata_completeness:
            scores.append(metadata_completeness['overall_completeness'] * 0.25)
        
        # Classification confidence (20% weight)
        classification = self.validation_results.get('classification_accuracy', {})
        if 'avg_confidence' in classification:
            confidence_score = classification['avg_confidence'] * 100
            scores.append(confidence_score * 0.2)
        
        # Token efficiency (15% weight)
        efficiency = self.validation_results.get('token_efficiency', {})
        if 'avg_efficiencies' in efficiency:
            eff_score = min(100, efficiency['avg_efficiencies'] * 50)  # Scale to 100
            scores.append(eff_score * 0.15)
        
        # Embedding quality (10% weight)
        embedding = self.validation_results.get('embedding_quality', {})
        if embedding:
            embed_score = 100
            if embedding.get('missing_embeddings', 0) > 0:
                embed_score -= 20
            if not embedding.get('dimension_consistency', True):
                embed_score -= 20
            scores.append(embed_score * 0.1)
        
        return sum(scores) if scores else 0.0
    
    def _build_chunk_quality_section(self) -> str:
        """Build chunk quality section"""
        
        quality_data = self.validation_results.get('chunk_quality', {})
        
        if not quality_data:
            return ""
        
        return f"""
        <div class="section">
            <h2>📊 Chunk Quality Analysis</h2>
            
            <div class="metric-grid">
                <div class="metric-card">
                    <h4>Total Chunks</h4>
                    <div class="metric-value">{quality_data.get('total_chunks', 0)}</div>
                </div>
                
                <div class="metric-card">
                    <h4>Average Completeness</h4>
                    <div class="metric-value">{quality_data.get('avg_completeness', 0):.2f}</div>
                </div>
                
                <div class="metric-card">
                    <h4>Average Token Efficiency</h4>
                    <div class="metric-value">{quality_data.get('avg_token_efficiency', 0):.2f}</div>
                </div>
                
                <div class="metric-card">
                    <h4>Chunks Needing Review</h4>
                    <div class="metric-value {'warning' if quality_data.get('needs_review_count', 0) > 0 else 'good'}">
                        {quality_data.get('needs_review_count', 0)}
                    </div>
                </div>
            </div>
        </div>
        """
    
    def _build_content_distribution_section(self) -> str:
        """Build content distribution section"""
        
        dist_data = self.validation_results.get('content_distribution', {})
        
        if not dist_data:
            return ""
        
        return f"""
        <div class="section">
            <h2>📋 Content Distribution</h2>
            
            <div class="metric-grid">
                <div class="metric-card">
                    <h4>Content Type Diversity</h4>
                    <div class="metric-value">{dist_data.get('content_type_diversity', 0)}</div>
                </div>
                
                <div class="metric-card">
                    <h4>Semantic Role Diversity</h4>
                    <div class="metric-value">{dist_data.get('semantic_role_diversity', 0)}</div>
                </div>
                
                <div class="metric-card">
                    <h4>Unique Sections</h4>
                    <div class="metric-value">{dist_data.get('section_diversity', 0)}</div>
                </div>
            </div>
        </div>
        """
    
    def _build_classification_section(self) -> str:
        """Build classification analysis section"""
        
        class_data = self.validation_results.get('classification_accuracy', {})
        
        if not class_data:
            return ""
        
        return f"""
        <div class="section">
            <h2>🧠 Classification Analysis</h2>
            
            <div class="metric-grid">
                <div class="metric-card">
                    <h4>Average Confidence</h4>
                    <div class="metric-value">{class_data.get('avg_confidence', 0):.2f}</div>
                </div>
                
                <div class="metric-card">
                    <h4>Low Confidence Chunks</h4>
                    <div class="metric-value {'warning' if class_data.get('low_confidence_chunks', 0) > 0 else 'good'}">
                        {class_data.get('low_confidence_chunks', 0)}
                    </div>
                </div>
                
                <div class="metric-card">
                    <h4>LLM Classifications</h4>
                    <div class="metric-value">{class_data.get('methods', {}).get('llm', 0)}</div>
                </div>
                
                <div class="metric-card">
                    <h4>Pattern Fallbacks</h4>
                    <div class="metric-value">{class_data.get('methods', {}).get('pattern_fallback', 0)}</div>
                </div>
            </div>
        </div>
        """
    
    def _build_metadata_section(self) -> str:
        """Build metadata completeness section"""
        
        meta_data = self.validation_results.get('metadata_completeness', {})
        
        if not meta_data:
            return ""
        
        return f"""
        <div class="section">
            <h2>📋 Metadata Completeness</h2>
            
            <div class="metric-grid">
                <div class="metric-card">
                    <h4>Overall Completeness</h4>
                    <div class="metric-value">{meta_data.get('overall_completeness', 0):.1f}%</div>
                </div>
                
                <div class="metric-card">
                    <h4>Missing Required Fields</h4>
                    <div class="metric-value {'warning' if meta_data.get('missing_required', 0) > 0 else 'good'}">
                        {meta_data.get('missing_required', 0)}
                    </div>
                </div>
            </div>
        </div>
        """
    
    def _build_recommendations_section(self) -> str:
        """Build recommendations section"""
        
        recommendations = self._generate_recommendations()
        
        rec_items = ""
        for rec in recommendations:
            rec_items += f"<li>{rec}</li>"
        
        return f"""
        <div class="recommendations">
            <h3>💡 Recommendations</h3>
            <ul>
                {rec_items}
            </ul>
        </div>
        """
    
    def _generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations"""
        
        recommendations = []
        
        # Chunk quality recommendations
        quality_data = self.validation_results.get('chunk_quality', {})
        if quality_data.get('needs_review_count', 0) > 0:
            recommendations.append(f"Review {quality_data['needs_review_count']} chunks flagged for manual review.")
        
        if quality_data.get('avg_completeness', 0) < 0.7:
            recommendations.append("Consider adjusting chunking parameters to improve completeness.")
        
        # Classification recommendations
        class_data = self.validation_results.get('classification_accuracy', {})
        if class_data.get('low_confidence_chunks', 0) > 0:
            recommendations.append(f"Review {class_data['low_confidence_chunks']} chunks with low classification confidence.")
        
        # General recommendations
        if not recommendations:
            recommendations.append("Overall quality looks good! Consider periodic validation.")
        
        return recommendations
    
    def _save_summary(self):
        """Save validation summary as JSON"""
        
        summary = {
            'report_generated_at': datetime.now().isoformat(),
            'overall_score': self._calculate_overall_score(),
            'validation_results': self.validation_results,
            'recommendations': self._generate_recommendations()
        }
        
        with open(self.summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"📋 Summary saved: {self.summary_file}")

def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate validation report for enhanced chunking")
    parser.add_argument("--jsonl", help="Path to JSONL file with chunks")
    parser.add_argument("--vector-dir", help="Path to vector directory")
    parser.add_argument("--output-dir", default="training/output/reports", help="Output directory for reports")
    
    args = parser.parse_args()
    
    if not args.jsonl and not args.vector_dir:
        print("❌ Must provide either --jsonl or --vector-dir")
        return 1
    
    # Generate report
    generator = ValidationReportGenerator(
        jsonl_file=args.jsonl,
        vector_dir=args.vector_dir,
        output_dir=args.output_dir
    )
    
    try:
        results = generator.generate_comprehensive_report()
        print(f"\n✅ Validation report completed successfully!")
        return 0
        
    except Exception as e:
        print(f"❌ Report generation failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())