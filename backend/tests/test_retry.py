"""Tests for nekonote.retry."""

import pytest

from nekonote.retry import retry


class TestRetry:
    def test_succeeds_first_try(self):
        call_count = 0

        @retry(max_attempts=3)
        def ok():
            nonlocal call_count
            call_count += 1
            return "done"

        assert ok() == "done"
        assert call_count == 1

    def test_retries_on_failure(self):
        call_count = 0

        @retry(max_attempts=3, delay=0)
        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("not yet")
            return "ok"

        assert flaky() == "ok"
        assert call_count == 3

    def test_raises_after_max_attempts(self):
        @retry(max_attempts=2, delay=0)
        def always_fail():
            raise RuntimeError("boom")

        with pytest.raises(RuntimeError, match="boom"):
            always_fail()

    def test_specific_exceptions(self):
        call_count = 0

        @retry(max_attempts=3, delay=0, exceptions=(ValueError,))
        def specific():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("retry this")
            return "ok"

        assert specific() == "ok"
        assert call_count == 2

    def test_non_matching_exception_not_retried(self):
        @retry(max_attempts=3, delay=0, exceptions=(ValueError,))
        def wrong_error():
            raise TypeError("not retried")

        with pytest.raises(TypeError):
            wrong_error()

    def test_backoff(self):
        import time

        times = []

        @retry(max_attempts=3, delay=0.05, backoff=2.0)
        def timed():
            times.append(time.time())
            if len(times) < 3:
                raise ValueError("retry")
            return "ok"

        timed()
        assert len(times) == 3
        # Second delay should be roughly 2x first delay
        gap1 = times[1] - times[0]
        gap2 = times[2] - times[1]
        assert gap2 > gap1 * 1.5  # backoff applied

    def test_preserves_function_name(self):
        @retry(max_attempts=2)
        def my_func():
            pass

        assert my_func.__name__ == "my_func"
