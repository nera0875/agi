"""
Observability - LangSmith tracing + Sentry error tracking
Implements retry patterns and custom error handlers
"""

import logging
import functools
import asyncio
from typing import Any, Callable, Optional, TypeVar, Union
from datetime import datetime

import sentry_sdk
from sentry_sdk import capture_exception, capture_message
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    after_log
)
from langsmith import Client as LangSmithClient
from langsmith.run_helpers import traceable

from config import settings

logger = logging.getLogger(__name__)

# Type variable for decorators
T = TypeVar("T")

# ============================================================================
# LANGSMITH CONFIGURATION
# ============================================================================

# Initialize LangSmith client
langsmith_client = LangSmithClient(
    api_key=settings.langchain_api_key,
    api_url=settings.langchain_endpoint
)

# Verify LangSmith connection
try:
    langsmith_client.list_projects()
    logger.info(f"LangSmith connected - Project: {settings.langchain_project}")
except Exception as e:
    logger.error(f"LangSmith connection failed: {e}")


# ============================================================================
# SENTRY CONFIGURATION
# ============================================================================

if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.sentry_environment,
        traces_sample_rate=1.0 if settings.is_development else 0.1,
        profiles_sample_rate=1.0 if settings.is_development else 0.1,
        enable_tracing=True,
        before_send=lambda event, hint: filter_sensitive_data(event)
    )
    logger.info(f"Sentry initialized - Environment: {settings.sentry_environment}")


def filter_sensitive_data(event: dict) -> dict:
    """
    Filter sensitive data from Sentry events

    Args:
        event: Sentry event dict

    Returns:
        Filtered event
    """
    # Remove sensitive headers
    if "request" in event and "headers" in event["request"]:
        headers = event["request"]["headers"]
        sensitive_headers = ["authorization", "x-api-key", "cookie"]
        for header in sensitive_headers:
            if header in headers:
                headers[header] = "[REDACTED]"

    # Remove API keys from extra context
    if "extra" in event:
        for key in list(event["extra"].keys()):
            if "key" in key.lower() or "token" in key.lower():
                event["extra"][key] = "[REDACTED]"

    return event


# ============================================================================
# RETRY PATTERNS
# ============================================================================

def retry_on_llm_error():
    """
    Retry decorator for LLM API calls

    Returns:
        Tenacity retry decorator configured for LLM errors
    """
    return retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((
            ConnectionError,
            TimeoutError,
            Exception  # Catch API errors
        )),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        after=after_log(logger, logging.INFO)
    )


def retry_on_db_error():
    """
    Retry decorator for database operations

    Returns:
        Tenacity retry decorator configured for DB errors
    """
    return retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=0.5, min=1, max=5),
        retry=retry_if_exception_type((
            ConnectionError,
            TimeoutError
        )),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )


def retry_on_redis_error():
    """
    Retry decorator for Redis operations

    Returns:
        Tenacity retry decorator configured for Redis errors
    """
    return retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=1, max=3),
        retry=retry_if_exception_type((
            ConnectionError,
            TimeoutError
        )),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )


# ============================================================================
# TRACING DECORATORS
# ============================================================================

def trace_llm_call(
    name: Optional[str] = None,
    metadata: Optional[dict] = None,
    tags: Optional[list] = None
):
    """
    Decorator to trace LLM calls with LangSmith

    Args:
        name: Operation name
        metadata: Additional metadata
        tags: Tags for filtering

    Returns:
        Decorated function with LangSmith tracing
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        @traceable(
            name=name or func.__name__,
            metadata=metadata or {},
            tags=tags or ["llm"],
            project_name=settings.langchain_project,
            client=langsmith_client,
            run_type="llm"
        )
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                capture_exception(e)
                logger.error(f"LLM call failed: {func.__name__} - {str(e)}")
                raise

        @functools.wraps(func)
        @traceable(
            name=name or func.__name__,
            metadata=metadata or {},
            tags=tags or ["llm"],
            project_name=settings.langchain_project,
            client=langsmith_client,
            run_type="llm"
        )
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                capture_exception(e)
                logger.error(f"LLM call failed: {func.__name__} - {str(e)}")
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def trace_retrieval(
    name: Optional[str] = None,
    metadata: Optional[dict] = None
):
    """
    Decorator to trace retrieval operations

    Args:
        name: Operation name
        metadata: Additional metadata

    Returns:
        Decorated function with retrieval tracing
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        @traceable(
            name=name or func.__name__,
            metadata=metadata or {},
            tags=["retrieval"],
            project_name=settings.langchain_project,
            client=langsmith_client,
            run_type="retriever"
        )
        async def async_wrapper(*args, **kwargs):
            try:
                start_time = datetime.utcnow()
                result = await func(*args, **kwargs)

                # Log retrieval metrics
                duration = (datetime.utcnow() - start_time).total_seconds()
                # Metrics logging via LangSmith traceable decorator (run_id auto-set)
                # Note: create_feedback called only if run_id available in context

                return result
            except Exception as e:
                capture_exception(e)
                logger.error(f"Retrieval failed: {func.__name__} - {str(e)}")
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return func

    return decorator


def trace_chain(
    name: Optional[str] = None,
    metadata: Optional[dict] = None
):
    """
    Decorator to trace chain/workflow operations

    Args:
        name: Operation name
        metadata: Additional metadata

    Returns:
        Decorated function with chain tracing
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        @traceable(
            name=name or func.__name__,
            metadata=metadata or {},
            tags=["chain"],
            project_name=settings.langchain_project,
            client=langsmith_client,
            run_type="chain"
        )
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                capture_exception(e)
                logger.error(f"Chain failed: {func.__name__} - {str(e)}")
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return func

    return decorator


# ============================================================================
# ERROR HANDLERS
# ============================================================================

class ErrorHandler:
    """
    Centralized error handling with Sentry integration
    """

    @staticmethod
    def handle_llm_error(error: Exception, context: dict = None):
        """
        Handle LLM-related errors

        Args:
            error: Exception object
            context: Additional context
        """
        sentry_sdk.capture_exception(
            error,
            extra={
                "error_type": "llm_error",
                "context": context or {}
            }
        )

        logger.error(f"LLM Error: {str(error)}", exc_info=True)

        # Determine if retryable
        retryable_errors = [
            "rate_limit",
            "timeout",
            "connection",
            "server_error"
        ]

        error_str = str(error).lower()
        is_retryable = any(err in error_str for err in retryable_errors)

        if is_retryable:
            logger.info("Error is retryable, will attempt retry")
            raise error  # Let retry decorator handle
        else:
            logger.error("Error is not retryable")
            raise

    @staticmethod
    def handle_retrieval_error(error: Exception, query: str = None):
        """
        Handle retrieval/memory errors

        Args:
            error: Exception object
            query: Query that failed
        """
        sentry_sdk.capture_exception(
            error,
            extra={
                "error_type": "retrieval_error",
                "query": query
            }
        )

        logger.error(f"Retrieval Error for query '{query}': {str(error)}", exc_info=True)

    @staticmethod
    def handle_database_error(error: Exception, operation: str = None):
        """
        Handle database errors

        Args:
            error: Exception object
            operation: Database operation that failed
        """
        sentry_sdk.capture_exception(
            error,
            extra={
                "error_type": "database_error",
                "operation": operation
            }
        )

        logger.error(f"Database Error during {operation}: {str(error)}", exc_info=True)


# ============================================================================
# MONITORING UTILITIES
# ============================================================================

class PerformanceMonitor:
    """
    Performance monitoring utilities
    """

    @staticmethod
    def track_latency(operation_name: str):
        """
        Decorator to track operation latency

        Args:
            operation_name: Name of operation

        Returns:
            Decorated function
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = datetime.utcnow()

                try:
                    result = await func(*args, **kwargs)
                    duration = (datetime.utcnow() - start_time).total_seconds()

                    # Log to LangSmith si un run_id explicite est fourni
                    run_id = kwargs.get("run_id")
                    if run_id is None and args:
                        run_id = getattr(args[0], "run_id", None)
                    if run_id:
                        try:
                            langsmith_client.create_feedback(
                                run_id=run_id,
                                key=f"{operation_name}_latency",
                                score=duration
                            )
                        except Exception as e:
                            logger.debug(
                                "LangSmith feedback skipped (%s): %s",
                                operation_name,
                                e
                            )

                    # Log to Sentry (as breadcrumb)
                    sentry_sdk.add_breadcrumb(
                        category="performance",
                        message=f"{operation_name} completed",
                        data={"duration": duration},
                        level="info"
                    )

                    if duration > 5:  # Warn if slow
                        logger.warning(f"{operation_name} took {duration:.2f}s")

                    return result

                except Exception as e:
                    duration = (datetime.utcnow() - start_time).total_seconds()
                    logger.error(f"{operation_name} failed after {duration:.2f}s")
                    raise

            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            return func

        return decorator

    @staticmethod
    async def health_check() -> dict:
        """
        Check observability services health

        Returns:
            Health status dict
        """
        status = {
            "langsmith": False,
            "sentry": False
        }

        # Check LangSmith
        try:
            langsmith_client.list_projects()
            status["langsmith"] = True
        except Exception as e:
            logger.error(f"LangSmith health check failed: {e}")

        # Check Sentry
        try:
            capture_message("Health check", level="info")
            status["sentry"] = True
        except Exception as e:
            logger.error(f"Sentry health check failed: {e}")

        return status


# ============================================================================
# CIRCUIT BREAKER
# ============================================================================

class CircuitBreaker:
    """
    Circuit breaker pattern for external services
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open

    def call(self, func: Callable, *args, **kwargs):
        """
        Call function with circuit breaker protection

        Args:
            func: Function to call
            args: Function arguments
            kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            Exception: If circuit is open
        """
        if self.state == "open":
            if self._should_attempt_reset():
                self.state = "half-open"
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        """Handle successful call"""
        self.failure_count = 0
        self.state = "closed"

    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()

        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.error(f"Circuit breaker OPEN after {self.failure_count} failures")
            try:
                capture_message(
                    f"Circuit breaker opened (failures={self.failure_count})",
                    level="error"
                )
            except Exception as e:
                logger.debug("Sentry capture_message skipped: %s", e)

    def _should_attempt_reset(self) -> bool:
        """Check if should attempt reset"""
        if self.last_failure_time:
            time_since_failure = (datetime.utcnow() - self.last_failure_time).total_seconds()
            return time_since_failure >= self.recovery_timeout
        return False


# Global instances
error_handler = ErrorHandler()
performance_monitor = PerformanceMonitor()

# Circuit breakers for external services
llm_circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)
embedding_circuit_breaker = CircuitBreaker(failure_threshold=10, recovery_timeout=30)
rerank_circuit_breaker = CircuitBreaker(failure_threshold=10, recovery_timeout=30)
