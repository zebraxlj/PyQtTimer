from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import auto, Enum
from typing import Optional


@dataclass
class SimpleTimer:
    dt_start: Optional[datetime] = None
    dt_stop: Optional[datetime] = None
    dt_pause_start: Optional[datetime] = field(default_factory=datetime.now)
    
    def is_time_up(self) -> bool:
        return datetime.now() >= self.dt_stop

    def ms_passed(self):
        return int((datetime.now() - self.dt_start).total_seconds() * 1000)

    def ms_remain(self):
        return int((self.dt_stop - datetime.now()).total_seconds() * 1000)

    def ms_total(self):
        return int((self.dt_stop - self.dt_start).total_seconds() * 1000)

    def pause(self):
        self.dt_pause_start = datetime.now()
        # print(f'Timer.pause dt_pause_start:{self.dt_pause_start}')

    def reset(self):
        # print(f'Timer.reset')
        ms_total = self.ms_total()
        self.dt_start = datetime.now()
        self.dt_stop = self.dt_start + timedelta(milliseconds=ms_total)

    def resume(self):
        # print(f'Timer.resume dt_end_old:{self.dt_stop}')
        dt_now = datetime.now()
        self.dt_pause_start = dt_now if self.dt_pause_start < self.dt_start else self.dt_pause_start
        timedelta_pause: timedelta = dt_now - self.dt_pause_start
        self.dt_stop += timedelta_pause
        self.dt_start += timedelta_pause
        # print(f'Timer.resume dt_end_new:{self.dt_stop}')

    def sec_remain(self):
        return max(self.ms_remain() // 1000, 0)

    def sec_total(self):
        return max(self.ms_total() // 1000, 0)
