from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QColor, QPainterPath, QPen, QBrush
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QRect, pyqtProperty


class SwitchButton(QWidget):
    statusChanged = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._space = 2
        self._radius = 5
        self._checked = False
        self._showText = False  # Original C++ code sets this to false
        self._showCircle = False  # Based on original declaration
        self._animation = True

        # Colors
        self._bgColorOn = QColor("#b6f6ff")
        self._bgColorOff = QColor("#244F9E")
        self._sliderColorOn = QColor(255, 255, 255)
        self._sliderColorOff = QColor(255, 255, 255)
        self._textColor = QColor(255, 255, 255)

        # Text labels
        self._textOn = "On"
        self._textOff = "Off"

        # Animation properties
        self._step = 0
        self._startX = 0
        self._endX = 0

        # Fixed size
        self.setMinimumSize(50, 20)
        self.setMaximumSize(50, 20)

        # Timer for animation
        self._timer = QTimer(self)
        self._timer.setInterval(30)
        self._timer.timeout.connect(self.updateValue)



    def drawBackGround(self, painter):
        painter.save()
        painter.setPen(Qt.NoPen)

        # Background color based on state
        bgColor = self._bgColorOn if self._checked else self._bgColorOff
        if self.isEnabled():
            bgColor.setAlpha(255)
        painter.setBrush(bgColor)

        rect = self.rect()
        side = min(rect.width(), rect.height())

        # Create rounded background shape
        path1 = QPainterPath()
        path1.addEllipse(rect.x(), rect.y(), side, side)

        path2 = QPainterPath()
        path2.addEllipse(rect.width() - side, rect.y(), side, side)

        path3 = QPainterPath()
        path3.addRect(rect.x() + side / 2, rect.y(), rect.width() - side, rect.height())

        path = path1 + path2 + path3
        painter.drawPath(path)

        # Draw text (note: always drawn regardless of _showText state)
        sliderWidth = min(self.height(), self.width()) - self._space * 2 - 5
        if self._checked:
            textRect = QRect(0, 0, self.width() - sliderWidth, self.height())
            if self._showText:
                painter.setPen(QPen(self._textColor))
                painter.drawText(textRect, Qt.AlignCenter, self._textOn)
        else:
            textRect = QRect(sliderWidth, 0, self.width() - sliderWidth, self.height())
            if self._showText:
                painter.setPen(QPen(self._textColor))
                painter.drawText(textRect, Qt.AlignCenter, self._textOff)

        painter.restore()

    def drawSlider(self, painter):
        painter.save()
        painter.setPen(Qt.NoPen)

        # Slider color based on state
        color = self._sliderColorOn if self._checked else self._sliderColorOff
        painter.setBrush(QBrush(color))

        # Calculate slider dimensions
        sliderWidth = min(self.width(), self.height()) - self._space * 2
        rect = QRect(self._space + self._startX, self._space, sliderWidth, sliderWidth)
        painter.drawEllipse(rect)

        painter.restore()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
        self.drawBackGround(painter)
        self.drawSlider(painter)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self._checked = not self._checked
        self.statusChanged.emit(self._checked)

        # Calculate animation parameters
        self._step = self.width() // 10
        self._endX = self.width() - self.height() if self._checked else 0

        # Start animation or immediate update
        if self._animation:
            self._timer.start()
        else:
            self._startX = self._endX
            self.update()

    def updateValue(self):
        if self._checked:
            if self._startX < self._endX:
                self._startX += self._step
            else:
                self._startX = self._endX
                self._timer.stop()
        else:
            if self._startX > self._endX:
                self._startX -= self._step
            else:
                self._startX = self._endX
                self._timer.stop()
        self.update()

    # Property getters
    def space(self):
        return self._space

    def radius(self):
        return self._radius

    def checked(self):
        return self._checked

    def showText(self):
        return self._showText

    def showCircle(self):
        return self._showCircle

    def animation(self):
        return self._animation

    def bgColorOn(self):
        return self._bgColorOn

    def bgColorOff(self):
        return self._bgColorOff

    def sliderColorOn(self):
        return self._sliderColorOn

    def sliderColorOff(self):
        return self._sliderColorOff

    def textColor(self):
        return self._textColor

    def textOn(self):
        return self._textOn

    def textOff(self):
        return self._textOff

    # Property setters
    def setSpace(self, space):
        if self._space != space:
            self._space = space
            self.update()

    def setRadius(self, radius):
        if self._radius != radius:
            self._radius = radius
            self.update()

    # def setChecked(self, checked):
    #     if self._checked != checked:
    #         self._checked = checked
    #         self.update()

    def setChecked(self, checked):
        if self._checked != checked:
            self._checked = checked
            self._step = self.width() // 10
            self._endX = self.width() - self.height() if self._checked else 0

            if self._animation:
                self._timer.start()
            else:
                self._startX = self._endX
                self.update()

    def setShowText(self, show):
        if self._showText != show:
            self._showText = show
            self.update()

    def setShowCircle(self, show):
        if self._showCircle != show:
            self._showCircle = show
            self.update()

    def setAnimation(self, ok):
        if self._animation != ok:
            self._animation = ok
            self.update()

    def setBgColorOn(self, color):
        if self._bgColorOn != color:
            self._bgColorOn = color
            self.update()

    def setBgColorOff(self, color):
        if self._bgColorOff != color:
            self._bgColorOff = color
            self.update()

    def setSliderColorOn(self, color):
        if self._sliderColorOn != color:
            self._sliderColorOn = color
            self.update()

    def setSliderColorOff(self, color):
        if self._sliderColorOff != color:
            self._sliderColorOff = color
            self.update()

    def setTextColor(self, color):
        if self._textColor != color:
            self._textColor = color
            self.update()

    def setTextOn(self, text):
        if self._textOn != text:
            self._textOn = text
            self.update()

    def setTextOff(self, text):
        if self._textOff != text:
            self._textOff = text
            self.update()

    @pyqtProperty(QColor)
    def bgColorOn(self):
        return self._bgColorOn

    @bgColorOn.setter
    def bgColorOn(self, color):
        self._bgColorOn = color
        self.update()

    @pyqtProperty(QColor)
    def bgColorOff(self):
        return self._bgColorOff

    @bgColorOff.setter
    def bgColorOff(self, color):
        self._bgColorOff = color
        self.update()

    @pyqtProperty(QColor)
    def sliderColorOn(self):
        return self._sliderColorOn

    @sliderColorOn.setter
    def sliderColorOn(self, color):
        self._sliderColorOn = color
        self.update()

    @pyqtProperty(QColor)
    def sliderColorOff(self):
        return self._sliderColorOff

    @sliderColorOff.setter
    def sliderColorOff(self, color):
        self._sliderColorOff = color
        self.update()

    @pyqtProperty(QColor)
    def textColor(self):
        return self._textColor

    @textColor.setter
    def textColor(self, color):
        self._textColor = color
        self.update()