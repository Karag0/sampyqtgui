import sys
from PyQt6 import QtWidgets, QtCore, QtGui
from ultralytics import SAM
import numpy as np
import cv2
import os
from threading import Thread

class SAMSegmentationApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SAM 2.1 Сегментация")
        self.setGeometry(100, 100, 1200, 800)
        
        # Загрузка модели SAM 2.1
        self.model = SAM("sam2.1_b.pt")
        self.current_image = None
        self.original_image = None
        self.current_mask = None
        self.drawing = False
        self.selection_points = []
        self.selection_rect = QtCore.QRect()
        self.mode = "all"  # all, bbox, point
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.offset_x = 0
        self.offset_y = 0
        
        self.init_ui()
        
    def init_ui(self):
        # Центральный виджет
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QtWidgets.QHBoxLayout(central_widget)
        
        # Левая панель управления
        control_panel = QtWidgets.QVBoxLayout()
        
        # Кнопка загрузки изображения
        self.load_btn = QtWidgets.QPushButton("Загрузить изображение")
        self.load_btn.clicked.connect(self.load_image)
        control_panel.addWidget(self.load_btn)
        
        # Режимы сегментации
        mode_group = QtWidgets.QGroupBox("Режим сегментации")
        mode_layout = QtWidgets.QVBoxLayout()
        
        self.all_radio = QtWidgets.QRadioButton("Выделить всё")
        self.all_radio.setChecked(True)
        self.all_radio.toggled.connect(lambda: self.set_mode("all"))
        mode_layout.addWidget(self.all_radio)
        
        self.bbox_radio = QtWidgets.QRadioButton("Прямоугольная область")
        self.bbox_radio.toggled.connect(lambda: self.set_mode("bbox"))
        mode_layout.addWidget(self.bbox_radio)
        
        self.point_radio = QtWidgets.QRadioButton("Точечный выбор")
        self.point_radio.toggled.connect(lambda: self.set_mode("point"))
        mode_layout.addWidget(self.point_radio)
        
        mode_group.setLayout(mode_layout)
        control_panel.addWidget(mode_group)
        
        # Кнопка применения сегментации
        self.segment_btn = QtWidgets.QPushButton("Применить сегментацию")
        self.segment_btn.clicked.connect(self.apply_segmentation)
        control_panel.addWidget(self.segment_btn)
        
        # Кнопка очистки
        self.clear_btn = QtWidgets.QPushButton("Очистить")
        self.clear_btn.clicked.connect(self.clear_selections)
        control_panel.addWidget(self.clear_btn)
        
        # Кнопка сохранения маски
        self.save_btn = QtWidgets.QPushButton("Сохранить маску")
        self.save_btn.clicked.connect(self.save_mask)
        control_panel.addWidget(self.save_btn)
        
        # Правая область просмотра
        self.image_label = QtWidgets.QLabel()
        self.image_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("background-color: #f0f0f0")
        self.image_label.mousePressEvent = self.handle_mouse_press
        self.image_label.mouseMoveEvent = self.handle_mouse_move
        self.image_label.mouseReleaseEvent = self.handle_mouse_release
        
        # Добавление элементов в макет
        main_layout.addLayout(control_panel, 1)
        main_layout.addWidget(self.image_label, 3)
        
    def set_mode(self, mode):
        self.mode = mode
        if mode != "bbox":
            self.selection_rect = QtCore.QRect()
        if mode != "point":
            self.selection_points = []
        self.update_display()
        
    def load_image(self):
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Открыть изображение", "", "Изображения (*.png *.jpg *.bmp)"
        )
        if file_name:
            self.current_image = cv2.imread(file_name)
            self.original_image = self.current_image.copy()
            self.current_mask = None
            self.update_display()
            
    def clear_selections(self):
        self.selection_points = []
        self.selection_rect = QtCore.QRect()
        self.current_mask = None
        self.update_display()
        
    def update_display(self):
        if self.current_image is None:
            self.image_label.setText("Здесь будет отображаться изображение")
            return
            
        display_image = self.current_image.copy()
        
        # Отображение текущего выбора
        if self.mode == "bbox" and not self.selection_rect.isNull():
            cv2.rectangle(display_image, 
                         (self.selection_rect.left(), self.selection_rect.top()),
                         (self.selection_rect.right(), self.selection_rect.bottom()),
                         (0, 255, 0), 2)
                         
        elif self.mode == "point":
            for point in self.selection_points:
                cv2.circle(display_image, (point[0], point[1]), 5, (0, 0, 255), -1)
        
        # Отображение маски, если она есть
        if self.current_mask is not None:
            mask_overlay = np.zeros_like(display_image)
            mask_overlay[self.current_mask > 0] = [0, 255, 0]
            display_image = cv2.addWeighted(display_image, 0.7, mask_overlay, 0.3, 0)
        
        # Преобразование в QPixmap для отображения
        height, width, channel = display_image.shape
        bytes_per_line = 3 * width
        q_img = QtGui.QImage(display_image.data, width, height, 
                            bytes_per_line, QtGui.QImage.Format.Format_BGR888)
        self.pixmap = QtGui.QPixmap.fromImage(q_img)

        # Сохраняем реальный размер изображения на экране
        label_size = self.image_label.size()
        scaled_pixmap = self.pixmap.scaled(
            label_size,
            QtCore.Qt.AspectRatioMode.KeepAspectRatio,
            QtCore.Qt.TransformationMode.SmoothTransformation
        )
        
        # Вычисляем коэффициенты масштабирования и смещение
        self.scale_x = width / scaled_pixmap.width()
        self.scale_y = height / scaled_pixmap.height()
        self.offset_x = (label_size.width() - scaled_pixmap.width()) // 2
        self.offset_y = (label_size.height() - scaled_pixmap.height()) // 2

        self.image_label.setPixmap(scaled_pixmap)
        
    def handle_mouse_press(self, event):
        if self.current_image is None or event.button() != QtCore.Qt.MouseButton.LeftButton:
            return
            
        # Преобразование координат с учетом масштаба и смещения
        x = int((event.position().x() - self.offset_x) * self.scale_x)
        y = int((event.position().y() - self.offset_y) * self.scale_y)
        
        if 0 <= x < self.current_image.shape[1] and 0 <= y < self.current_image.shape[0]:
            if self.mode == "bbox":
                self.drawing = True
                self.selection_rect = QtCore.QRect(x, y, 0, 0)
            elif self.mode == "point":
                self.selection_points.append([x, y])
            self.update_display()
        
    def handle_mouse_move(self, event):
        if self.drawing and self.mode == "bbox":
            # Преобразование координат с учетом масштаба и смещения
            x = int((event.position().x() - self.offset_x) * self.scale_x)
            y = int((event.position().y() - self.offset_y) * self.scale_y)
            self.selection_rect.setBottomRight(QtCore.QPoint(x, y))
            self.update_display()
            
    def handle_mouse_release(self, event):
        self.drawing = False
        
    def apply_segmentation(self):
        if self.current_image is None:
            return
            
        # Создаем временную директорию, если ее нет
        os.makedirs("temp", exist_ok=True)
        temp_path = "temp/temp_image.jpg"
        cv2.imwrite(temp_path, self.current_image)
        
        try:
            if self.mode == "all":
                # Запускаем обработку в отдельном потоке, чтобы не зависал интерфейс
                Thread(target=self.process_all_mode, args=(temp_path,)).start()
            elif self.mode == "bbox":
                x1, y1 = self.selection_rect.topLeft().x(), self.selection_rect.topLeft().y()
                x2, y2 = self.selection_rect.bottomRight().x(), self.selection_rect.bottomRight().y()
                Thread(target=self.process_bbox_mode, args=(temp_path, x1, y1, x2, y2)).start()
            elif self.mode == "point":
                points = [[p[0], p[1]] for p in self.selection_points]
                labels = [1] * len(points)  # Все точки - положительные
                Thread(target=self.process_point_mode, args=(temp_path, points, labels)).start()
                
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Ошибка", f"Ошибка при обработке: {str(e)}")
            
    def process_all_mode(self, temp_path):
        try:
            results = self.model(temp_path)
            if results and len(results) > 0:
                self.current_mask = results[0].masks.data[0].cpu().numpy()
                self.current_mask = (self.current_mask * 255).astype(np.uint8)
                self.update_display()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Ошибка", f"Ошибка при обработке 'Выделить всё': {str(e)}")
            
    def process_bbox_mode(self, temp_path, x1, y1, x2, y2):
        try:
            results = self.model(temp_path, bboxes=[x1, y1, x2, y2])
            if results and len(results) > 0:
                self.current_mask = results[0].masks.data[0].cpu().numpy()
                self.current_mask = (self.current_mask * 255).astype(np.uint8)
                self.update_display()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Ошибка", f"Ошибка при обработке 'Прямоугольная область': {str(e)}")
            
    def process_point_mode(self, temp_path, points, labels):
        try:
            results = self.model(temp_path, points=points, labels=labels)
            if results and len(results) > 0:
                self.current_mask = results[0].masks.data[0].cpu().numpy()
                self.current_mask = (self.current_mask * 255).astype(np.uint8)
                self.update_display()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Ошибка", f"Ошибка при обработке 'Точечный выбор': {str(e)}")
            
    def save_mask(self):
        if self.current_mask is None:
            QtWidgets.QMessageBox.warning(self, "Предупреждение", "Сначала создайте маску!")
            return  
            
        file_name, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Сохранить маску", "", "PNG Files (*.png)"
        )
        if file_name:
            cv2.imwrite(file_name, self.current_mask)
            QtWidgets.QMessageBox.information(self, "Успех", "Маска успешно сохранена!")
            
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.current_image is not None:
            self.update_display()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = SAMSegmentationApp()
    window.show()
    sys.exit(app.exec())