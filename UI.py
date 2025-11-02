import sys
import random
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QFrame, QPushButton)
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QFont, QPainter, QColor, QPen, QBrush, QPolygon, QPixmap, QImage


class RoadViewWidget(QWidget):
    """中央道路视图控件"""

    def __init__(self):
        super().__init__()
        self.setMinimumSize(500, 500)
        self.vehicles = []
        self.recommendation = "keep"  # keep, left, right

        # 加载车辆图片和箭头图片
        self.load_car_images()
        self.load_arrow_images()

    def load_car_images(self):
        """加载车辆图片"""
        # 创建默认的车辆图片
        self.car_images = {
            'safe': self.create_default_car_image(QColor(100, 200, 100)),
            'warning': self.create_default_car_image(QColor(255, 255, 100)),
            'danger': self.create_default_car_image(QColor(255, 100, 100)),
            'target': self.create_default_car_image(QColor(0, 150, 255, 180))
        }

        # 尝试加载外部图片文件
        try:
            safe_pixmap = QPixmap("png/green.png")
            if not safe_pixmap.isNull():
                self.car_images['safe'] = safe_pixmap

            warning_pixmap = QPixmap("png/yello.png")
            if not warning_pixmap.isNull():
                self.car_images['warning'] = warning_pixmap

            danger_pixmap = QPixmap("png/red.png")
            if not danger_pixmap.isNull():
                self.car_images['danger'] = danger_pixmap

            target_pixmap = QPixmap("png/blue.png")
            if not target_pixmap.isNull():
                self.car_images['target'] = target_pixmap

        except Exception as e:
            print(f"加载车辆图片失败: {e}")

    def load_arrow_images(self):
        self.arrow_images = {
            'left': None,
            'right': None
        }

        # 尝试加载箭头图片
        try:
            left_arrow = QPixmap("png/left_arrow.png")
            if not left_arrow.isNull():
                self.arrow_images['left'] = left_arrow

            right_arrow = QPixmap("png/right_arrow.png")
            if not right_arrow.isNull():
                self.arrow_images['right'] = right_arrow

        except Exception as e:
            print(f"加载箭头图片失败: {e}")

        # 如果未加载到图片，创建默认箭头
        if self.arrow_images['left'] is None:
            self.arrow_images['left'] = self.create_default_arrow('left')
        if self.arrow_images['right'] is None:
            self.arrow_images['right'] = self.create_default_arrow('right')

    def create_default_arrow(self, direction):
        """创建默认箭头图片"""
        size = 100
        image = QImage(size, size, QImage.Format_ARGB32)
        image.fill(Qt.transparent)

        painter = QPainter(image)
        painter.setRenderHint(QPainter.Antialiasing)

        # 创建半透明蓝色
        arrow_color = QColor(0, 150, 255, 200)
        painter.setBrush(QBrush(arrow_color))
        painter.setPen(QPen(arrow_color, 2))

        # 根据方向绘制箭头
        if direction == 'left':
            points = [
                QPoint(size * 0.8, size * 0.2),
                QPoint(size * 0.2, size * 0.5),
                QPoint(size * 0.8, size * 0.8)
            ]
        else:  # right
            points = [
                QPoint(size * 0.2, size * 0.2),
                QPoint(size * 0.8, size * 0.5),
                QPoint(size * 0.2, size * 0.8)
            ]

        painter.drawPolygon(QPolygon(points))
        painter.end()

        return QPixmap.fromImage(image)

    def create_default_car_image(self, color):
        """创建默认车辆图片"""
        size = 64
        image = QImage(size, size, QImage.Format_ARGB32)
        image.fill(Qt.transparent)

        painter = QPainter(image)
        painter.setRenderHint(QPainter.Antialiasing)

        # 绘制车辆主体
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(QColor(50, 50, 50), 2))
        painter.drawRoundedRect(10, 20, 44, 24, 5, 5)
        painter.setBrush(QBrush(QColor(200, 230, 255)))
        painter.drawRect(15, 22, 8, 6)
        painter.drawRect(41, 22, 8, 6)

        painter.end()
        return QPixmap.fromImage(image)

    def update_vehicles(self, vehicles):
        self.vehicles = vehicles
        self.update()

    def set_recommendation(self, rec):
        self.recommendation = rec
        self.update()

    def paintEvent(self, event):
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)

            width = self.width()
            height = self.height()

            # 绘制道路背景
            painter.fillRect(0, 0, width, height, QColor(50, 50, 50))

            # 绘制车道
            lane_width = width / 3
            road_color = QColor(100, 100, 100)

            # 左车道
            painter.fillRect(0, 0, int(lane_width), height, road_color)
            # 当前车道（高亮）
            current_lane_color = QColor(120, 120, 120)
            painter.fillRect(int(lane_width), 0, int(lane_width), height, current_lane_color)
            # 右车道
            painter.fillRect(int(lane_width * 2), 0, int(lane_width), height, road_color)

            # 绘制车道线
            painter.setPen(QPen(QColor(255, 255, 255), 2, Qt.DashLine))
            for i in range(1, 3):
                x = int(lane_width * i)
                painter.drawLine(x, 0, x, height)

            # 绘制变道建议箭头
            if self.recommendation != "keep":
                # 选择箭头图片
                arrow_pixmap = self.arrow_images['left' if self.recommendation == 'left' else 'right']

                # 计算箭头位置（放在靠近中央车道的位置）
                if self.recommendation == 'left':

                    arrow_x = int(lane_width * 0.8)
                else:  # right

                    arrow_x = int(lane_width * 2.2) - 80

                arrow_y = height - 350  # 箭头垂直位置，更靠近中央


                arrow_size = 400
                scaled_arrow = arrow_pixmap.scaled(
                    arrow_size, arrow_size,
                    Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                painter.drawPixmap(arrow_x, arrow_y, scaled_arrow)

            # 绘制本车
            car_width = int(lane_width * 0.7)
            car_height = int(car_width * 0.5)
            car_x = width / 2 - car_width / 2
            car_y = height - car_height - 20


            own_car_pixmap = self.car_images['target']
            scaled_own_car = own_car_pixmap.scaled(car_width, car_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            painter.drawPixmap(int(car_x), int(car_y), scaled_own_car)

            # 绘制周围车辆
            for vehicle in self.vehicles:
                lane = vehicle['lane']
                pos = vehicle['position']


                vehicle_x = lane_width * lane + lane_width * 0.1 + (lane_width * 0.8) * pos
                vehicle_y = height * (1 - pos)
                size_factor = 0.3 + pos * 0.7
                v_width = int(lane_width * 0.7 * size_factor)
                v_height = int(v_width * 0.5)
                vehicle_x = int(vehicle_x)
                vehicle_y = int(vehicle_y)

                # 选择车辆图片
                if vehicle.get('target_lane', False):
                    car_pixmap = self.car_images['target']
                elif vehicle['risk_level'] == 0:
                    car_pixmap = self.car_images['safe']
                elif vehicle['risk_level'] == 1:
                    car_pixmap = self.car_images['warning']
                else:
                    car_pixmap = self.car_images['danger']

                # 缩放并绘制车辆图片
                scaled_pixmap = car_pixmap.scaled(v_width, v_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                painter.drawPixmap(
                    vehicle_x - scaled_pixmap.width() // 2,
                    vehicle_y - scaled_pixmap.height() // 2,
                    scaled_pixmap
                )

                # 绘制风险指示圈（如果有风险且不是目标车道车辆）
                if vehicle['risk_level'] > 0 and not vehicle.get('target_lane', False):
                    painter.setPen(QPen(
                        QColor(255, 100, 100) if vehicle['risk_level'] == 2
                        else QColor(255, 200, 100), 2, Qt.DashLine
                    ))
                    painter.setBrush(Qt.NoBrush)
                    risk_radius = max(v_width, v_height) + 5
                    painter.drawEllipse(
                        vehicle_x - risk_radius // 2,
                        vehicle_y - risk_radius // 2,
                        risk_radius,
                        risk_radius
                    )
        except Exception as e:
            print(f"绘制错误: {e}")


class RecommendationApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("智能网联车变道建议系统")
        self.setGeometry(100, 100, 800, 800)

        # 定义建议模板
        self.scenarios = [
            {
                "name": "保持车道-畅通",
                "recommendation": ("keep", "保持当前车道", "前方畅通", "🚗"),
                "vehicles": []
            },
            {
                "name": "保持车道-拥堵",
                "recommendation": ("keep", "保持车道，前方拥堵", "请耐心等待", "🚦"),
                "vehicles": [
                    {"lane": 1, "position": 0.6, "speed": 20, "risk_level": 0},
                    {"lane": 0, "position": 0.4, "speed": 60, "risk_level": 1},
                    {"lane": 2, "position": 0.5, "speed": 50, "risk_level": 1},
                ]
            },
            {
                "name": "建议左转-畅通",
                "recommendation": ("left", "建议向左变道", "500米内完成", "⬅️"),
                "vehicles": [
                    {"lane": 1, "position": 0.5, "speed": 40, "risk_level": 1},
                    {"lane": 0, "position": 0.8, "speed": 80, "risk_level": 0, "target_lane": True},
                    {"lane": 2, "position": 0.3, "speed": 60, "risk_level": 1},
                ]
            },
            {
                "name": "建议右转-畅通",
                "recommendation": ("right", "建议向右变道", "300米内完成", "➡️"),
                "vehicles": [
                    {"lane": 1, "position": 0.5, "speed": 40, "risk_level": 1},
                    {"lane": 0, "position": 0.3, "speed": 60, "risk_level": 1},
                    {"lane": 2, "position": 0.8, "speed": 80, "risk_level": 0, "target_lane": True},
                ]
            },
            {
                "name": "建议左转-超车",
                "recommendation": ("left", "建议变道超车", "安全距离充足", "🚙"),
                "vehicles": [
                    {"lane": 1, "position": 0.4, "speed": 30, "risk_level": 1},
                    {"lane": 0, "position": 0.9, "speed": 90, "risk_level": 0, "target_lane": True},
                ]
            },
            {
                "name": "建议右转-畅通",
                "recommendation": ("right", "右侧车道更畅通", "建议变道", "🛣️"),
                "vehicles": [
                    {"lane": 1, "position": 0.6, "speed": 50, "risk_level": 1},
                    {"lane": 0, "position": 0.5, "speed": 60, "risk_level": 1},
                    {"lane": 2, "position": 0.9, "speed": 80, "risk_level": 0, "target_lane": True},
                ]
            },
            {
                "name": "保持车道-安全",
                "recommendation": ("keep", "保持车道，注意安全", "侧方有车辆", "⚠️"),
                "vehicles": [
                    {"lane": 0, "position": 0.3, "speed": 70, "risk_level": 2},
                    {"lane": 2, "position": 0.4, "speed": 65, "risk_level": 2},
                ]
            }
        ]

        self.current_scenario_index = 0

        # 中央窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # 区域一：顶部状态栏
        self.create_top_status_bar(main_layout)

        # 区域二：中央道路视图
        self.create_road_view(main_layout)

        # 区域三：底部数据栏
        self.create_bottom_data_bar(main_layout)

        # 控制按钮区域
        self.create_control_buttons(main_layout)

        # 模拟数据 - 初始化为零
        self.co2_saved = 0
        self.efficiency = 0
        self.fuel_saved = 0.0
        self.safety_score = 100
        self.simulation_active = False

        # 设置定时器更新UI
        self.timer = QTimer()
        self.timer.timeout.connect(self.auto_update_scenario)
        self.update_simulation(update_data=False)

    def create_top_status_bar(self, layout):
        """创建顶部状态栏"""
        status_frame = QFrame()
        status_frame.setFrameStyle(QFrame.StyledPanel)
        status_frame.setStyleSheet("background-color: #2c3e50; border-radius: 5px;")
        status_frame.setFixedHeight(100)

        status_layout = QHBoxLayout(status_frame)

        # 建议图标
        self.recommendation_icon = QLabel("🚗")
        self.recommendation_icon.setFont(QFont("Arial", 28))
        self.recommendation_icon.setAlignment(Qt.AlignCenter)
        self.recommendation_icon.setFixedWidth(80)

        # 建议文本
        self.recommendation_text = QLabel("系统初始化中...")
        self.recommendation_text.setFont(QFont("Arial", 18, QFont.Bold))
        self.recommendation_text.setStyleSheet("color: white;")
        self.recommendation_text.setAlignment(Qt.AlignCenter)

        # 距离提示
        self.distance_hint = QLabel("")
        self.distance_hint.setFont(QFont("Arial", 14))
        self.distance_hint.setStyleSheet("color: #ecf0f1;")
        self.distance_hint.setAlignment(Qt.AlignCenter)

        # 场景名称显示
        self.scenario_label = QLabel("")
        self.scenario_label.setFont(QFont("Arial", 12))
        self.scenario_label.setStyleSheet("color: #bdc3c7;")
        self.scenario_label.setAlignment(Qt.AlignCenter)

        status_layout.addWidget(self.recommendation_icon)
        status_layout.addWidget(self.recommendation_text, 1)
        status_layout.addWidget(self.distance_hint)
        status_layout.addWidget(self.scenario_label)

        layout.addWidget(status_frame)

    def create_road_view(self, layout):
        """创建中央道路视图"""
        self.road_view = RoadViewWidget()
        self.road_view.setStyleSheet("background-color: #34495e; border-radius: 5px;")
        layout.addWidget(self.road_view, 1)

    def create_bottom_data_bar(self, layout):
        """创建底部数据栏"""
        data_frame = QFrame()
        data_frame.setFrameStyle(QFrame.StyledPanel)
        data_frame.setStyleSheet("background-color: #2c3e50; border-radius: 5px;")
        data_frame.setMinimumHeight(250)

        data_layout = QHBoxLayout(data_frame)

        # 碳减排量
        co2_widget = self.create_data_widget("CO₂减排", "0g", "🌱")
        efficiency_widget = self.create_data_widget("能效提升", "0%", "⚡")
        fuel_widget = self.create_data_widget("节省燃油", "0L", "⛽")
        safety_widget = self.create_data_widget("安全评分", "100", "🛡️")

        data_layout.addWidget(co2_widget)
        data_layout.addWidget(efficiency_widget)
        data_layout.addWidget(fuel_widget)
        data_layout.addWidget(safety_widget)

        layout.addWidget(data_frame)

    def create_data_widget(self, title, value, icon):
        """创建单个数据展示部件"""
        widget = QFrame()
        widget.setStyleSheet("""
            background-color: #34495e; 
            border-radius: 5px; 
            margin: 5px;
            padding: 15px;
        """)
        layout = QVBoxLayout(widget)

        # 标题
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        title_label.setStyleSheet("color: #bdc3c7;")
        title_label.setAlignment(Qt.AlignCenter)

        # 数值和图标
        value_layout = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Arial", 24))

        value_label = QLabel(value)
        value_label.setFont(QFont("Arial", 18, QFont.Bold))
        value_label.setStyleSheet("color: #2ecc71;")

        value_layout.addWidget(icon_label)
        value_layout.addWidget(value_label)
        value_layout.setAlignment(Qt.AlignCenter)

        layout.addWidget(title_label)
        layout.addLayout(value_layout)

        # 保存引用以便更新
        if title == "CO₂减排":
            self.co2_label = value_label
        elif title == "能效提升":
            self.efficiency_label = value_label
        elif title == "节省燃油":
            self.fuel_label = value_label
        elif title == "安全评分":
            self.safety_label = value_label

        return widget

    def create_control_buttons(self, layout):
        """创建控制按钮区域"""
        button_frame = QFrame()
        button_layout = QHBoxLayout(button_frame)

        # 模拟控制按钮
        self.simulate_btn = QPushButton("开始模拟")
        self.simulate_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.simulate_btn.clicked.connect(self.toggle_simulation)

        # 手动触发建议按钮
        self.manual_suggest_btn = QPushButton("手动触发建议")
        self.manual_suggest_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        self.manual_suggest_btn.clicked.connect(self.manual_suggest)

        button_layout.addWidget(self.simulate_btn)
        button_layout.addWidget(self.manual_suggest_btn)
        button_layout.addStretch(1)

        layout.addWidget(button_frame)

    def toggle_simulation(self):
        """切换模拟状态"""
        if self.simulation_active:
            self.timer.stop()
            self.simulate_btn.setText("开始模拟")
            self.simulation_active = False
        else:
            self.timer.start(3000)
            self.simulate_btn.setText("停止模拟")
            self.simulation_active = True

    def auto_update_scenario(self):
        """自动更新场景"""
        self.current_scenario_index = (self.current_scenario_index + 1) % len(self.scenarios)
        self.update_simulation(update_data=True)

    def manual_suggest(self):
        """手动触发建议"""
        self.current_scenario_index = (self.current_scenario_index + 1) % len(self.scenarios)
        self.update_simulation(update_data=True)

    def update_simulation(self, update_data=True):
        """更新模拟数据"""
        try:
            # 获取当前场景
            scenario = self.scenarios[self.current_scenario_index]

            # 获取建议和车辆数据
            rec_type, rec_text, distance, icon = scenario["recommendation"]
            vehicles = scenario["vehicles"]

            # 更新顶部状态栏
            self.recommendation_icon.setText(icon)
            self.recommendation_text.setText(rec_text)
            self.distance_hint.setText(distance)
            self.scenario_label.setText(f"场景: {scenario['name']}")

            # 更新道路视图
            self.road_view.set_recommendation(rec_type)
            self.road_view.update_vehicles(vehicles)

            # 只有在update_data为True时才更新环保数据
            if update_data:
                # 更新环保数据（模拟增长）
                self.co2_saved += random.randint(1, 5)
                self.efficiency = random.randint(1, 10)
                self.fuel_saved = round(self.fuel_saved + random.random() * 0.1, 2)
                self.safety_score = max(85, min(100, self.safety_score + random.randint(-2, 1)))

            # 更新显示
            self.co2_label.setText(f"{self.co2_saved}g")
            self.efficiency_label.setText(f"+{self.efficiency}%")
            self.fuel_label.setText(f"{self.fuel_saved:.1f}L")
            self.safety_label.setText(f"{self.safety_score}")
        except Exception as e:
            print(f"更新模拟错误: {e}")


def main():
    try:
        app = QApplication(sys.argv)
        app.setStyle('Fusion')
        font = QFont("Arial", 10)
        app.setFont(font)
        window = RecommendationApp()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        print(f"应用程序错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()