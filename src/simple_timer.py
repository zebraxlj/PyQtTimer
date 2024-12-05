from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import auto, Enum
from typing import Optional


@dataclass
class SimpleTimer:
    dt_start: Optional[datetime] = None
    dt_stop: Optional[datetime] = None
    dt_pause_start: Optional[datetime] = field(default_factory=datetime.now)

    def is_time_set(self) -> bool:
        return self.dt_start is not None and self.dt_stop is not None

    def is_time_up(self) -> bool:
        if not self.is_time_set():
            return False
        return datetime.now() >= self.dt_stop

    def ms_passed(self) -> int:
        if not self.is_time_set():
            return 0
        return int((datetime.now() - self.dt_start).total_seconds() * 1000)

    def ms_remain(self) -> int:
        if not self.is_time_set():
            return 0
        return int((self.dt_stop - datetime.now()).total_seconds() * 1000)

    def ms_total(self) -> int:
        if not self.is_time_set():
            return 0
        return int((self.dt_stop - self.dt_start).total_seconds() * 1000)

    def pause(self) -> None:
        if not self.is_time_set():
            return
        self.dt_pause_start = datetime.now()
        # print(f'Timer.pause dt_pause_start:{self.dt_pause_start}')

    def reset(self) -> None:
        # print(f'Timer.reset')
        if not self.is_time_set():
            return
        ms_total = self.ms_total()
        self.dt_start = datetime.now()
        self.dt_stop = self.dt_start + timedelta(milliseconds=ms_total)

    def resume(self) -> None:
        # print(f'Timer.resume dt_end_old:{self.dt_stop}')
        if not self.is_time_set():
            return
        dt_now = datetime.now()
        self.dt_pause_start = dt_now if self.dt_pause_start < self.dt_start else self.dt_pause_start
        timedelta_pause: timedelta = dt_now - self.dt_pause_start
        self.dt_stop += timedelta_pause
        self.dt_start += timedelta_pause
        # print(f'Timer.resume dt_end_new:{self.dt_stop}')

    def sec_remain(self):
        if not self.is_time_set():
            return 0
        return max(self.ms_remain() // 1000, 0)

    def sec_total(self):
        if not self.is_time_set():
            return 0
        return max(self.ms_total() // 1000, 0)
