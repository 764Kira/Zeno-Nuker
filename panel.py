import sys
import os
import json
import threading
import asyncio
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QTextEdit, QComboBox, QSpinBox,
    QFrame, QFileDialog, QSizePolicy, QStackedWidget, QGridLayout
)
from PyQt5.QtCore import Qt, QPoint, pyqtSignal, QSize, QTimer
from PyQt5.QtGui import (
    QColor, QFont, QFontDatabase, QPainter,
    QPainterPath, QBrush, QPen, QLinearGradient, QCursor, QPixmap
)
from bot import RecoveryBot

CONFIG_FILE = "config.json"


def load_token():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                return data.get("token", "")
        except:
            pass
    return ""


def save_token(token):
    with open(CONFIG_FILE, "w") as f:
        json.dump({"token": token}, f)


# ════════════════════════════════════
#  CUSTOM WIDGETS
# ════════════════════════════════════

class TitleBar(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_window = parent
        self.setFixedHeight(38)
        self._drag_pos = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 8, 0)
        layout.setSpacing(6)

        dot = QLabel()
        dot.setFixedSize(8, 8)
        dot.setStyleSheet("background: #7c3aed; border-radius: 4px;")
        layout.addWidget(dot)

        title = QLabel("ZENO SOLUTIONS")
        title.setStyleSheet("""
            color: #7c3aed;
            font-size: 11px;
            font-weight: bold;
            letter-spacing: 3px;
        """)
        layout.addWidget(title)
        layout.addStretch()

        ver = QLabel("v1.0")
        ver.setStyleSheet("color: #2a2a40; font-size: 9px; font-weight: bold;")
        layout.addWidget(ver)

        for text, hover_bg in [("-", "#374151"), ("x", "#dc2626")]:
            btn = QPushButton(text)
            btn.setFixedSize(28, 28)
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: #3a3a55;
                    border: none;
                    border-radius: 6px;
                    font-size: 11px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background: {hover_bg};
                    color: #e5e7eb;
                }}
            """)
            if text == "-":
                btn.clicked.connect(parent.showMinimized)
            else:
                btn.clicked.connect(parent.close)
            layout.addWidget(btn)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.parent_window.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() & Qt.LeftButton:
            self.parent_window.move(event.globalPos() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None


class ActionCard(QPushButton):
    def __init__(self, label, color="#7c3aed"):
        super().__init__(label)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setFixedHeight(44)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setStyleSheet(f"""
            QPushButton {{
                background: #111120;
                color: #8b8ba0;
                border: 1px solid #1a1a30;
                border-radius: 8px;
                font-size: 11px;
                font-weight: bold;
                padding: 4px 10px;
            }}
            QPushButton:hover {{
                background: #1a1a30;
                color: {color};
                border: 1px solid {color}66;
            }}
            QPushButton:pressed {{
                background: {color}22;
                border: 1px solid {color};
            }}
        """)


class SectionLabel(QLabel):
    def __init__(self, text):
        super().__init__(text)
        self.setStyleSheet("""
            color: #2a2a44;
            font-size: 9px;
            font-weight: bold;
            letter-spacing: 2.5px;
            padding: 3px 0 1px 2px;
        """)


class Separator(QFrame):
    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.HLine)
        self.setStyleSheet("background: #16162a; max-height: 1px;")


def make_input(placeholder):
    inp = QLineEdit()
    inp.setPlaceholderText(placeholder)
    inp.setFixedHeight(34)
    inp.setStyleSheet("""
        QLineEdit {
            background: #0d0d1a;
            color: #c5c5d5;
            border: 1px solid #1a1a30;
            border-radius: 8px;
            padding: 0 10px;
            font-size: 11px;
        }
        QLineEdit:focus {
            border: 1px solid #7c3aed;
            background: #0f0f20;
        }
    """)
    return inp


def make_spin(max_val=500):
    spin = QSpinBox()
    spin.setRange(1, max_val)
    spin.setValue(10)
    spin.setFixedSize(55, 34)
    spin.setStyleSheet("""
        QSpinBox {
            background: #0d0d1a;
            color: #c5c5d5;
            border: 1px solid #1a1a30;
            border-radius: 8px;
            padding: 0 6px;
            font-size: 11px;
        }
        QSpinBox::up-button, QSpinBox::down-button {
            width: 14px; border: none; background: #1a1a30;
        }
        QSpinBox::up-button:hover, QSpinBox::down-button:hover {
            background: #252540;
        }
    """)
    return spin


def make_btn(text, color="#7c3aed"):
    btn = QPushButton(text)
    btn.setCursor(QCursor(Qt.PointingHandCursor))
    btn.setFixedHeight(34)
    btn.setStyleSheet(f"""
        QPushButton {{
            background: {color};
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 11px;
            font-weight: bold;
            padding: 0 14px;
        }}
        QPushButton:hover {{
            background: {color}cc;
        }}
        QPushButton:pressed {{
            background: {color}aa;
        }}
    """)
    return btn


# ════════════════════════════════════
#  MAIN PANEL
# ════════════════════════════════════

class MainPanel(QWidget):
    log_signal = pyqtSignal(str)
    ready_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.bot = RecoveryBot(
            log_callback=self._emit_log,
            on_ready_callback=self._on_bot_ready
        )
        self.bot_thread = None
        self.connected = False
        self.selected_guild_id = None
        self.selected_guild_name = None

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowMinimizeButtonHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(460, 680) # Increased height for spam
        self._center_on_screen()

        self.log_signal.connect(self._append_log)
        self.ready_signal.connect(self._on_ready_ui)
        self._build_ui()

        saved = load_token()
        if saved:
            self.token_input.setText(saved)

    def _center_on_screen(self):
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 14, 14)

        grad = QLinearGradient(0, 0, 0, self.height())
        grad.setColorAt(0, QColor("#0e0e1a"))
        grad.setColorAt(0.4, QColor("#0b0b16"))
        grad.setColorAt(1, QColor("#080812"))
        painter.fillPath(path, QBrush(grad))

        painter.setPen(QPen(QColor(124, 58, 237, 25), 1.0))
        painter.drawPath(path)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.title_bar = TitleBar(self)
        root.addWidget(self.title_bar)

        self.stack = QStackedWidget()
        root.addWidget(self.stack)

        self.stack.addWidget(self._build_token_screen())
        self.stack.addWidget(self._build_server_screen())
        self.stack.addWidget(self._build_main_screen())
        self.stack.setCurrentIndex(0)

    # ─────────────────────────
    #  SCREEN 1: TOKEN
    # ─────────────────────────
    def _build_token_screen(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 36, 40, 28)
        layout.setSpacing(10)

        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo1.png")
        if os.path.exists(logo_path):
            logo_pixmap = QPixmap(logo_path).scaled(56, 56, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label = QLabel()
            logo_label.setPixmap(logo_pixmap)
            logo_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(logo_label)
        else:
            spacer = QLabel()
            spacer.setFixedHeight(20)
            layout.addWidget(spacer)

        title = QLabel("Zeno Solutions")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #e0e0f0; font-size: 20px; font-weight: bold; letter-spacing: 1px;")
        layout.addWidget(title)

        sub = QLabel("Authentifizierung erforderlich")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet("color: #3a3a55; font-size: 10px; letter-spacing: 1px;")
        layout.addWidget(sub)

        layout.addSpacing(12)

        token_label = QLabel("BOT TOKEN")
        token_label.setStyleSheet("color: #3a3a55; font-size: 9px; font-weight: bold; letter-spacing: 2px;")
        layout.addWidget(token_label)

        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("Token einfuegen...")
        self.token_input.setEchoMode(QLineEdit.Password)
        self.token_input.setFixedHeight(40)
        self.token_input.setStyleSheet("""
            QLineEdit {
                background: #0a0a16;
                color: #c5c5d5;
                border: 1px solid #1a1a30;
                border-radius: 8px;
                padding: 0 14px;
                font-size: 12px;
                font-family: 'Consolas', monospace;
            }
            QLineEdit:focus {
                border: 1px solid #7c3aed;
                background: #0d0d1e;
            }
        """)
        layout.addWidget(self.token_input)

        layout.addSpacing(4)

        self.connect_btn = QPushButton("VERBINDEN")
        self.connect_btn.setFixedHeight(40)
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6d28d9, stop:1 #7c3aed);
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 12px;
                letter-spacing: 2px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7c3aed, stop:1 #8b5cf6);
            }
            QPushButton:disabled {
                background: #141425;
                color: #2a2a44;
            }
        """)
        self.connect_btn.clicked.connect(self._connect_bot)
        layout.addWidget(self.connect_btn)

        status_row = QHBoxLayout()
        status_row.setSpacing(6)
        self.status_dot = QLabel()
        self.status_dot.setFixedSize(6, 6)
        self.status_dot.setStyleSheet("background: #ef4444; border-radius: 3px;")
        status_row.addStretch()
        status_row.addWidget(self.status_dot)
        self.status_label = QLabel("Offline")
        self.status_label.setStyleSheet("color: #3a3a55; font-size: 10px; font-weight: bold;")
        status_row.addWidget(self.status_label)
        status_row.addStretch()
        layout.addLayout(status_row)

        layout.addSpacing(6)

        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet("""
            QTextEdit {
                background: #080812;
                color: #3a3a55;
                border: 1px solid #12121e;
                border-radius: 8px;
                padding: 8px;
                font-family: 'Consolas', monospace;
                font-size: 10px;
            }
        """)
        layout.addWidget(self.log_area)

        return page

    # ─────────────────────────
    #  SCREEN 2: SERVER SELECT
    # ─────────────────────────
    def _build_server_screen(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 36, 40, 28)
        layout.setSpacing(10)

        title = QLabel("Server Auswahl")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #e0e0f0; font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        sub = QLabel("Ziel-Server waehlen")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet("color: #3a3a55; font-size: 10px; letter-spacing: 1px;")
        layout.addWidget(sub)

        layout.addSpacing(14)

        label = QLabel("SERVER")
        label.setStyleSheet("color: #3a3a55; font-size: 9px; font-weight: bold; letter-spacing: 2px;")
        layout.addWidget(label)

        self.server_combo = QComboBox()
        self.server_combo.setFixedHeight(40)
        self.server_combo.setStyleSheet("""
            QComboBox {
                background: #0a0a16;
                color: #c5c5d5;
                border: 1px solid #1a1a30;
                border-radius: 8px;
                padding: 0 14px;
                font-size: 12px;
            }
            QComboBox:focus { border: 1px solid #7c3aed; }
            QComboBox::drop-down { border: none; width: 28px; }
            QComboBox QAbstractItemView {
                background: #0a0a16;
                color: #c5c5d5;
                border: 1px solid #1a1a30;
                selection-background-color: #7c3aed;
            }
        """)
        layout.addWidget(self.server_combo)

        layout.addSpacing(4)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        refresh_btn = make_btn("AKTUALISIEREN", "#1a1a30")
        refresh_btn.setFixedHeight(36)
        refresh_btn.clicked.connect(self._refresh_servers)
        btn_row.addWidget(refresh_btn)

        select_btn = make_btn("AUSWAEHLEN", "#059669")
        select_btn.setFixedHeight(36)
        select_btn.clicked.connect(self._select_server)
        btn_row.addWidget(select_btn)
        layout.addLayout(btn_row)

        layout.addSpacing(8)

        back_btn = QPushButton("Zurueck & Trennen")
        back_btn.setFixedHeight(30)
        back_btn.clicked.connect(self._back_to_token)
        back_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #2a2a44;
                border: 1px solid #16162a;
                border-radius: 6px;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover { color: #ef4444; border-color: #ef4444; }
        """)
        layout.addWidget(back_btn)

        self.server_log = QTextEdit()
        self.server_log.setReadOnly(True)
        self.server_log.setStyleSheet("""
            QTextEdit {
                background: #080812;
                color: #3a3a55;
                border: 1px solid #12121e;
                border-radius: 8px;
                padding: 8px;
                font-family: 'Consolas', monospace;
                font-size: 10px;
            }
        """)
        layout.addWidget(self.server_log)

        return page

    # ─────────────────────────
    #  SCREEN 3: MAIN PANEL
    # ─────────────────────────
    def _build_main_screen(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(14, 6, 14, 10)
        layout.setSpacing(4)

        top = QHBoxLayout()
        top.setSpacing(6)
        self.guild_info_label = QLabel("Kein Server")
        self.guild_info_label.setStyleSheet("color: #7c3aed; font-size: 11px; font-weight: bold; letter-spacing: 1px;")
        top.addWidget(self.guild_info_label)
        top.addStretch()

        back_btn = QPushButton("Server wechseln")
        back_btn.setFixedHeight(24)
        back_btn.clicked.connect(self._back_to_servers)
        back_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #2a2a44;
                border: 1px solid #16162a;
                border-radius: 5px;
                font-size: 9px;
                font-weight: bold;
                padding: 0 8px;
            }
            QPushButton:hover { color: #a78bfa; border-color: #7c3aed; }
        """)
        top.addWidget(back_btn)
        layout.addLayout(top)

        layout.addWidget(Separator())

        # ACTIONS
        layout.addWidget(SectionLabel("AKTIONEN"))
        grid = QGridLayout()
        grid.setSpacing(5)
        cards = [
            ("Kanaele loeschen", "#dc2626", self._delete_all_channels),
            ("Alle bannen", "#dc2626", self._ban_all),
            ("Rollen loeschen", "#ea580c", self._delete_all_roles),
            ("Alle entbannen", "#ea580c", self._unban_all),
        ]
        for i, (label, color, action) in enumerate(cards):
            card = ActionCard(label, color)
            card.clicked.connect(action)
            grid.addWidget(card, i // 2, i % 2)
        layout.addLayout(grid)

        # SPAM (NEW SECTION)
        layout.addWidget(SectionLabel("SPAM"))
        r_spam = QHBoxLayout()
        r_spam.setSpacing(5)
        self.spam_msg_input = make_input("Spam Nachricht...")
        r_spam.addWidget(self.spam_msg_input)
        self.spam_spin = make_spin(100)
        self.spam_spin.setValue(5)
        r_spam.addWidget(self.spam_spin)
        btn_spam = make_btn("Spam", "#7c3aed")
        btn_spam.setFixedSize(65, 34)
        btn_spam.clicked.connect(self._spam_channels)
        r_spam.addWidget(btn_spam)
        layout.addLayout(r_spam)

        # SERVER
        layout.addWidget(SectionLabel("SERVER"))
        r1 = QHBoxLayout()
        r1.setSpacing(5)
        self.server_name_input = make_input("Server-Name...")
        r1.addWidget(self.server_name_input)
        btn_rename = make_btn("Rename", "#7c3aed")
        btn_rename.setFixedSize(70, 34)
        btn_rename.clicked.connect(self._change_server_name)
        r1.addWidget(btn_rename)
        layout.addLayout(r1)

        r2 = QHBoxLayout()
        r2.setSpacing(5)
        self.icon_path_input = make_input("Icon-Pfad/URL...")
        r2.addWidget(self.icon_path_input)
        btn_browse = QPushButton("...")
        btn_browse.setFixedSize(34, 34)
        btn_browse.setStyleSheet("""
            QPushButton { background: #111120; color: #6b6b85; border: 1px solid #1a1a30; border-radius: 8px; font-weight: bold; }
            QPushButton:hover { background: #1a1a30; color: #a78bfa; }
        """)
        btn_browse.clicked.connect(self._browse_icon)
        r2.addWidget(btn_browse)
        btn_icon = make_btn("Icon", "#7c3aed")
        btn_icon.setFixedSize(50, 34)
        btn_icon.clicked.connect(self._change_icon)
        r2.addWidget(btn_icon)
        layout.addLayout(r2)

        r3 = QHBoxLayout()
        r3.setSpacing(5)
        self.rename_ch_input = make_input("Kanaele umbenennen...")
        r3.addWidget(self.rename_ch_input)
        btn_rn = make_btn("Rename", "#2563eb")
        btn_rn.setFixedSize(70, 34)
        btn_rn.clicked.connect(self._rename_all_channels)
        r3.addWidget(btn_rn)
        layout.addLayout(r3)

        # CREATE
        layout.addWidget(SectionLabel("ERSTELLEN"))
        r4 = QHBoxLayout()
        r4.setSpacing(5)
        self.ch_name_input = make_input("Kanal...")
        r4.addWidget(self.ch_name_input)
        self.ch_spin = make_spin(500)
        r4.addWidget(self.ch_spin)
        btn_ch = make_btn("Create", "#059669")
        btn_ch.setFixedSize(55, 34)
        btn_ch.clicked.connect(self._create_channels)
        r4.addWidget(btn_ch)
        layout.addLayout(r4)

        r5 = QHBoxLayout()
        r5.setSpacing(5)
        self.role_name_input = make_input("Rolle...")
        r5.addWidget(self.role_name_input)
        self.role_spin = make_spin(250)
        r5.addWidget(self.role_spin)
        btn_rl = make_btn("Create", "#059669")
        btn_rl.setFixedSize(55, 34)
        btn_rl.clicked.connect(self._create_roles)
        r5.addWidget(btn_rl)
        layout.addLayout(r5)

        # LOG
        layout.addWidget(SectionLabel("LOG"))
        self.main_log = QTextEdit()
        self.main_log.setReadOnly(True)
        self.main_log.setStyleSheet("""
            QTextEdit { background: #080812; color: #3a3a55; border: 1px solid #12121e; border-radius: 8px; padding: 6px; font-family: 'Consolas', monospace; font-size: 10px; }
        """)
        self.main_log.setMinimumHeight(60)
        layout.addWidget(self.main_log)

        return page

    # BOT METHODS
    def _on_bot_ready(self):
        self.ready_signal.emit()

    def _on_ready_ui(self):
        self.connected = True
        self.status_dot.setStyleSheet("background: #22c55e; border-radius: 3px;")
        self.status_label.setText("Online")
        self.status_label.setStyleSheet("color: #22c55e; font-size: 10px; font-weight: bold;")
        self.connect_btn.setEnabled(True)
        self.connect_btn.setText("VERBINDEN")
        self._refresh_servers()
        self.stack.setCurrentIndex(1)

    def _connect_bot(self):
        token = self.token_input.text().strip()
        if not token: return
        save_token(token)
        self._append_log("[...] Verbinde...")
        self.connect_btn.setEnabled(False)
        self.connect_btn.setText("VERBINDE...")
        def run_bot():
            self.bot.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.bot.loop)
            try:
                self.bot.loop.run_until_complete(self.bot.client.start(token))
            except Exception as e:
                self._emit_log(f"[ERROR] {e}")
                self.connected = False
                self.connect_btn.setEnabled(True)
                self.connect_btn.setText("VERBINDEN")
        threading.Thread(target=run_bot, daemon=True).start()

    def _disconnect_bot(self):
        if self.bot.loop and self.bot.loop.is_running():
            asyncio.run_coroutine_threadsafe(self.bot.client.close(), self.bot.loop)
        self.connected = False
        self.status_dot.setStyleSheet("background: #ef4444; border-radius: 3px;")
        self.status_label.setText("Offline")
        self.status_label.setStyleSheet("color: #3a3a55; font-size: 10px; font-weight: bold;")
        self.server_combo.clear()
        self.connect_btn.setEnabled(True)
        self.connect_btn.setText("VERBINDEN")

    def _back_to_token(self):
        self._disconnect_bot()
        self.stack.setCurrentIndex(0)

    def _back_to_servers(self):
        self.selected_guild_id = None
        self._refresh_servers()
        self.stack.setCurrentIndex(1)

    def _select_server(self):
        idx = self.server_combo.currentIndex()
        if idx < 0: return
        self.selected_guild_id = self.server_combo.itemData(idx)
        self.selected_guild_name = self.server_combo.currentText()
        self.guild_info_label.setText(self.selected_guild_name)
        self.stack.setCurrentIndex(2)

    def _refresh_servers(self):
        self.server_combo.clear()
        for name, gid in self.bot.get_guilds():
            self.server_combo.addItem(name, gid)

    # ACTIONS
    def _get_guild(self): return self.selected_guild_id

    def _delete_all_channels(self):
        g = self._get_guild()
        if g: self.bot.delete_all_channels(g)

    def _ban_all(self):
        g = self._get_guild()
        if g: self.bot.ban_all_members(g)

    def _delete_all_roles(self):
        g = self._get_guild()
        if g: self.bot.delete_all_roles(g)

    def _unban_all(self):
        g = self._get_guild()
        if g: self.bot.unban_all(g)

    def _change_server_name(self):
        g = self._get_guild()
        n = self.server_name_input.text().strip()
        if g and n: self.bot.change_server_name(g, n)

    def _change_icon(self):
        g = self._get_guild()
        p = self.icon_path_input.text().strip()
        if g and p: self.bot.change_server_icon(g, p)

    def _browse_icon(self):
        path, _ = QFileDialog.getOpenFileName(self, "Icon", "", "Images (*.png *.jpg *.jpeg *.gif *.webp)")
        if path: self.icon_path_input.setText(path)

    def _rename_all_channels(self):
        g = self._get_guild()
        n = self.rename_ch_input.text().strip()
        if g and n: self.bot.rename_all_channels(g, n)

    def _create_channels(self):
        g = self._get_guild()
        n = self.ch_name_input.text().strip()
        a = self.ch_spin.value()
        if g and n: self.bot.create_channels(g, n, a)

    def _create_roles(self):
        g = self._get_guild()
        n = self.role_name_input.text().strip()
        a = self.role_spin.value()
        if g and n: self.bot.create_roles(g, n, a)

    def _spam_channels(self):
        g = self._get_guild()
        m = self.spam_msg_input.text().strip()
        a = self.spam_spin.value()
        if g and m:
            self.bot.spam_all_channels(g, m, a)
        elif not m:
            self.main_log.append("[ERROR] Nachricht eingeben!")

    def _emit_log(self, msg): self.log_signal.emit(msg)
    def _append_log(self, msg):
        self.log_area.append(msg)
        if self.stack.currentIndex() == 2: self.main_log.append(msg)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainPanel()
    window.show()
    sys.exit(app.exec_())
