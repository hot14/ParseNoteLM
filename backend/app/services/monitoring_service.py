"""
성능 모니터링 서비스 모듈
"""

import time
import psutil
import logging
from typing import Dict, Any, Optional
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from functools import wraps
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Prometheus 메트릭 정의
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration', ['method', 'endpoint'])
ACTIVE_CONNECTIONS = Gauge('active_connections', 'Number of active connections')
SYSTEM_CPU_USAGE = Gauge('system_cpu_usage_percent', 'System CPU usage percentage')
SYSTEM_MEMORY_USAGE = Gauge('system_memory_usage_percent', 'System memory usage percentage')
SYSTEM_DISK_USAGE = Gauge('system_disk_usage_percent', 'System disk usage percentage')
VIDEO_PROCESSING_TIME = Histogram('video_processing_duration_seconds', 'Video processing duration')
VIDEO_PROCESSING_COUNT = Counter('video_processing_total', 'Total video processing requests', ['status'])

class PerformanceMonitor:
    """성능 모니터링 클래스"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.request_stats = {}
        self.video_processing_stats = {}
        
    def track_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """HTTP 요청 추적"""
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=str(status_code)).inc()
        REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)
        
        # 내부 통계 업데이트
        key = f"{method}:{endpoint}"
        if key not in self.request_stats:
            self.request_stats[key] = {
                'count': 0,
                'total_duration': 0,
                'avg_duration': 0,
                'min_duration': float('inf'),
                'max_duration': 0,
                'error_count': 0
            }
        
        stats = self.request_stats[key]
        stats['count'] += 1
        stats['total_duration'] += duration
        stats['avg_duration'] = stats['total_duration'] / stats['count']
        stats['min_duration'] = min(stats['min_duration'], duration)
        stats['max_duration'] = max(stats['max_duration'], duration)
        
        if status_code >= 400:
            stats['error_count'] += 1
    
    def track_video_processing(self, duration: float, status: str, file_size: Optional[int] = None):
        """비디오 처리 추적"""
        VIDEO_PROCESSING_TIME.observe(duration)
        VIDEO_PROCESSING_COUNT.labels(status=status).inc()
        
        # 내부 통계 업데이트
        if 'video_processing' not in self.video_processing_stats:
            self.video_processing_stats['video_processing'] = {
                'count': 0,
                'total_duration': 0,
                'avg_duration': 0,
                'min_duration': float('inf'),
                'max_duration': 0,
                'success_count': 0,
                'error_count': 0,
                'total_file_size': 0
            }
        
        stats = self.video_processing_stats['video_processing']
        stats['count'] += 1
        stats['total_duration'] += duration
        stats['avg_duration'] = stats['total_duration'] / stats['count']
        stats['min_duration'] = min(stats['min_duration'], duration)
        stats['max_duration'] = max(stats['max_duration'], duration)
        
        if status == 'success':
            stats['success_count'] += 1
        else:
            stats['error_count'] += 1
            
        if file_size:
            stats['total_file_size'] += file_size
    
    def update_system_metrics(self):
        """시스템 메트릭 업데이트"""
        try:
            # CPU 사용률
            cpu_percent = psutil.cpu_percent(interval=1)
            SYSTEM_CPU_USAGE.set(cpu_percent)
            
            # 메모리 사용률
            memory = psutil.virtual_memory()
            SYSTEM_MEMORY_USAGE.set(memory.percent)
            
            # 디스크 사용률
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            SYSTEM_DISK_USAGE.set(disk_percent)
            
            logger.debug(f"System metrics updated - CPU: {cpu_percent}%, Memory: {memory.percent}%, Disk: {disk_percent}%")
            
        except Exception as e:
            logger.error(f"시스템 메트릭 업데이트 실패: {e}")
    
    def get_system_info(self) -> Dict[str, Any]:
        """시스템 정보 조회"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'cpu': {
                    'usage_percent': cpu_percent,
                    'count': psutil.cpu_count()
                },
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'used': memory.used,
                    'usage_percent': memory.percent
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'usage_percent': (disk.used / disk.total) * 100
                },
                'uptime': str(datetime.now() - self.start_time)
            }
        except Exception as e:
            logger.error(f"시스템 정보 조회 실패: {e}")
            return {}
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """성능 통계 조회"""
        return {
            'request_stats': self.request_stats,
            'video_processing_stats': self.video_processing_stats,
            'system_info': self.get_system_info(),
            'uptime': str(datetime.now() - self.start_time)
        }
    
    def get_prometheus_metrics(self) -> str:
        """Prometheus 메트릭 반환"""
        self.update_system_metrics()
        return generate_latest()

# 전역 모니터 인스턴스
performance_monitor = PerformanceMonitor()

def monitor_request(func):
    """HTTP 요청 모니터링 데코레이터"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        method = "UNKNOWN"
        endpoint = func.__name__
        status_code = 200
        
        try:
            # FastAPI Request 객체에서 정보 추출
            if args and hasattr(args[0], 'method'):
                method = args[0].method
                endpoint = str(args[0].url.path)
            
            result = await func(*args, **kwargs)
            return result
            
        except Exception as e:
            status_code = 500
            logger.error(f"Request monitoring error: {e}")
            raise
            
        finally:
            duration = time.time() - start_time
            performance_monitor.track_request(method, endpoint, status_code, duration)
    
    return wrapper

def monitor_video_processing(func):
    """비디오 처리 모니터링 데코레이터"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        status = "success"
        file_size = None
        
        try:
            result = await func(*args, **kwargs)
            
            # 결과에서 파일 크기 추출 시도
            if isinstance(result, dict) and 'file_size' in result:
                file_size = result['file_size']
                
            return result
            
        except Exception as e:
            status = "error"
            logger.error(f"Video processing monitoring error: {e}")
            raise
            
        finally:
            duration = time.time() - start_time
            performance_monitor.track_video_processing(duration, status, file_size)
    
    return wrapper

