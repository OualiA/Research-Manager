from PySide6.QtWidgets import QStackedWidget, QGraphicsOpacityEffect
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QParallelAnimationGroup

class AnimatedStackedWidget(QStackedWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._duration = 500  # Animation duration in milliseconds
        self._animations = {}  # Store active animations
        self._opacity_effects = {}  # Store opacity effects to prevent GC issues

        # Pre-initialize opacity effects for existing pages
        self.init_opacity_effects()

    def init_opacity_effects(self):
        """Apply QGraphicsOpacityEffect to all existing pages at startup"""
        for i in range(self.count()):
            widget = self.widget(i)
            if widget:
                effect = QGraphicsOpacityEffect()
                widget.setGraphicsEffect(effect)
                effect.setOpacity(1.0)  # Ensure full opacity initially
                self._opacity_effects[widget] = effect

    def setCurrentIndexAnimated(self, index):
        """Animate the transition between QStackedWidget pages using fade effect"""
        if index == self.currentIndex():
            return

        current_widget = self.currentWidget()
        next_widget = self.widget(index)

        if current_widget is None or next_widget is None:
            self.setCurrentIndex(index)
            return

        # Ensure opacity effects exist for these widgets
        if current_widget not in self._opacity_effects:
            self._opacity_effects[current_widget] = QGraphicsOpacityEffect()
            current_widget.setGraphicsEffect(self._opacity_effects[current_widget])

        if next_widget not in self._opacity_effects:
            self._opacity_effects[next_widget] = QGraphicsOpacityEffect()
            next_widget.setGraphicsEffect(self._opacity_effects[next_widget])

        # Retrieve effects
        current_effect = self._opacity_effects[current_widget]
        next_effect = self._opacity_effects[next_widget]

        current_effect.setOpacity(1.0)
        next_effect.setOpacity(0.0)
        next_widget.show()

        # Fade out animation for current page
        fade_out = QPropertyAnimation(current_effect, b"opacity", parent=current_widget)
        fade_out.setDuration(self._duration)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(QEasingCurve.Type.InOutQuad)

        # Fade in animation for next page
        fade_in = QPropertyAnimation(next_effect, b"opacity", parent=next_widget)
        fade_in.setDuration(self._duration)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        fade_in.setEasingCurve(QEasingCurve.Type.InOutQuad)

        # Group animations
        group = QParallelAnimationGroup()
        group.addAnimation(fade_out)
        group.addAnimation(fade_in)

        # Store animation to prevent GC
        self._animations[index] = group

        # Ensure correct page switch after animation
        group.finished.connect(lambda: self.setCurrentIndex(index))
        group.finished.connect(lambda: self._animations.pop(index, None))  # Clean up
        group.start()
