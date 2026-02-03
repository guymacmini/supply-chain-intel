"""Asynchronous research engine for improved performance and concurrent operations."""

import asyncio
import aiohttp
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
import logging

from .performance_optimizer import timed, cached, AsyncExecutor, BatchProcessor
from .finnhub_client import FinnhubClient
from .tavily_client import TavilyClient
from ..agents.explore_agent import ExploreAgent

logger = logging.getLogger(__name__)


@dataclass
class ResearchTask:
    """Represents a research task to be processed asynchronously."""
    task_id: str
    query: str
    depth: int = 2
    tickers: List[str] = None
    priority: int = 0  # Higher values = higher priority
    callback: Optional[Callable] = None
    
    def __post_init__(self):
        if self.tickers is None:
            self.tickers = []


@dataclass
class ResearchResult:
    """Result of an asynchronous research operation."""
    task_id: str
    success: bool
    result: Optional[Dict] = None
    error: Optional[str] = None
    duration: float = 0.0
    generated_at: str = None
    
    def __post_init__(self):
        if self.generated_at is None:
            self.generated_at = datetime.now().isoformat()


class AsyncResearchEngine:
    """High-performance asynchronous research engine."""
    
    def __init__(self, data_dir: Path, max_workers: int = 8, 
                 enable_caching: bool = True):
        """Initialize async research engine.
        
        Args:
            data_dir: Data directory for outputs and caching
            max_workers: Maximum concurrent workers
            enable_caching: Whether to enable result caching
        """
        self.data_dir = data_dir
        self.max_workers = max_workers
        self.enable_caching = enable_caching
        
        # Initialize async components
        self.executor = AsyncExecutor(max_workers)
        self.batch_processor = BatchProcessor(batch_size=5, max_workers=max_workers)
        
        # Initialize research agents and clients
        self.explore_agent = ExploreAgent(data_dir)
        
        # Task queue and results
        self.pending_tasks: List[ResearchTask] = []
        self.completed_results: Dict[str, ResearchResult] = {}
        self.active_tasks: Dict[str, asyncio.Task] = {}
        
        # Performance tracking
        self.stats = {
            'tasks_completed': 0,
            'tasks_failed': 0,
            'total_duration': 0.0,
            'cache_hits': 0,
            'cache_misses': 0
        }
    
    async def submit_research_task(self, task: ResearchTask) -> str:
        """Submit a research task for async processing.
        
        Args:
            task: Research task to submit
            
        Returns:
            Task ID for tracking
        """
        self.pending_tasks.append(task)
        
        # Start processing if not at capacity
        if len(self.active_tasks) < self.max_workers:
            await self._process_next_task()
        
        return task.task_id
    
    async def submit_bulk_research(self, queries: List[str], 
                                 depth: int = 2) -> List[str]:
        """Submit multiple research queries for batch processing.
        
        Args:
            queries: List of research queries
            depth: Research depth for all queries
            
        Returns:
            List of task IDs
        """
        tasks = []
        task_ids = []
        
        for i, query in enumerate(queries):
            task_id = f"bulk_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i:03d}"
            task = ResearchTask(
                task_id=task_id,
                query=query,
                depth=depth,
                priority=1  # Bulk tasks get normal priority
            )
            tasks.append(task)
            task_ids.append(task_id)
        
        # Add to pending queue
        self.pending_tasks.extend(tasks)
        
        # Process tasks in batches
        await self._process_pending_tasks()
        
        return task_ids
    
    async def get_research_result(self, task_id: str, 
                                wait: bool = True, 
                                timeout: float = 300) -> Optional[ResearchResult]:
        """Get result for a specific research task.
        
        Args:
            task_id: Task ID to get result for
            wait: Whether to wait for completion
            timeout: Maximum wait time in seconds
            
        Returns:
            ResearchResult or None if not found/timeout
        """
        if task_id in self.completed_results:
            return self.completed_results[task_id]
        
        if not wait:
            return None
        
        # Wait for completion
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            if task_id in self.completed_results:
                return self.completed_results[task_id]
            
            if task_id in self.active_tasks:
                try:
                    await asyncio.wait_for(self.active_tasks[task_id], timeout=1.0)
                except asyncio.TimeoutError:
                    continue
                except Exception:
                    break
            
            await asyncio.sleep(0.1)
        
        return None
    
    async def wait_for_all_tasks(self, timeout: float = 600) -> Dict[str, ResearchResult]:
        """Wait for all pending and active tasks to complete.
        
        Args:
            timeout: Maximum wait time in seconds
            
        Returns:
            Dictionary of all completed results
        """
        start_time = asyncio.get_event_loop().time()
        
        while (self.pending_tasks or self.active_tasks) and \
              (asyncio.get_event_loop().time() - start_time < timeout):
            
            # Process pending tasks
            await self._process_pending_tasks()
            
            # Wait for active tasks
            if self.active_tasks:
                done, pending = await asyncio.wait(
                    list(self.active_tasks.values()),
                    timeout=1.0,
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                # Clean up completed tasks
                for task in done:
                    task_id = None
                    for tid, active_task in list(self.active_tasks.items()):
                        if active_task == task:
                            task_id = tid
                            break
                    
                    if task_id:
                        del self.active_tasks[task_id]
            
            await asyncio.sleep(0.1)
        
        return dict(self.completed_results)
    
    @timed('async_research_execution')
    @cached(ttl_seconds=3600)  # Cache results for 1 hour
    async def _execute_research_task(self, task: ResearchTask) -> ResearchResult:
        """Execute a single research task asynchronously.
        
        Args:
            task: Research task to execute
            
        Returns:
            ResearchResult with outcome
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Execute research using thread pool to avoid blocking
            result = await self.executor.run_in_thread(
                self._sync_research_execution,
                task
            )
            
            duration = asyncio.get_event_loop().time() - start_time
            
            # Update stats
            self.stats['tasks_completed'] += 1
            self.stats['total_duration'] += duration
            
            return ResearchResult(
                task_id=task.task_id,
                success=True,
                result=result,
                duration=duration
            )
            
        except Exception as e:
            duration = asyncio.get_event_loop().time() - start_time
            self.stats['tasks_failed'] += 1
            
            logger.error(f"Research task {task.task_id} failed: {str(e)}")
            
            return ResearchResult(
                task_id=task.task_id,
                success=False,
                error=str(e),
                duration=duration
            )
    
    def _sync_research_execution(self, task: ResearchTask) -> Dict:
        """Synchronous research execution (runs in thread pool).
        
        Args:
            task: Research task to execute
            
        Returns:
            Research result dictionary
        """
        # Execute the research using the existing ExploreAgent
        result = self.explore_agent.explore(
            query=task.query,
            depth=task.depth,
            use_cache=self.enable_caching
        )
        
        return {
            'query': task.query,
            'depth': task.depth,
            'content': result,
            'tickers': task.tickers,
            'timestamp': datetime.now().isoformat()
        }
    
    async def _process_next_task(self) -> None:
        """Process the next pending task if workers are available."""
        if not self.pending_tasks or len(self.active_tasks) >= self.max_workers:
            return
        
        # Sort by priority (highest first)
        self.pending_tasks.sort(key=lambda t: t.priority, reverse=True)
        task = self.pending_tasks.pop(0)
        
        # Start async task
        async_task = asyncio.create_task(self._execute_research_task(task))
        self.active_tasks[task.task_id] = async_task
        
        # Set up completion callback
        async_task.add_done_callback(
            lambda t: asyncio.create_task(self._on_task_completed(task.task_id, t))
        )
    
    async def _process_pending_tasks(self) -> None:
        """Process all pending tasks up to worker limit."""
        while self.pending_tasks and len(self.active_tasks) < self.max_workers:
            await self._process_next_task()
    
    async def _on_task_completed(self, task_id: str, async_task: asyncio.Task) -> None:
        """Handle task completion.
        
        Args:
            task_id: ID of completed task
            async_task: Completed asyncio task
        """
        try:
            result = await async_task
            self.completed_results[task_id] = result
            
            # Execute callback if provided
            if hasattr(result, 'callback') and result.callback:
                try:
                    result.callback(result)
                except Exception as e:
                    logger.error(f"Callback for task {task_id} failed: {e}")
            
        except Exception as e:
            logger.error(f"Task {task_id} completion handling failed: {e}")
            self.completed_results[task_id] = ResearchResult(
                task_id=task_id,
                success=False,
                error=str(e)
            )
        finally:
            # Remove from active tasks
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
            
            # Process next task if available
            await self._process_next_task()
    
    async def get_parallel_market_data(self, tickers: List[str]) -> Dict[str, Any]:
        """Get market data for multiple tickers in parallel.
        
        Args:
            tickers: List of ticker symbols
            
        Returns:
            Dictionary mapping tickers to market data
        """
        async def fetch_ticker_data(ticker: str) -> tuple[str, Dict]:
            try:
                # Run in thread pool to avoid blocking
                data = await self.executor.run_in_thread(
                    self._get_ticker_data_sync, ticker
                )
                return ticker, data
            except Exception as e:
                logger.error(f"Failed to fetch data for {ticker}: {e}")
                return ticker, {'error': str(e)}
        
        # Create tasks for all tickers
        tasks = [fetch_ticker_data(ticker) for ticker in tickers]
        
        # Execute in parallel with limit
        results = await self.executor.gather_with_limit(tasks, limit=10)
        
        return dict(results)
    
    def _get_ticker_data_sync(self, ticker: str) -> Dict:
        """Synchronous ticker data retrieval."""
        # Use existing FinnhubClient
        client = FinnhubClient()
        return {
            'quote': client.get_quote(ticker),
            'profile': client.get_company_profile(ticker)
        }
    
    async def parallel_web_research(self, queries: List[str], 
                                  max_results: int = 5) -> Dict[str, Any]:
        """Perform web research for multiple queries in parallel.
        
        Args:
            queries: List of search queries
            max_results: Maximum results per query
            
        Returns:
            Dictionary mapping queries to search results
        """
        async def search_query(query: str) -> tuple[str, Dict]:
            try:
                # Use thread pool for web requests
                results = await self.executor.run_in_thread(
                    self._web_search_sync, query, max_results
                )
                return query, results
            except Exception as e:
                logger.error(f"Web search failed for '{query}': {e}")
                return query, {'error': str(e)}
        
        # Create search tasks
        search_tasks = [search_query(query) for query in queries]
        
        # Execute with concurrency limit
        results = await self.executor.gather_with_limit(search_tasks, limit=5)
        
        return dict(results)
    
    def _web_search_sync(self, query: str, max_results: int) -> Dict:
        """Synchronous web search."""
        # Use existing TavilyClient
        client = TavilyClient()
        return client.search(query, max_results=max_results)
    
    async def batch_analyze_documents(self, file_paths: List[Path],
                                    analyzer_func: Callable) -> List[Any]:
        """Analyze multiple documents in batches for performance.
        
        Args:
            file_paths: List of document paths to analyze
            analyzer_func: Function to analyze each document
            
        Returns:
            List of analysis results
        """
        def process_batch(batch_paths: List[Path]) -> List[Any]:
            results = []
            for path in batch_paths:
                try:
                    if path.exists():
                        with open(path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        result = analyzer_func(content, str(path))
                        results.append(result)
                    else:
                        results.append({'error': 'File not found', 'path': str(path)})
                except Exception as e:
                    results.append({'error': str(e), 'path': str(path)})
            return results
        
        # Process in batches
        batch_results = await self.batch_processor.process_batches(
            file_paths, process_batch
        )
        
        # Flatten results
        all_results = []
        for batch_result in batch_results:
            all_results.extend(batch_result)
        
        return all_results
    
    def get_performance_stats(self) -> Dict:
        """Get performance statistics for the async engine.
        
        Returns:
            Dictionary with performance metrics
        """
        total_tasks = self.stats['tasks_completed'] + self.stats['tasks_failed']
        avg_duration = (
            self.stats['total_duration'] / self.stats['tasks_completed'] 
            if self.stats['tasks_completed'] > 0 else 0
        )
        
        return {
            'total_tasks_processed': total_tasks,
            'successful_tasks': self.stats['tasks_completed'],
            'failed_tasks': self.stats['tasks_failed'],
            'success_rate': (
                self.stats['tasks_completed'] / total_tasks * 100 
                if total_tasks > 0 else 0
            ),
            'average_task_duration': avg_duration,
            'total_processing_time': self.stats['total_duration'],
            'pending_tasks': len(self.pending_tasks),
            'active_tasks': len(self.active_tasks),
            'completed_results': len(self.completed_results),
            'cache_hit_rate': (
                self.stats['cache_hits'] / 
                (self.stats['cache_hits'] + self.stats['cache_misses']) * 100
                if (self.stats['cache_hits'] + self.stats['cache_misses']) > 0 else 0
            )
        }
    
    def clear_completed_results(self, keep_recent: int = 100) -> int:
        """Clear old completed results to free memory.
        
        Args:
            keep_recent: Number of recent results to keep
            
        Returns:
            Number of results cleared
        """
        if len(self.completed_results) <= keep_recent:
            return 0
        
        # Sort by completion time and keep most recent
        sorted_results = sorted(
            self.completed_results.items(),
            key=lambda x: x[1].generated_at,
            reverse=True
        )
        
        results_to_keep = dict(sorted_results[:keep_recent])
        cleared_count = len(self.completed_results) - len(results_to_keep)
        
        self.completed_results = results_to_keep
        return cleared_count
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the async research engine."""
        logger.info("Shutting down async research engine...")
        
        # Cancel pending tasks
        self.pending_tasks.clear()
        
        # Wait for active tasks to complete (with timeout)
        if self.active_tasks:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*self.active_tasks.values(), return_exceptions=True),
                    timeout=30.0
                )
            except asyncio.TimeoutError:
                logger.warning("Some tasks did not complete within shutdown timeout")
        
        # Close executor
        self.executor.close()
        
        logger.info("Async research engine shutdown complete")


class ResearchWorkflowManager:
    """Manages complex research workflows with dependencies and priorities."""
    
    def __init__(self, async_engine: AsyncResearchEngine):
        """Initialize workflow manager.
        
        Args:
            async_engine: Async research engine instance
        """
        self.engine = async_engine
        self.workflows = {}
        self.workflow_results = {}
    
    async def create_sector_analysis_workflow(self, sector: str, 
                                            companies: List[str]) -> str:
        """Create a comprehensive sector analysis workflow.
        
        Args:
            sector: Sector to analyze
            companies: List of companies in the sector
            
        Returns:
            Workflow ID for tracking
        """
        workflow_id = f"sector_{sector}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create research tasks for the workflow
        tasks = []
        
        # 1. Sector overview task (high priority)
        sector_task = ResearchTask(
            task_id=f"{workflow_id}_overview",
            query=f"{sector} sector analysis and market trends",
            depth=3,
            priority=10
        )
        tasks.append(sector_task)
        
        # 2. Individual company analysis tasks (medium priority)
        for i, company in enumerate(companies[:10]):  # Limit to 10 companies
            company_task = ResearchTask(
                task_id=f"{workflow_id}_company_{i:02d}",
                query=f"{company} financial analysis and investment outlook",
                depth=2,
                tickers=[company] if len(company) <= 5 else [],  # Assume ticker if short
                priority=5
            )
            tasks.append(company_task)
        
        # 3. Competitive analysis task (low priority)
        comp_task = ResearchTask(
            task_id=f"{workflow_id}_competitive",
            query=f"{sector} competitive landscape and market leaders",
            depth=2,
            priority=3
        )
        tasks.append(comp_task)
        
        # Submit all tasks
        task_ids = []
        for task in tasks:
            task_id = await self.engine.submit_research_task(task)
            task_ids.append(task_id)
        
        self.workflows[workflow_id] = {
            'type': 'sector_analysis',
            'sector': sector,
            'companies': companies,
            'task_ids': task_ids,
            'created_at': datetime.now().isoformat(),
            'status': 'running'
        }
        
        return workflow_id
    
    async def get_workflow_status(self, workflow_id: str) -> Dict:
        """Get status of a workflow.
        
        Args:
            workflow_id: Workflow ID to check
            
        Returns:
            Workflow status information
        """
        if workflow_id not in self.workflows:
            return {'error': 'Workflow not found'}
        
        workflow = self.workflows[workflow_id]
        task_ids = workflow['task_ids']
        
        # Check task completion status
        completed_tasks = []
        pending_tasks = []
        
        for task_id in task_ids:
            if task_id in self.engine.completed_results:
                completed_tasks.append(task_id)
            else:
                pending_tasks.append(task_id)
        
        completion_percentage = len(completed_tasks) / len(task_ids) * 100
        
        status = 'completed' if len(pending_tasks) == 0 else 'running'
        
        return {
            'workflow_id': workflow_id,
            'type': workflow['type'],
            'status': status,
            'completion_percentage': completion_percentage,
            'completed_tasks': len(completed_tasks),
            'pending_tasks': len(pending_tasks),
            'total_tasks': len(task_ids),
            'created_at': workflow['created_at']
        }
    
    async def wait_for_workflow(self, workflow_id: str, 
                              timeout: float = 1800) -> Optional[Dict]:
        """Wait for workflow to complete.
        
        Args:
            workflow_id: Workflow ID to wait for
            timeout: Maximum wait time in seconds
            
        Returns:
            Workflow results or None on timeout
        """
        if workflow_id not in self.workflows:
            return None
        
        workflow = self.workflows[workflow_id]
        task_ids = workflow['task_ids']
        
        # Wait for all tasks to complete
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            # Check if all tasks are complete
            all_complete = all(
                task_id in self.engine.completed_results 
                for task_id in task_ids
            )
            
            if all_complete:
                # Compile workflow results
                results = {}
                for task_id in task_ids:
                    results[task_id] = self.engine.completed_results[task_id]
                
                self.workflow_results[workflow_id] = results
                self.workflows[workflow_id]['status'] = 'completed'
                
                return results
            
            await asyncio.sleep(1.0)
        
        return None  # Timeout
    
    def get_workflow_results(self, workflow_id: str) -> Optional[Dict]:
        """Get compiled results for a completed workflow.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            Workflow results or None if not found/incomplete
        """
        return self.workflow_results.get(workflow_id)