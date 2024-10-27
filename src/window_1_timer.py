from functools import partial
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QIcon, QMouseEvent
from PyQt5.QtWidgets import QApplication, QMainWindow

from timer_widget import TimerWidget, ICON_TOMATO


class OneTimerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUi()
    
    def initUi(self):
        pass


if __name__ == '__main__':
    '''
    pyinstaller --clean --onefile -n "番茄计时器" --add-data "*.png;." --noconsole -i pomodoro-icon.ico .\pomodoro.py
    rm -r build
    '''
    import os
    import sys
    # os.chdir(os.path.dirname(os.path.abspath(__file__)))
    os.environ["QT_SCALE_FACTOR"] = "1"
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)

    app = QApplication(sys.argv)
    window = TimerWidget()
    window.setWindowTitle('番茄计时器')
    window.setWindowIcon(QIcon(ICON_TOMATO))
    window_flags = (
        Qt.WindowType.Window | Qt.WindowType.WindowCloseButtonHint | Qt.WindowType.WindowStaysOnTopHint
        # | Qt.WindowType.FramelessWindowHint
        )
    window.setWindowFlags(window_flags)
    # window.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    window.setFixedSize(window.layout().sizeHint())

    def mousePressEvent(self: TimerWidget, event: QMouseEvent):
        # print('__main__.mousePressEvent', event.button(), event.type(), QMouseEvent.Type.MouseButtonPress, )
        self.lastPos = event.globalPos()  # 记录按下鼠标位置
        if event.button() == Qt.MouseButton.MiddleButton:  # 检查是否是中键
            if event.type() == QMouseEvent.Type.MouseButtonPress:
                QApplication.setOverrideCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self: TimerWidget, event: QMouseEvent):
        globalPos = event.globalPos()
        # print('__main__.mouseMoveEvent', self.lastPos, globalPos)
        if event.buttons() & Qt.MouseButton.MiddleButton:  # 检查中键是否被按下
            # 当前鼠标位置 - 之前鼠标位置 + 窗口左上角位置 = 移动后窗口左上角位置
            self.move(globalPos - self.lastPos + self.frameGeometry().topLeft())
            self.lastPos = globalPos  # 保存当前鼠标位置

    def mouseReleaseEvent(self: TimerWidget, event: QMouseEvent):
        if (
            event.button() in {Qt.MouseButton.MiddleButton}
            ):
            self.lastPos = QPoint()  # 松开鼠标重置位置信息
            QApplication.restoreOverrideCursor()

    window.mousePressEvent = partial(mousePressEvent, window)
    window.mouseMoveEvent = partial(mouseMoveEvent, window)
    window.mouseReleaseEvent = partial(mouseReleaseEvent, window)

    window.show()
    sys.exit(app.exec_())
