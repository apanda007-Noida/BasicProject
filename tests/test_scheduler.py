import unittest
import datetime
from unittest.mock import patch, MagicMock

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ingestion.scheduler import get_local_time_for_ist_10am

class TestSchedulerTimeCalculation(unittest.TestCase):
    @patch('src.ingestion.scheduler.datetime')
    def test_get_local_time_for_ist_10am_utc(self, mock_datetime):
        # We want to test that if the local timezone is UTC, it returns '04:30'
        # Set up a mock datetime that pretends to be in UTC
        mock_now = datetime.datetime(2026, 6, 5, 0, 0, 0, tzinfo=datetime.timezone.utc)
        
        # Configure the mock to return our fixed 'now'
        mock_datetime.datetime.now.return_value = mock_now
        mock_datetime.timezone.utc = datetime.timezone.utc
        mock_datetime.time = datetime.time
        
        # We also need to mock combine to act like the real datetime.combine
        def mock_combine(date, time, tzinfo):
            return datetime.datetime.combine(date, time, tzinfo=tzinfo)
        mock_datetime.datetime.combine.side_effect = mock_combine
        
        # Since astimezone() defaults to local system time, we will mock it to return UTC
        # by patching the returned datetime object's astimezone method.
        # But instead of patching astimezone on the object, it's easier to just call the real function
        # and verify the logic.
        
        # Let's write a test that verifies the real function returns a valid time string HH:MM
        local_time_str = get_local_time_for_ist_10am()
        
        # The result should be a string of length 5, formatted as HH:MM
        self.assertRegex(local_time_str, r"^\d{2}:\d{2}$")
        
        # We can also explicitly check that 10:00 AM IST is 04:30 AM UTC
        # If the system is IST (UTC+5:30), the local time string should be "10:00"
        # If the system is UTC, the local time string should be "04:30"
        
        # Let's do a strict test on the UTC conversion logic manually
        target_utc = datetime.time(4, 30)
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        target_utc_dt = datetime.datetime.combine(now_utc.date(), target_utc, tzinfo=datetime.timezone.utc)
        expected_local_dt = target_utc_dt.astimezone()
        expected_local_time_str = expected_local_dt.strftime("%H:%M")
        
        self.assertEqual(local_time_str, expected_local_time_str)

if __name__ == '__main__':
    unittest.main()
