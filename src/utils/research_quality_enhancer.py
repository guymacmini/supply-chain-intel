"""Research quality enhancement utilities for improved analysis depth and accuracy."""

import re
import json
import statistics
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from collections import Counter, defaultdict
import logging

from .research_analytics import ResearchAnalyticsEngine
from .performance_optimizer import cached, timed

logger = logging.getLogger(__name__)


@dataclass
class QualityMetrics:
    """Comprehensive quality metrics for research documents."""
    factual_accuracy_score: float = 0.0
    source_credibility_score: float = 0.0
    analysis_depth_score: float = 0.0
    objectivity_score: float = 0.0
    actionability_score: float = 0.0
    clarity_score: float = 0.0
    completeness_score: float = 0.0
    timeliness_score: float = 0.0
    overall_quality_score: float = 0.0
    
    improvement_suggestions: List[str] = field(default_factory=list)
    strength_areas: List[str] = field(default_factory=list)
    weakness_areas: List[str] = field(default_factory=list)


@dataclass
class ContentEnhancement:
    """Suggested enhancements for research content."""
    enhancement_type: str  # 'fact_check', 'add_source', 'clarify', etc.
    priority: str  # 'high', 'medium', 'low'
    suggestion: str
    original_text: str = ""
    suggested_replacement: str = ""
    confidence: float = 1.0


class ResearchQualityAnalyzer:
    """Analyzes and measures research quality across multiple dimensions."""
    
    def __init__(self, data_dir: Path):
        """Initialize quality analyzer.
        
        Args:
            data_dir: Directory containing research data
        """
        self.data_dir = data_dir
        self.analytics_engine = ResearchAnalyticsEngine(data_dir)
        
        # Load quality standards and benchmarks
        self.quality_standards = self._load_quality_standards()
        self.source_credibility_db = self._load_source_credibility_database()
        
    def _load_quality_standards(self) -> Dict:
        """Load quality standards for research evaluation."""
        return {
            'min_word_count': 3000,
            'min_sources': 8,
            'min_tables': 2,
            'min_sections': 5,
            'max_sentiment_bias': 0.3,
            'min_confidence_indicators': 5,
            'required_sections': [
                'executive summary', 'tldr', 'analysis', 'investment thesis',
                'risk factors', 'sources'
            ],
            'credible_domains': [
                'sec.gov', 'edgar.gov', 'bloomberg.com', 'reuters.com',
                'wsj.com', 'ft.com', 'economist.com', 'investopedia.com',
                'morningstar.com', 'yahoo.com/finance', 'google.com/finance'
            ]
        }
    
    def _load_source_credibility_database(self) -> Dict:
        """Load database of source credibility ratings."""
        return {
            # Financial news sources (scale 0.0-1.0)
            'bloomberg.com': 0.95,
            'reuters.com': 0.93,
            'wsj.com': 0.92,
            'ft.com': 0.90,
            'economist.com': 0.88,
            'cnbc.com': 0.75,
            'marketwatch.com': 0.72,
            'yahoo.com': 0.65,
            'investopedia.com': 0.85,
            'morningstar.com': 0.87,
            
            # Government and regulatory
            'sec.gov': 1.0,
            'edgar.gov': 1.0,
            'fed.gov': 0.98,
            'treasury.gov': 0.98,
            
            # Research institutions
            'mckinsey.com': 0.85,
            'bcg.com': 0.84,
            'pwc.com': 0.82,
            'deloitte.com': 0.80,
            
            # Default scores by domain type
            '.gov': 0.95,
            '.edu': 0.85,
            '.org': 0.70,
            '.com': 0.60
        }
    
    @timed('quality_analysis')
    def analyze_research_quality(self, content: str, filename: str = "") -> QualityMetrics:
        """Perform comprehensive quality analysis of research content.
        
        Args:
            content: Research content to analyze
            filename: Optional filename for context
            
        Returns:
            QualityMetrics object with detailed quality assessment
        """
        metrics = QualityMetrics()
        
        # Analyze different quality dimensions
        metrics.factual_accuracy_score = self._assess_factual_accuracy(content)
        metrics.source_credibility_score = self._assess_source_credibility(content)
        metrics.analysis_depth_score = self._assess_analysis_depth(content)
        metrics.objectivity_score = self._assess_objectivity(content)
        metrics.actionability_score = self._assess_actionability(content)
        metrics.clarity_score = self._assess_clarity(content)
        metrics.completeness_score = self._assess_completeness(content)
        metrics.timeliness_score = self._assess_timeliness(content, filename)
        
        # Calculate overall quality score (weighted average)
        weights = {
            'factual_accuracy': 0.20,
            'source_credibility': 0.15,
            'analysis_depth': 0.15,
            'objectivity': 0.12,
            'actionability': 0.10,
            'clarity': 0.10,
            'completeness': 0.10,
            'timeliness': 0.08
        }
        
        metrics.overall_quality_score = (
            metrics.factual_accuracy_score * weights['factual_accuracy'] +
            metrics.source_credibility_score * weights['source_credibility'] +
            metrics.analysis_depth_score * weights['analysis_depth'] +
            metrics.objectivity_score * weights['objectivity'] +
            metrics.actionability_score * weights['actionability'] +
            metrics.clarity_score * weights['clarity'] +
            metrics.completeness_score * weights['completeness'] +
            metrics.timeliness_score * weights['timeliness']
        )
        
        # Generate improvement suggestions
        metrics.improvement_suggestions = self._generate_improvement_suggestions(metrics, content)
        metrics.strength_areas = self._identify_strengths(metrics)
        metrics.weakness_areas = self._identify_weaknesses(metrics)
        
        return metrics
    
    def _assess_factual_accuracy(self, content: str) -> float:
        """Assess factual accuracy of research content."""
        score = 1.0  # Start with perfect score
        
        # Check for fact-checking indicators
        fact_indicators = [
            'according to', 'reported by', 'data shows', 'studies indicate',
            'research reveals', 'analysis found', 'statistics show',
            'evidence suggests', 'peer-reviewed', 'verified by'
        ]
        
        fact_count = sum(content.lower().count(indicator) for indicator in fact_indicators)
        
        # Check for speculation without backing
        speculation_patterns = [
            r'might be', r'could potentially', r'it seems', r'appears to be',
            r'possibly', r'maybe', r'perhaps', r'presumably'
        ]
        
        speculation_count = sum(len(re.findall(pattern, content, re.IGNORECASE)) 
                               for pattern in speculation_patterns)
        
        # Calculate score based on fact vs speculation ratio
        total_claims = fact_count + speculation_count
        if total_claims > 0:
            fact_ratio = fact_count / total_claims
            score = max(0.4, fact_ratio)  # Minimum score of 0.4
        
        # Penalty for excessive speculation
        if speculation_count > fact_count * 2:
            score *= 0.8
        
        # Check for data citations and numbers
        number_patterns = r'\$[\d,.]+ [a-z]+|\d+%|\d+\.?\d* [a-z]+'
        numbers_found = len(re.findall(number_patterns, content, re.IGNORECASE))
        if numbers_found > 10:  # Good quantitative backing
            score += 0.1
        
        return min(1.0, score)
    
    def _assess_source_credibility(self, content: str) -> float:
        """Assess credibility of sources cited in research."""
        # Extract URLs and source mentions
        url_pattern = r'https?://([a-zA-Z0-9.-]+)'
        urls = re.findall(url_pattern, content)
        
        if not urls:
            return 0.3  # Low score if no sources
        
        credibility_scores = []
        
        for url in urls:
            domain = url.lower()
            
            # Check exact domain match
            if domain in self.source_credibility_db:
                credibility_scores.append(self.source_credibility_db[domain])
            else:
                # Check domain type
                domain_score = 0.5  # Default score
                for domain_type, score in self.source_credibility_db.items():
                    if domain_type.startswith('.') and domain.endswith(domain_type):
                        domain_score = score
                        break
                credibility_scores.append(domain_score)
        
        if credibility_scores:
            avg_credibility = statistics.mean(credibility_scores)
            
            # Bonus for diverse sources
            unique_domains = len(set(urls))
            if unique_domains >= 5:
                avg_credibility += 0.05
            
            return min(1.0, avg_credibility)
        
        return 0.3
    
    def _assess_analysis_depth(self, content: str) -> float:
        """Assess depth and thoroughness of analysis."""
        score = 0.0
        
        # Check for analytical frameworks
        frameworks = [
            'swot analysis', 'porter five forces', 'pestle', 'competitive analysis',
            'financial analysis', 'market analysis', 'risk assessment',
            'scenario analysis', 'sensitivity analysis', 'dcf', 'valuation model'
        ]
        
        framework_count = sum(content.lower().count(framework) for framework in frameworks)
        score += min(0.3, framework_count * 0.1)
        
        # Check for quantitative analysis
        quant_indicators = [
            'ratio', 'margin', 'growth rate', 'correlation', 'trend',
            'projection', 'forecast', 'estimate', 'calculation', 'model'
        ]
        
        quant_count = sum(content.lower().count(indicator) for indicator in quant_indicators)
        score += min(0.3, quant_count * 0.02)
        
        # Check for multiple perspectives
        perspective_indicators = [
            'however', 'on the other hand', 'alternatively', 'conversely',
            'but', 'nevertheless', 'despite', 'although', 'while'
        ]
        
        perspective_count = sum(content.lower().count(indicator) for indicator in perspective_indicators)
        score += min(0.2, perspective_count * 0.05)
        
        # Check for detailed sections
        section_count = len(re.findall(r'^#{1,3}\s', content, re.MULTILINE))
        score += min(0.2, section_count * 0.02)
        
        return min(1.0, score)
    
    def _assess_objectivity(self, content: str) -> float:
        """Assess objectivity and lack of bias in research."""
        # Calculate sentiment bias (from analytics engine)
        sentiment_score = self._calculate_sentiment_bias(content)
        
        # Objective language indicators
        objective_phrases = [
            'data suggests', 'analysis shows', 'research indicates',
            'studies demonstrate', 'evidence points to', 'statistics reveal',
            'according to', 'based on', 'findings indicate'
        ]
        
        subjective_phrases = [
            'i believe', 'in my opinion', 'clearly', 'obviously',
            'definitely', 'certainly', 'undoubtedly', 'absolutely'
        ]
        
        objective_count = sum(content.lower().count(phrase) for phrase in objective_phrases)
        subjective_count = sum(content.lower().count(phrase) for phrase in subjective_phrases)
        
        # Calculate objectivity ratio
        total_phrases = objective_count + subjective_count
        if total_phrases > 0:
            objectivity_ratio = objective_count / total_phrases
        else:
            objectivity_ratio = 0.7  # Neutral if no indicators found
        
        # Combine sentiment and language objectivity
        sentiment_objectivity = 1.0 - abs(sentiment_score)  # Closer to 0 is more objective
        
        return (objectivity_ratio * 0.6) + (sentiment_objectivity * 0.4)
    
    def _assess_actionability(self, content: str) -> float:
        """Assess how actionable the research insights are."""
        score = 0.0
        
        # Check for clear recommendations
        recommendation_indicators = [
            'recommend', 'suggestion', 'should', 'advised', 'propose',
            'buy', 'sell', 'hold', 'target price', 'price target',
            'investment thesis', 'strategy', 'action plan'
        ]
        
        rec_count = sum(content.lower().count(indicator) for indicator in recommendation_indicators)
        score += min(0.4, rec_count * 0.05)
        
        # Check for specific metrics and targets
        target_patterns = [
            r'\$[\d,.]+ target', r'\d+% upside', r'\d+% downside',
            r'price target.*\$[\d,.]+', r'\d+ [a-z]+ horizon'
        ]
        
        target_count = sum(len(re.findall(pattern, content, re.IGNORECASE)) 
                          for pattern in target_patterns)
        score += min(0.3, target_count * 0.1)
        
        # Check for timeline indicators
        timeline_indicators = [
            'short term', 'long term', 'near term', 'medium term',
            'next quarter', 'next year', 'within', 'by 2024', 'by 2025'
        ]
        
        timeline_count = sum(content.lower().count(indicator) for indicator in timeline_indicators)
        score += min(0.3, timeline_count * 0.03)
        
        return min(1.0, score)
    
    def _assess_clarity(self, content: str) -> float:
        """Assess clarity and readability of research content."""
        # Calculate reading complexity
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return 0.0
        
        # Average sentence length
        avg_sentence_length = statistics.mean(len(sentence.split()) for sentence in sentences)
        
        # Penalty for overly long sentences
        length_score = max(0.5, 1.0 - (avg_sentence_length - 15) / 20) if avg_sentence_length > 15 else 1.0
        
        # Check for clear structure
        structure_indicators = [
            'tldr', 'executive summary', 'key points', 'conclusion',
            'overview', 'highlights', 'summary'
        ]
        
        structure_count = sum(content.lower().count(indicator) for indicator in structure_indicators)
        structure_score = min(0.3, structure_count * 0.1)
        
        # Check for jargon density
        jargon_words = [
            'synergy', 'paradigm', 'leverage', 'scalable', 'optimization',
            'monetization', 'verticalization', 'ideation', 'operationalize'
        ]
        
        jargon_count = sum(content.lower().count(word) for word in jargon_words)
        word_count = len(content.split())
        jargon_density = jargon_count / word_count if word_count > 0 else 0
        
        jargon_penalty = min(0.2, jargon_density * 10)  # Penalty for excessive jargon
        
        return max(0.0, length_score + structure_score - jargon_penalty)
    
    def _assess_completeness(self, content: str) -> float:
        """Assess completeness of research coverage."""
        score = 0.0
        
        # Check for required sections
        required_sections = self.quality_standards['required_sections']
        sections_found = 0
        
        for section in required_sections:
            if section.lower() in content.lower():
                sections_found += 1
        
        section_score = sections_found / len(required_sections)
        score += section_score * 0.4
        
        # Check for comprehensive coverage indicators
        coverage_indicators = [
            'market size', 'competitors', 'financial metrics', 'growth prospects',
            'risk factors', 'valuation', 'industry trends', 'regulatory environment'
        ]
        
        coverage_count = sum(content.lower().count(indicator) for indicator in coverage_indicators)
        coverage_score = min(0.3, coverage_count * 0.04)
        score += coverage_score
        
        # Check for adequate length
        word_count = len(content.split())
        min_words = self.quality_standards['min_word_count']
        
        if word_count >= min_words:
            length_score = 0.3
        elif word_count >= min_words * 0.8:
            length_score = 0.2
        elif word_count >= min_words * 0.6:
            length_score = 0.1
        else:
            length_score = 0.0
        
        score += length_score
        
        return min(1.0, score)
    
    def _assess_timeliness(self, content: str, filename: str) -> float:
        """Assess timeliness and currency of research content."""
        score = 1.0  # Start with full score
        
        # Extract date from filename if possible
        date_pattern = r'(\d{4})(\d{2})(\d{2})'
        date_match = re.search(date_pattern, filename)
        
        if date_match:
            try:
                file_date = datetime.strptime(date_match.group(), '%Y%m%d')
                days_old = (datetime.now() - file_date).days
                
                # Penalize old research
                if days_old > 30:
                    score *= 0.8
                elif days_old > 90:
                    score *= 0.6
                elif days_old > 180:
                    score *= 0.4
            except:
                pass
        
        # Check for recent data references
        recent_indicators = [
            '2024', '2023', 'recent', 'latest', 'current', 'today',
            'this quarter', 'this year', 'last quarter'
        ]
        
        recent_count = sum(content.lower().count(indicator) for indicator in recent_indicators)
        if recent_count > 5:
            score = min(1.0, score + 0.1)
        
        # Penalty for outdated references
        outdated_indicators = ['2020', '2019', '2018', 'several years ago', 'historically']
        outdated_count = sum(content.lower().count(indicator) for indicator in outdated_indicators)
        
        if outdated_count > recent_count:
            score *= 0.7
        
        return max(0.1, score)
    
    def _calculate_sentiment_bias(self, content: str) -> float:
        """Calculate sentiment bias score."""
        positive_words = [
            'excellent', 'outstanding', 'strong', 'impressive', 'remarkable',
            'significant', 'substantial', 'robust', 'solid', 'promising'
        ]
        
        negative_words = [
            'terrible', 'awful', 'weak', 'poor', 'disappointing',
            'concerning', 'problematic', 'declining', 'struggling', 'failing'
        ]
        
        pos_count = sum(content.lower().count(word) for word in positive_words)
        neg_count = sum(content.lower().count(word) for word in negative_words)
        
        total_sentiment = pos_count + neg_count
        if total_sentiment == 0:
            return 0.0
        
        return (pos_count - neg_count) / total_sentiment
    
    def _generate_improvement_suggestions(self, metrics: QualityMetrics, content: str) -> List[str]:
        """Generate specific improvement suggestions based on quality analysis."""
        suggestions = []
        
        if metrics.factual_accuracy_score < 0.7:
            suggestions.append("Add more factual references and reduce speculative language")
        
        if metrics.source_credibility_score < 0.6:
            suggestions.append("Include more credible sources from established financial publications")
        
        if metrics.analysis_depth_score < 0.6:
            suggestions.append("Deepen analysis with quantitative metrics and analytical frameworks")
        
        if metrics.objectivity_score < 0.7:
            suggestions.append("Reduce bias and use more objective language")
        
        if metrics.actionability_score < 0.6:
            suggestions.append("Add specific recommendations and price targets")
        
        if metrics.clarity_score < 0.7:
            suggestions.append("Improve readability with shorter sentences and clearer structure")
        
        if metrics.completeness_score < 0.7:
            suggestions.append("Ensure all required sections are covered comprehensively")
        
        if metrics.timeliness_score < 0.8:
            suggestions.append("Update with more recent data and market developments")
        
        return suggestions
    
    def _identify_strengths(self, metrics: QualityMetrics) -> List[str]:
        """Identify strength areas based on quality metrics."""
        strengths = []
        
        if metrics.factual_accuracy_score >= 0.8:
            strengths.append("Strong factual accuracy")
        if metrics.source_credibility_score >= 0.8:
            strengths.append("Credible source references")
        if metrics.analysis_depth_score >= 0.8:
            strengths.append("Deep analytical coverage")
        if metrics.objectivity_score >= 0.8:
            strengths.append("Objective presentation")
        if metrics.actionability_score >= 0.8:
            strengths.append("Clear actionable insights")
        if metrics.clarity_score >= 0.8:
            strengths.append("Excellent clarity and readability")
        if metrics.completeness_score >= 0.8:
            strengths.append("Comprehensive coverage")
        if metrics.timeliness_score >= 0.9:
            strengths.append("Current and timely information")
        
        return strengths
    
    def _identify_weaknesses(self, metrics: QualityMetrics) -> List[str]:
        """Identify weakness areas based on quality metrics."""
        weaknesses = []
        
        if metrics.factual_accuracy_score < 0.6:
            weaknesses.append("Insufficient factual backing")
        if metrics.source_credibility_score < 0.6:
            weaknesses.append("Weak source credibility")
        if metrics.analysis_depth_score < 0.6:
            weaknesses.append("Surface-level analysis")
        if metrics.objectivity_score < 0.6:
            weaknesses.append("Biased presentation")
        if metrics.actionability_score < 0.6:
            weaknesses.append("Lacks clear recommendations")
        if metrics.clarity_score < 0.6:
            weaknesses.append("Poor clarity and structure")
        if metrics.completeness_score < 0.6:
            weaknesses.append("Incomplete coverage")
        if metrics.timeliness_score < 0.7:
            weaknesses.append("Outdated information")
        
        return weaknesses


class ContentEnhancer:
    """Suggests and applies content enhancements to improve research quality."""
    
    def __init__(self, quality_analyzer: ResearchQualityAnalyzer):
        """Initialize content enhancer.
        
        Args:
            quality_analyzer: Quality analyzer instance
        """
        self.quality_analyzer = quality_analyzer
    
    def suggest_enhancements(self, content: str, quality_metrics: QualityMetrics) -> List[ContentEnhancement]:
        """Suggest specific content enhancements.
        
        Args:
            content: Research content to enhance
            quality_metrics: Quality analysis results
            
        Returns:
            List of ContentEnhancement suggestions
        """
        enhancements = []
        
        # Source enhancement suggestions
        if quality_metrics.source_credibility_score < 0.7:
            enhancements.extend(self._suggest_source_improvements(content))
        
        # Clarity enhancements
        if quality_metrics.clarity_score < 0.7:
            enhancements.extend(self._suggest_clarity_improvements(content))
        
        # Completeness enhancements
        if quality_metrics.completeness_score < 0.7:
            enhancements.extend(self._suggest_completeness_improvements(content))
        
        # Objectivity enhancements
        if quality_metrics.objectivity_score < 0.7:
            enhancements.extend(self._suggest_objectivity_improvements(content))
        
        return sorted(enhancements, key=lambda x: x.priority)
    
    def _suggest_source_improvements(self, content: str) -> List[ContentEnhancement]:
        """Suggest improvements to source quality and citations."""
        enhancements = []
        
        # Look for unsourced claims
        claim_patterns = [
            r'(\w+ reported that [^.]+\.)',
            r'(Studies show [^.]+\.)',
            r'(Research indicates [^.]+\.)',
            r'(Analysis reveals [^.]+\.)'
        ]
        
        for pattern in claim_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                claim = match.group(1)
                if 'http' not in claim:  # No URL in the claim
                    enhancements.append(ContentEnhancement(
                        enhancement_type='add_source',
                        priority='high',
                        suggestion=f'Add credible source citation for: "{claim}"',
                        original_text=claim,
                        confidence=0.8
                    ))
        
        return enhancements
    
    def _suggest_clarity_improvements(self, content: str) -> List[ContentEnhancement]:
        """Suggest clarity and readability improvements."""
        enhancements = []
        
        # Find overly long sentences
        sentences = re.split(r'[.!?]+', content)
        for sentence in sentences:
            words = sentence.strip().split()
            if len(words) > 40:  # Very long sentence
                enhancements.append(ContentEnhancement(
                    enhancement_type='clarify',
                    priority='medium',
                    suggestion='Consider breaking this long sentence into shorter ones',
                    original_text=sentence.strip(),
                    confidence=0.7
                ))
        
        # Find jargon that could be simplified
        jargon_replacements = {
            'utilize': 'use',
            'facilitate': 'help',
            'optimize': 'improve',
            'leverage': 'use',
            'paradigm': 'model',
            'synergistic': 'combined'
        }
        
        for jargon, replacement in jargon_replacements.items():
            if jargon.lower() in content.lower():
                enhancements.append(ContentEnhancement(
                    enhancement_type='simplify',
                    priority='low',
                    suggestion=f'Consider replacing "{jargon}" with "{replacement}"',
                    original_text=jargon,
                    suggested_replacement=replacement,
                    confidence=0.6
                ))
        
        return enhancements
    
    def _suggest_completeness_improvements(self, content: str) -> List[ContentEnhancement]:
        """Suggest improvements for content completeness."""
        enhancements = []
        
        required_sections = [
            ('executive summary', 'Add an executive summary section'),
            ('risk factors', 'Include risk factors analysis'),
            ('financial metrics', 'Add financial performance metrics'),
            ('competitive analysis', 'Include competitive landscape analysis'),
            ('investment thesis', 'Clearly state the investment thesis')
        ]
        
        for section_name, suggestion in required_sections:
            if section_name.lower() not in content.lower():
                enhancements.append(ContentEnhancement(
                    enhancement_type='add_section',
                    priority='high',
                    suggestion=suggestion,
                    confidence=0.9
                ))
        
        return enhancements
    
    def _suggest_objectivity_improvements(self, content: str) -> List[ContentEnhancement]:
        """Suggest improvements for objectivity and bias reduction."""
        enhancements = []
        
        # Find subjective language
        subjective_patterns = [
            (r'\bobviously\b', 'Consider removing "obviously" for more objective tone'),
            (r'\bclearly\b', 'Consider removing "clearly" for more objective tone'),
            (r'\bundoubtedly\b', 'Consider replacing with "the evidence suggests"'),
            (r'\bdefinitely\b', 'Consider using more measured language'),
            (r'\babsolutely\b', 'Consider using more qualified statements')
        ]
        
        for pattern, suggestion in subjective_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                enhancements.append(ContentEnhancement(
                    enhancement_type='objectify',
                    priority='medium',
                    suggestion=suggestion,
                    original_text=match.group(),
                    confidence=0.8
                ))
        
        return enhancements


class QualityBenchmarking:
    """Benchmarks research quality against industry standards and peer analysis."""
    
    def __init__(self, data_dir: Path):
        """Initialize quality benchmarking.
        
        Args:
            data_dir: Directory containing research data
        """
        self.data_dir = data_dir
        self.quality_analyzer = ResearchQualityAnalyzer(data_dir)
        self.benchmark_cache = {}
    
    @cached(ttl_seconds=7200)  # Cache for 2 hours
    def generate_quality_benchmark_report(self) -> Dict:
        """Generate comprehensive quality benchmark report.
        
        Returns:
            Detailed benchmarking report
        """
        # Analyze all research documents
        research_dir = self.data_dir / 'research'
        if not research_dir.exists():
            return {'error': 'No research directory found'}
        
        all_metrics = []
        file_metrics = {}
        
        for research_file in research_dir.glob('*.md'):
            try:
                with open(research_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                metrics = self.quality_analyzer.analyze_research_quality(
                    content, research_file.name
                )
                all_metrics.append(metrics)
                file_metrics[research_file.name] = metrics
                
            except Exception as e:
                logger.error(f"Error analyzing {research_file.name}: {e}")
                continue
        
        if not all_metrics:
            return {'error': 'No research documents could be analyzed'}
        
        # Calculate benchmark statistics
        benchmark_stats = self._calculate_benchmark_statistics(all_metrics)
        
        # Identify top performers
        top_performers = self._identify_top_performers(file_metrics)
        
        # Generate improvement recommendations
        improvement_plan = self._generate_system_improvement_plan(all_metrics)
        
        return {
            'generated_at': datetime.now().isoformat(),
            'total_documents_analyzed': len(all_metrics),
            'benchmark_statistics': benchmark_stats,
            'top_performing_documents': top_performers,
            'improvement_recommendations': improvement_plan,
            'quality_trends': self._analyze_quality_trends(file_metrics)
        }
    
    def _calculate_benchmark_statistics(self, metrics_list: List[QualityMetrics]) -> Dict:
        """Calculate benchmark statistics across all metrics."""
        if not metrics_list:
            return {}
        
        # Extract scores for each dimension
        dimensions = [
            'factual_accuracy_score', 'source_credibility_score', 'analysis_depth_score',
            'objectivity_score', 'actionability_score', 'clarity_score',
            'completeness_score', 'timeliness_score', 'overall_quality_score'
        ]
        
        stats = {}
        for dimension in dimensions:
            scores = [getattr(metric, dimension) for metric in metrics_list]
            
            stats[dimension] = {
                'mean': statistics.mean(scores),
                'median': statistics.median(scores),
                'std_dev': statistics.stdev(scores) if len(scores) > 1 else 0,
                'min': min(scores),
                'max': max(scores),
                'percentile_25': statistics.quantiles(scores, n=4)[0] if len(scores) >= 4 else min(scores),
                'percentile_75': statistics.quantiles(scores, n=4)[2] if len(scores) >= 4 else max(scores)
            }
        
        return stats
    
    def _identify_top_performers(self, file_metrics: Dict[str, QualityMetrics], top_n: int = 5) -> List[Dict]:
        """Identify top performing research documents."""
        # Sort by overall quality score
        sorted_files = sorted(
            file_metrics.items(),
            key=lambda x: x[1].overall_quality_score,
            reverse=True
        )
        
        top_performers = []
        for filename, metrics in sorted_files[:top_n]:
            top_performers.append({
                'filename': filename,
                'overall_quality_score': metrics.overall_quality_score,
                'strength_areas': metrics.strength_areas,
                'key_metrics': {
                    'factual_accuracy': metrics.factual_accuracy_score,
                    'source_credibility': metrics.source_credibility_score,
                    'analysis_depth': metrics.analysis_depth_score,
                    'actionability': metrics.actionability_score
                }
            })
        
        return top_performers
    
    def _generate_system_improvement_plan(self, metrics_list: List[QualityMetrics]) -> Dict:
        """Generate system-wide improvement recommendations."""
        # Aggregate all improvement suggestions
        all_suggestions = []
        all_weaknesses = []
        
        for metrics in metrics_list:
            all_suggestions.extend(metrics.improvement_suggestions)
            all_weaknesses.extend(metrics.weakness_areas)
        
        # Count frequency of suggestions and weaknesses
        suggestion_counts = Counter(all_suggestions)
        weakness_counts = Counter(all_weaknesses)
        
        # Calculate average scores by dimension
        avg_scores = {
            'factual_accuracy': statistics.mean(m.factual_accuracy_score for m in metrics_list),
            'source_credibility': statistics.mean(m.source_credibility_score for m in metrics_list),
            'analysis_depth': statistics.mean(m.analysis_depth_score for m in metrics_list),
            'objectivity': statistics.mean(m.objectivity_score for m in metrics_list),
            'actionability': statistics.mean(m.actionability_score for m in metrics_list),
            'clarity': statistics.mean(m.clarity_score for m in metrics_list),
            'completeness': statistics.mean(m.completeness_score for m in metrics_list),
            'timeliness': statistics.mean(m.timeliness_score for m in metrics_list)
        }
        
        # Identify priority improvement areas
        priority_areas = sorted(avg_scores.items(), key=lambda x: x[1])[:3]
        
        return {
            'priority_improvement_areas': [{'area': area, 'avg_score': score} for area, score in priority_areas],
            'most_common_suggestions': dict(suggestion_counts.most_common(5)),
            'most_common_weaknesses': dict(weakness_counts.most_common(5)),
            'overall_system_score': statistics.mean(m.overall_quality_score for m in metrics_list),
            'recommended_actions': self._generate_action_plan(avg_scores, suggestion_counts)
        }
    
    def _generate_action_plan(self, avg_scores: Dict, suggestion_counts: Counter) -> List[str]:
        """Generate specific action plan for quality improvement."""
        actions = []
        
        # Address lowest scoring areas
        lowest_areas = sorted(avg_scores.items(), key=lambda x: x[1])[:2]
        
        for area, score in lowest_areas:
            if score < 0.7:
                if area == 'source_credibility':
                    actions.append("Establish approved source list and citation standards")
                elif area == 'factual_accuracy':
                    actions.append("Implement fact-checking processes and verification requirements")
                elif area == 'analysis_depth':
                    actions.append("Develop analytical framework templates and depth requirements")
                elif area == 'clarity':
                    actions.append("Create writing style guide and readability standards")
        
        # Address most common suggestions
        top_suggestions = suggestion_counts.most_common(2)
        for suggestion, count in top_suggestions:
            if count > len(avg_scores) * 0.3:  # If >30% of documents need this
                actions.append(f"System-wide focus needed: {suggestion}")
        
        return actions
    
    def _analyze_quality_trends(self, file_metrics: Dict[str, QualityMetrics]) -> Dict:
        """Analyze quality trends over time."""
        # Extract dates from filenames and group by time period
        dated_metrics = {}
        
        for filename, metrics in file_metrics.items():
            # Try to extract date from filename
            date_pattern = r'(\d{4})(\d{2})(\d{2})'
            date_match = re.search(date_pattern, filename)
            
            if date_match:
                try:
                    file_date = datetime.strptime(date_match.group(), '%Y%m%d')
                    month_key = file_date.strftime('%Y-%m')
                    
                    if month_key not in dated_metrics:
                        dated_metrics[month_key] = []
                    
                    dated_metrics[month_key].append(metrics)
                except:
                    continue
        
        if len(dated_metrics) < 2:
            return {'note': 'Insufficient temporal data for trend analysis'}
        
        # Calculate monthly averages
        monthly_trends = {}
        for month, month_metrics in dated_metrics.items():
            monthly_trends[month] = {
                'document_count': len(month_metrics),
                'avg_quality_score': statistics.mean(m.overall_quality_score for m in month_metrics),
                'avg_factual_accuracy': statistics.mean(m.factual_accuracy_score for m in month_metrics),
                'avg_source_credibility': statistics.mean(m.source_credibility_score for m in month_metrics)
            }
        
        # Calculate trends
        months = sorted(monthly_trends.keys())
        quality_scores = [monthly_trends[month]['avg_quality_score'] for month in months]
        
        trend_direction = 'improving' if quality_scores[-1] > quality_scores[0] else 'declining'
        
        return {
            'monthly_trends': monthly_trends,
            'trend_direction': trend_direction,
            'quality_change': quality_scores[-1] - quality_scores[0] if len(quality_scores) >= 2 else 0,
            'months_analyzed': len(months)
        }