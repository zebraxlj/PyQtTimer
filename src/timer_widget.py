import os
import platform
import sys
from datetime import datetime, timedelta
from enum import Enum, auto
from functools import partial
from PyQt5.QtCore import Qt, QEvent, QSize, QTimer, QObject
from PyQt5.QtGui import QColor, QFont, QIcon, QIntValidator, QPalette, QKeyEvent, QKeySequence, QMouseEvent, QWheelEvent
from PyQt5.QtWidgets import (
    QApplication, QWidget,
    QFrame, QHBoxLayout, QVBoxLayout,
    QLabel, QLayout, QLineEdit, QProgressBar, QPushButton
    )

from simple_timer import SimpleTimer

FONT_CN = 'Microsoft YaHei'


def resource_path(relative_path):
    """Get the absolute path to a resource."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, f'./{relative_path}')
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), f'../{relative_path}')

# 使用这个函数来获取图片路径
RES_FOLDER = resource_path('res/')


ICON_CLEAR = f'{RES_FOLDER}trash.png'
ICON_START = f'{RES_FOLDER}play-circle.png'
ICON_PAUSE = f'{RES_FOLDER}pause-circle.png'
ICON_RESET = f'{RES_FOLDER}rotate-left.png'
ICON_TOMATO = f'{RES_FOLDER}pomodoro-icon.png'

COLOR_WINDOW_BG = QColor('white')
COLOR_WINDOW_BG_ALARM = QColor('mistyrose')


class DispModeEnum(Enum):
    CLEAN = auto()
    FULL = auto()


class TimerCtrlStateEnum(str, Enum):
    PAUSE = 'Pause'
    RESUME = 'Resume'
    START = 'Start'
    UNKNOWN = ''
    NA = 'NA'


class TimerCtrlButton(QPushButton):
    def __init__(self, ctrl_state = TimerCtrlStateEnum.UNKNOWN, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.curr_state: TimerCtrlStateEnum = ctrl_state

    def set_curr_state(self, state: TimerCtrlStateEnum) -> None:
        self.curr_state = state
        if state in {TimerCtrlStateEnum.START, TimerCtrlStateEnum.RESUME}:
            self.setIcon(QIcon(ICON_START))
        elif state == TimerCtrlStateEnum.PAUSE:
            self.setIcon(QIcon(ICON_PAUSE))


class TimerNumberLineEdit(QLineEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setReadOnly(True)
        self.__is_edit_allowed: bool = True

    def refresh_display(self):
        if not self.__is_edit_allowed:
            self.clearFocus()

    @property
    def is_edit_allowed(self) -> bool:
        return self.__is_edit_allowed

    @is_edit_allowed.setter
    def is_edit_allowed(self, is_allowed: bool) -> None:
        self.__is_edit_allowed = is_allowed
        self.refresh_display()

    def changeEvent(self, event: QEvent):
        super().changeEvent(event)
        if event.type() in (event.Type.FontChange, event.Type.StyleChange):
            self.updateGeometry()

    def sizeHint(self):
        hint = super().sizeHint()
        charWidth = self.fontMetrics().horizontalAdvance('0')
        width_prefered = int((charWidth * 2 * 1.25 + 10))
        hint.setWidth(width_prefered)
        self.setMaximumWidth(width_prefered)
        self.setMinimumWidth(width_prefered)
        return hint

    def contextMenuEvent(self, event):
        # 禁用右键菜单，不调用父类的 contextMenuEvent，
        pass

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in {Qt.Key.Key_Shift, Qt.Key.Key_Control, Qt.Key.Key_Alt}:
            print(f'TimerNumberLineEdit.handle_key_press {QKeySequence(event.key())}')
        else:
            print(f'TimerNumberLineEdit.handle_key_press {QKeySequence(event.key()).toString(QKeySequence.SequenceFormat.NativeText)}')

        if not self.is_edit_allowed:
            self.refresh_display()
        elif event.key() == Qt.Key.Key_Escape:
            self.clearFocus()
        elif event.key() in {
            Qt.Key.Key_0, Qt.Key.Key_1, Qt.Key.Key_2, Qt.Key.Key_3, Qt.Key.Key_4,
            Qt.Key.Key_5, Qt.Key.Key_6, Qt.Key.Key_7, Qt.Key.Key_8, Qt.Key.Key_9,
            }:
            text = f'{self.text()}{chr(event.key())}'[-2:]
            self.setReadOnly(False)
            self.setText(f'{text:02}')
            self.setReadOnly(True)
        elif event.key() == Qt.Key.Key_Backspace:
            text = self.text()[:-1]
            self.setReadOnly(False)
            self.setText(f'{int(text):02}')
            self.setReadOnly(True)
            return

    def mouseDoubleClickEvent(self, a0: QMouseEvent) -> None:
        # print(f'TimerNumberLineEdit.mouseDoubleClickEvent {self.is_edit_allowed}')
        self.refresh_display()
        return

    def mousePressEvent(self, event: QMouseEvent) -> None:
        print(f'TimerNumberLineEdit.mousePressEvent {self.is_edit_allowed}')
        self.refresh_display()
        if self.is_edit_allowed and event.button() == Qt.MouseButton.LeftButton:
            self.setFocus()
        elif self.is_edit_allowed and event.button() == Qt.MouseButton.RightButton:
            self.setFocus()


class TimerAddTimeButton(QPushButton):
    def __init__(self, second: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setText(f'±{self.text()}')
        self.second = second


class TimerWidget(QWidget):
    def __init__(self, name: str = '') -> None:
        super().__init__()
        # 倒计时名字
        self.name = name
        # UI 刷新计时
        self.update_timer = QTimer()
        self.update_timer_step_ms = 100
        self.complete_notice_timer = QTimer()
        # 计时器时间输入
        self.timer_mm_edit = TimerNumberLineEdit('00', self)
        self.timer_ss_edit = TimerNumberLineEdit('00', self)
        self.timer_sep_label = QLabel(':', self)
        self.timer_progress = QProgressBar()
        # 计时器控制按钮
        self.start_pause_button = TimerCtrlButton(TimerCtrlStateEnum.START, QIcon(ICON_START), '', self)
        self.reset_button = TimerCtrlButton(TimerCtrlStateEnum.NA, QIcon(ICON_RESET), '', self)
        self.clear_button = TimerCtrlButton(TimerCtrlStateEnum.NA, QIcon(ICON_CLEAR), '', self)
        # 计时器加减时间按钮
        self.minute_1_button = TimerAddTimeButton(1 * 60, '1分', self)
        self.minute_3_button = TimerAddTimeButton(3 * 60, '3分', self)
        self.minute_5_button = TimerAddTimeButton(5 * 60, '5分', self)
        self.minute_10_button = TimerAddTimeButton(10 * 60,'10分', self)
        self.timer = SimpleTimer()
        self.dt_pause_start, self.dt_pause_stop = datetime.now(), datetime.now()
        # 说明文字
        self.disp_mode = DispModeEnum.FULL
        self.timer_hint_label = QLabel('鼠标选中数字+键盘 / 鼠标移到数字+滚轮')
        self.add_time_label = QLabel('左键加时长，右键减时长')

        self.initUi()

    def initUi(self):
        hbox_align_center = QHBoxLayout()
        hbox_align_center.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hbox_align_center.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        self.setLayout(hbox_align_center)

        vbox = QVBoxLayout()
        vbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hbox_align_center.addStretch(1)
        hbox_align_center.addLayout(vbox)
        hbox_align_center.addStretch(1)

        hbox_hint = QHBoxLayout()
        hint_head_label = QLabel('计时提醒 :')
        hint_head_label.setStyleSheet(f'font-family: {FONT_CN}; font-size: 20px; font-weight: bold;')
        hint_line_edit = QLineEdit()
        hint_line_edit.setStyleSheet(f'''
                                     background: hsla(5, 0%, 85%, 45%);
                                     border-radius: 15px;
                                     font-family: {FONT_CN}; font-size: 20px; font-weight: bold;
                                     padding: 3px 12px;
                                     ''')
        hbox_hint.addWidget(hint_head_label)
        hbox_hint.addWidget(hint_line_edit)
        vbox.addLayout(hbox_hint)

        self.timer_hint_label = QLabel('鼠标选中数字+键盘 / 鼠标移到数字+滚轮')
        self.timer_hint_label.setStyleSheet(f'color:gray; font-family:{FONT_CN}; font-size: 20px; font-weight: bold;')
        self.timer_hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.addWidget(self.timer_hint_label)

        # region 元素：时间展示区
        vbox_timer_w_progress = QVBoxLayout()
        vbox_timer_w_progress.setSpacing(0)
        vbox_timer_w_progress.setContentsMargins(0, 0, 0, 0)

        hbox_timer_display = QHBoxLayout()
        hbox_timer_display.setSpacing(2)
        hbox_timer_display.setContentsMargins(0, 0, 0, 0)
        hbox_timer_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hbox_timer_display.addWidget(self.timer_mm_edit)
        hbox_timer_display.addWidget(self.timer_sep_label)
        hbox_timer_display.addWidget(self.timer_ss_edit)

        vbox_timer_w_progress.addLayout(hbox_timer_display)
        vbox_timer_w_progress.addWidget(self.timer_progress)

        vbox.addLayout(vbox_timer_w_progress)
        # endregion 元素：时间展示区

        self.timer_progress.setObjectName('timer_progress')
        self.timer_progress.setTextVisible(False)
        timer_progress_border = 'border: 1px; border-bottom-left-radius:12px; border-bottom-right-radius:12px;'
        self.timer_progress.setStyleSheet(f'''
                                        #timer_progress{{ background-color: hsla(5, 0%, 85%, 45%); {timer_progress_border} }}
                                        #timer_progress::chunk{{ background-color: hsl(210, 45%, 45%); {timer_progress_border} }}
                                        ''')
        self.timer_progress.setFixedHeight(12)

        # region 元素：控制按钮
        hbox_control = QHBoxLayout()
        hbox_control.addWidget(self.start_pause_button)
        hbox_control.addWidget(self.reset_button)
        hbox_control.addWidget(self.clear_button)
        vbox.addLayout(hbox_control)

        separator = QFrame()
        separator.setFrameStyle(QFrame.Shape.HLine | QFrame.Shadow.Plain)
        separator.setContentsMargins(0, 0, 0, 0)
        vbox.addWidget(separator)

        vbox_add_time = QVBoxLayout()
        vbox_add_time.setContentsMargins(0, 0, 0, 0)

        self.add_time_label.setStyleSheet(f'color:gray; font-family:{FONT_CN}; font-size: 20px; font-weight: bold;')
        self.add_time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox_add_time.addWidget(self.add_time_label)

        hbox_add_time = QHBoxLayout()
        hbox_add_time.setSpacing(10)
        hbox_add_time.setContentsMargins(0, 0, 0, 0)
        hbox_add_time.addWidget(self.minute_1_button)
        hbox_add_time.addWidget(self.minute_3_button)
        hbox_add_time.addWidget(self.minute_5_button)
        hbox_add_time.addWidget(self.minute_10_button)
        vbox_add_time.addLayout(hbox_add_time)

        vbox.addLayout(vbox_add_time)
        # endregion 元素：控制按钮

        # 时间展示与输入
        self.timer_mm_edit.setValidator(QIntValidator(1, 99, self))
        self.timer_ss_edit.setValidator(QIntValidator(1, 99, self))
        self.timer_mm_edit.wheelEvent = partial(self.handle_wheel_event_timer_edit, 'mm')
        self.timer_ss_edit.wheelEvent = partial(self.handle_wheel_event_timer_edit, 'ss')
        self.timer_sep_label.setFocus()

        timer_font = QFont('calibri', 80, QFont.Weight.Bold)
        self.timer_mm_edit.setFont(timer_font)
        self.timer_ss_edit.setFont(timer_font)
        self.timer_sep_label.setFont(timer_font)
        self.timer_mm_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer_ss_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer_sep_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer_mm_edit.setText('00')
        self.timer_ss_edit.setText('00')
        self.timer_mm_edit.setMaxLength(2)
        self.timer_ss_edit.setMaxLength(2)
        self.timer_mm_edit.setFocus()

        self.timer_mm_edit.setObjectName('timer_mm_edit')
        self.timer_ss_edit.setObjectName('timer_ss_edit')
        self.timer_sep_label.setObjectName('timer_sep_label')

        ctrl_btn_h = ctrl_btn_w = 50
        ctrl_btn_size = QSize(ctrl_btn_w, ctrl_btn_h)
        self.start_pause_button.setIconSize(ctrl_btn_size)
        self.reset_button.setIconSize(ctrl_btn_size)
        self.clear_button.setIconSize(ctrl_btn_size)
        self.start_pause_button.setFixedSize(ctrl_btn_size)
        self.reset_button.setFixedSize(ctrl_btn_size)
        self.clear_button.setFixedSize(ctrl_btn_size)

        p = self.palette()
        p.setColor(QPalette.ColorRole.Background, COLOR_WINDOW_BG)
        self.setPalette(p)
        self.setStyleSheet(f'''
                            #timer_mm_edit, #timer_ss_edit, #timer_sep_label{{
                                background-color: transparent;
                                border: 0px;
                            }}
                            #timer_mm_edit{{ border-top-left-radius: 12px; }}
                            #timer_ss_edit{{ border-top-right-radius: 12px; }}
                            #timer_mm_edit::focus, #timer_ss_edit::focus{{ background-color: gainsboro; }}
                            TimerCtrlButton{{ background-color: transparent; border: 0px; }}
                            TimerAddTimeButton{{
                                height: 36px;
                                font-family: {FONT_CN}; font-size: 20px; font-weight: bold;
                                border: 3px solid; border-radius: 12px;
                            }}
                            TimerAddTimeButton:disabled{{ border-color: gray; }}
                           ''')

        # 按钮控制
        self.start_pause_button.clicked.connect(self.start_pause)
        self.reset_button.clicked.connect(self.reset)
        self.clear_button.clicked.connect(self.clear)

        self.minute_1_button.mousePressEvent = partial(self.handle_mouse_press_event_add_time_btn, self.minute_1_button)
        self.minute_3_button.mousePressEvent = partial(self.handle_mouse_press_event_add_time_btn, self.minute_3_button)
        self.minute_5_button.mousePressEvent = partial(self.handle_mouse_press_event_add_time_btn, self.minute_5_button)
        self.minute_10_button.mousePressEvent = partial(self.handle_mouse_press_event_add_time_btn, self.minute_10_button)

        self.update_timer.timeout.connect(self.on_timer_timeout)
        self.complete_notice_timer.timeout.connect(self.handle_timer_complete)

        self.installEventFilter(self)
        self.keyPressEvent = self.handle_key_press

    def eventFilter(self, obj: QObject, event: QEvent):
        if event.type() == QEvent.Type.MouseButtonPress:
            if obj in {self.timer_mm_edit, self.timer_ss_edit}:
                return True
            self.timer_mm_edit.clearFocus()
            self.timer_ss_edit.clearFocus()
        return super().eventFilter(obj, event)

    def handle_key_press(self, event: QKeyEvent):
        """ 处理 各种按键
        1. 计时器结束，正在播放提示时，可 Esc 停止
        """
        modifiers_mask = {
            Qt.KeyboardModifier.AltModifier, Qt.KeyboardModifier.ControlModifier, Qt.KeyboardModifier.MetaModifier, 
            Qt.KeyboardModifier.ShiftModifier
            }
        keys_mask = {Qt.Key.Key_Alt, Qt.Key.Key_Control, Qt.Key.Key_Meta, Qt.Key.Key_Shift}
        if event.modifiers() in modifiers_mask:
            if event.key() not in keys_mask:
                print(f'TimerWidget{self.name}.handle_key_press {QKeySequence(int(event.modifiers()) + event.key()).toString()}')
            else:
                print(f'TimerWidget{self.name}.handle_key_press {QKeySequence(int(event.modifiers())).toString()[:-1]}')
        else:
            print(f'TimerWidget{self.name}.handle_key_press {QKeySequence(event.key()).toString(QKeySequence.SequenceFormat.NativeText)}')
        if self.complete_notice_timer.isActive() and event.key() == Qt.Key.Key_Escape:
            self.reset()
        if event.key() == Qt.Key.Key_F11:
            if self.disp_mode == DispModeEnum.CLEAN:
                self.set_disp_mode_full()
            elif self.disp_mode == DispModeEnum.FULL:
                self.set_disp_mode_clean()

    def handle_mouse_press_event_add_time_btn(self, btn: TimerAddTimeButton, event: QMouseEvent):
        """ 处理 增减时间按钮 鼠标行为，左键加时长，右键减时长 """
        if event.button() == Qt.MouseButton.LeftButton:
            self.add_to_total_seconds(0, btn.second)
        elif event.button() == Qt.MouseButton.RightButton:
            self.add_to_total_seconds(0, -btn.second)
        else:
            event.ignore()

    def handle_wheel_event_timer_edit(self, unit: str, event: QWheelEvent):
        """ 处理 计时器输入框 滚轮行为 """
        # print('[handle_wheel_event_timer_edit]', event.angleDelta().y())
        if self.update_timer.isActive() or self.complete_notice_timer.isActive():
            return
        delta = -1 if event.angleDelta().y() < 0 else 1
        if unit == 'mm':
            self.add_to_total_seconds(delta)
        elif unit == 'ss':
            self.add_to_total_seconds(0, delta)

    def add_to_total_seconds(self, minute: int, second: int = 0) -> None:
        """ 增加计时器时长 """
        mm = 0 if not self.timer_mm_edit.text() else int(self.timer_mm_edit.text())
        ss = 0 if not self.timer_ss_edit.text() else int(self.timer_ss_edit.text())
        total_seconds = mm * 60 + ss + minute * 60 + second
        if total_seconds < 0 or total_seconds > 99 * 60:
            return
        self.refresh_timer_display(seconds=total_seconds)

    def enable_change_time(self, is_enable: bool):
        """ 设置是否允许更改当前计时器时间，例：计时器暂停时，不允许修改剩余时长 """
        self.timer_mm_edit.is_edit_allowed = is_enable
        self.timer_ss_edit.is_edit_allowed = is_enable
        self.minute_1_button.setEnabled(is_enable)
        self.minute_3_button.setEnabled(is_enable)
        self.minute_5_button.setEnabled(is_enable)
        self.minute_10_button.setEnabled(is_enable)
        if is_enable:
            self.start_pause_button.setEnabled(True)
        else:
            self.timer_mm_edit.clearFocus()
            self.timer_ss_edit.clearFocus()

    def start_pause(self):
        """ 计时器 开始或暂停 """
        button_state = self.start_pause_button.curr_state
        if button_state == TimerCtrlStateEnum.PAUSE:
            success = self.pause()
        elif button_state == TimerCtrlStateEnum.RESUME:
            success = self.resume()
        elif button_state == TimerCtrlStateEnum.START:
            success = self.start()

        if success:
            self.flip_start_pause_button()

    def flip_start_pause_button(self):
        """ 根据倒计时状态 设置开始、暂停按钮状态与显示 """
        button_text = self.start_pause_button.curr_state
        if button_text == TimerCtrlStateEnum.PAUSE:
            self.start_pause_button.set_curr_state(TimerCtrlStateEnum.RESUME)
        elif button_text == TimerCtrlStateEnum.RESUME:
            self.start_pause_button.set_curr_state(TimerCtrlStateEnum.PAUSE)
        elif button_text == TimerCtrlStateEnum.START:
            self.start_pause_button.set_curr_state(TimerCtrlStateEnum.PAUSE)

    # region 计时控制功能
    def start(self) -> bool:
        """ 倒计时开始 """
        mm = 0 if not self.timer_mm_edit.text() else int(self.timer_mm_edit.text())
        ss = 0 if not self.timer_ss_edit.text() else int(self.timer_ss_edit.text())
        total_seconds = mm * 60 + ss
        dt_start, dt_stop = datetime.now(), datetime.now() + timedelta(seconds=total_seconds)
        # print(f'[start] mm: {mm}, ss: {ss}, total_second: {total_seconds}, curr_ts: {self.timer.dt_start.isoformat()}, ts: {self.timer.dt_stop.isoformat()}')
        if dt_start == dt_stop:
            return False
        self.timer = SimpleTimer(dt_start, dt_stop)
        self.reset()  # 先重置显示
        self.enable_change_time(False)
        self.update_timer.start(self.update_timer_step_ms)
        return True

    def pause(self) -> bool:
        """ 倒计时暂停 """
        self.timer.pause()
        # self.dt_pause_start = datetime.now()
        self.update_timer.stop()
        self.complete_notice_timer.stop()
        return True

    def resume(self) -> bool:
        """ 倒计时继续 """
        self.timer.resume()
        self.update_timer.start(self.update_timer_step_ms)
        return True

    def reset(self):
        """ 倒计时重置 """
        self.update_timer.stop()
        self.complete_notice_timer.stop()
        self.timer.reset()
        total_seconds = self.timer.sec_total()
        # print(f'[reset]: {total_seconds // 3600:02}:{total_seconds % 3600 // 60:02}:{total_seconds % 60:02}')
        self.enable_change_time(True)
        self.start_pause_button.set_curr_state(TimerCtrlStateEnum.START)
        self.refresh_timer_display(total_seconds)
        self.refresh_timer_progress(0)

    def clear(self):
        """ 倒计时清除 """
        self.enable_change_time(True)
        self.start_pause_button.set_curr_state(TimerCtrlStateEnum.START)
        self.update_timer.stop()
        self.complete_notice_timer.stop()
        self.timer = SimpleTimer()
        self.refresh_timer_display(0)
        self.refresh_timer_progress(0)
    # endregion 计时控制功能

    def refresh_timer_display(self, seconds: int = None) -> None:
        """ 倒计时剩余时间 显示更新 """
        seconds = self.timer.sec_total() if seconds is None else seconds
        mm = seconds // 60
        ss = seconds % 60
        self.timer_mm_edit.setText(f'{mm:02}')
        self.timer_ss_edit.setText(f'{ss:02}')

    def refresh_timer_progress(self, millisec_remain: int = None):
        """ 倒计时进度条 显示更新 """
        millisec_remain = millisec_remain if millisec_remain is not None else self.timer.ms_remain()
        if self.start_pause_button.curr_state == TimerCtrlStateEnum.START:
            self.timer_progress.reset()
        else:
            self.timer_progress.setMaximum(self.timer.ms_total())
            self.timer_progress.setValue(millisec_remain)
            # print(f'[refresh_timer_progress] max:{self.timer_progress.maximum()} val:{self.timer_progress.value()}')

    def on_timer_timeout(self):
        """ 倒计时结束 主线程行为 """
        # print(f'[on_timer_timeout], {self.timer.dt_stop.isoformat()} {datetime.now().isoformat()} {self.timer.ms_remain()}')
        self.refresh_timer_display(self.timer.sec_remain())
        self.refresh_timer_progress(self.timer.ms_remain())
        if self.timer.is_time_up():
            # 倒计时结束
            self.pause()
            self.start_pause_button.setEnabled(False)
            self.handle_timer_complete()
            self.complete_notice_timer.start(1600)
            self.raise_()
            self.show()
            self.activateWindow()

    def handle_timer_complete(self):
        import threading
        threading.Thread(target=self.timer_complete_worker).start()

    def timer_complete_worker(self):
        """ 倒计时结束 子线程行为 """
        p = self.palette()
        p.setColor(QPalette.ColorRole.Background, COLOR_WINDOW_BG_ALARM)
        self.setPalette(p)

        duration = 200  # milliseconds
        freq = 450  # Hz
        repeat_cnt = 3
        if platform.system() == 'Windows':
            import winsound
            for _ in range(repeat_cnt):
                winsound.Beep(freq, duration)
        else:
            import os
            for _ in range(repeat_cnt):
                os.system('play -nq -t alsa synth {} sine {}'.format(duration, freq))

        p.setColor(QPalette.ColorRole.Background, COLOR_WINDOW_BG)
        self.setPalette(p)

    def set_disp_mode_clean(self):
        self.disp_mode = DispModeEnum.CLEAN
        self.timer_hint_label.hide()
        self.add_time_label.hide()
        self.adjustSize()
        # self.resize(self.layout().sizeHint())
        # self.setFixedSize(self.layout().sizeHint())

    def set_disp_mode_full(self):
        self.disp_mode = DispModeEnum.FULL
        self.timer_hint_label.show()
        self.add_time_label.show()
        self.adjustSize()
        # self.resize(self.layout().sizeHint())
        # self.setFixedSize(self.layout().sizeHint())


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    window = TimerWidget()
    window.show()
    sys.exit(app.exec_())
