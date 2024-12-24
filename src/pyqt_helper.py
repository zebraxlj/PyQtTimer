from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeyEvent, QKeySequence


def print_key_event(msg: str, event: QKeyEvent):
    modifiers_mask = {
        Qt.KeyboardModifier.AltModifier, Qt.KeyboardModifier.ControlModifier, Qt.KeyboardModifier.MetaModifier, 
        Qt.KeyboardModifier.ShiftModifier
    }
    keys_mask = {Qt.Key.Key_Alt, Qt.Key.Key_Control, Qt.Key.Key_Meta, Qt.Key.Key_Shift}
    if event.modifiers() in modifiers_mask:
        if event.key() not in keys_mask:
            print(f'{msg} {QKeySequence(int(event.modifiers()) + event.key()).toString()}')
        else:
            print(f'{msg} {QKeySequence(int(event.modifiers())).toString()[:-1]}')
    else:
        if event.key() not in keys_mask:
            print(f'{msg} {QKeySequence(event.key()).toString(QKeySequence.SequenceFormat.NativeText)}')
        else:
            print(f'{msg} {event.key()}')
