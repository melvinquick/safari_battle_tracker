import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from .cli import (
    BattleSimulator,
    catch_percentage,
    flee_percentage,
    get_display_name,
    get_games,
    get_pokemon_list,
    modify_catch_factor,
    modify_escape_factor,
)
from .qss_file_handler import QssFileHandler
from .yaml_file_handler import YamlFileHandler

config_file = YamlFileHandler("resources/configs/config.yaml")
config = config_file.load_yaml_file()

themes_file = YamlFileHandler("resources/configs/themes.yaml")
themes = themes_file.load_yaml_file()

qss_file = QssFileHandler("resources/styles/nord.qss")
qss = qss_file.load_qss_file()


class SafariBattleTracker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.theme_name = "dark"
        self.sim = None
        self.pending_action = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(config["window_title"])
        self.setFixedSize(
            config["window_size"]["width"],
            config["window_size"]["height"],
        )
        self.setObjectName("MainWindow")

        central = QWidget()
        central.setObjectName("CentralWidget")
        self.setCentralWidget(central)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setObjectName("CentralWidget")

        scroll_content = QWidget()
        scroll_content.setObjectName("CentralWidget")

        root_layout = QVBoxLayout(scroll_content)
        root_layout.setContentsMargins(24, 24, 24, 24)
        root_layout.setSpacing(16)

        root_layout.addWidget(self.build_top_bar())
        root_layout.addWidget(self.build_selection_section())
        root_layout.addWidget(self.build_stats_section())
        root_layout.addWidget(self.build_actions_section())
        root_layout.addStretch()

        scroll.setWidget(scroll_content)

        outer_layout = QVBoxLayout(central)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(scroll)

        self.apply_theme(self.theme_name)

    def build_top_bar(self):
        top_bar = QFrame()
        top_bar.setObjectName("TopBar")
        top_bar.setFrameShape(QFrame.Shape.NoFrame)
        top_bar.setFixedHeight(48)

        layout = QHBoxLayout(top_bar)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(12)

        app_name = QLabel("Safari Battle Tracker")
        app_name.setObjectName("AppName")

        self.theme_toggle = QPushButton("Switch theme")
        self.theme_toggle.setObjectName("SecondaryButton")
        self.theme_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_toggle.clicked.connect(self.toggle_theme)

        layout.addWidget(app_name)
        layout.addStretch()
        layout.addWidget(self.theme_toggle)

        return top_bar

    def make_section(self, title):
        section = QFrame()
        section.setObjectName("Section")
        section.setFrameShape(QFrame.Shape.NoFrame)

        layout = QVBoxLayout(section)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        section_title = QLabel(title)
        section_title.setObjectName("SectionTitle")
        layout.addWidget(section_title)

        return section, layout

    def build_selection_section(self):
        section, layout = self.make_section("Selection")

        game_row = QHBoxLayout()
        game_row.setSpacing(12)

        game_label = QLabel("Game:")
        game_label.setObjectName("MutedLabel")
        game_label.setFixedWidth(70)

        self.game_combo = QComboBox()
        self.game_combo.setObjectName("ComboBox")
        for game in get_games():
            self.game_combo.addItem(get_display_name(game), game)
        self.game_combo.currentIndexChanged.connect(self.on_game_changed)

        game_row.addWidget(game_label)
        game_row.addWidget(self.game_combo, 1)
        layout.addLayout(game_row)

        poke_row = QHBoxLayout()
        poke_row.setSpacing(12)

        poke_label = QLabel("Pokémon:")
        poke_label.setObjectName("MutedLabel")
        poke_label.setFixedWidth(70)

        self.pokemon_combo = QComboBox()
        self.pokemon_combo.setObjectName("ComboBox")
        self.pokemon_combo.setEnabled(False)
        self.pokemon_combo.currentIndexChanged.connect(self.on_pokemon_changed)

        poke_row.addWidget(poke_label)
        poke_row.addWidget(self.pokemon_combo, 1)
        layout.addLayout(poke_row)

        self.start_button = QPushButton("Start Battle")
        self.start_button.setObjectName("PrimaryButton")
        self.start_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_button.setMinimumHeight(46)
        self.start_button.setEnabled(False)
        self.start_button.clicked.connect(self.start_battle)
        layout.addWidget(self.start_button)

        if get_games():
            self.on_game_changed(0)

        return section

    def build_stats_section(self):
        section, layout = self.make_section("Battle Stats")

        self.pokemon_name_label = QLabel("No battle active")
        self.pokemon_name_label.setObjectName("SectionTitle")
        self.pokemon_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.pokemon_name_label)

        self.turn_label = QLabel("")
        self.turn_label.setObjectName("MutedLabel")
        self.turn_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.turn_label)

        catch_row = QHBoxLayout()
        catch_row.setSpacing(10)

        catch_label = QLabel("Catch:")
        catch_label.setObjectName("MutedLabel")
        catch_label.setFixedWidth(50)

        self.catch_bar = QProgressBar()
        self.catch_bar.setRange(0, 1000)
        self.catch_bar.setValue(0)
        self.catch_bar.setTextVisible(False)
        self.catch_bar.setMinimumHeight(20)

        self.catch_pct_label = QLabel("--%")
        self.catch_pct_label.setObjectName("MutedLabel")
        self.catch_pct_label.setFixedWidth(55)
        self.catch_pct_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )

        catch_row.addWidget(catch_label)
        catch_row.addWidget(self.catch_bar, 1)
        catch_row.addWidget(self.catch_pct_label)
        layout.addLayout(catch_row)

        flee_row = QHBoxLayout()
        flee_row.setSpacing(10)

        flee_label = QLabel("Flee:")
        flee_label.setObjectName("MutedLabel")
        flee_label.setFixedWidth(50)

        self.flee_bar = QProgressBar()
        self.flee_bar.setRange(0, 1000)
        self.flee_bar.setValue(0)
        self.flee_bar.setTextVisible(False)
        self.flee_bar.setMinimumHeight(20)

        self.flee_pct_label = QLabel("--%")
        self.flee_pct_label.setObjectName("MutedLabel")
        self.flee_pct_label.setFixedWidth(55)
        self.flee_pct_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )

        flee_row.addWidget(flee_label)
        flee_row.addWidget(self.flee_bar, 1)
        flee_row.addWidget(self.flee_pct_label)
        layout.addLayout(flee_row)

        return section

    def build_actions_section(self):
        section, layout = self.make_section("Actions")

        action_grid = QGridLayout()
        action_grid.setSpacing(10)

        self.ball_button = QPushButton("Throw Ball")
        self.ball_button.setObjectName("SecondaryButton")
        self.ball_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.ball_button.setMinimumHeight(46)
        self.ball_button.setEnabled(False)
        self.ball_button.clicked.connect(lambda: self.select_action("ball"))

        self.bait_button = QPushButton("Throw Bait")
        self.bait_button.setObjectName("SecondaryButton")
        self.bait_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.bait_button.setMinimumHeight(46)
        self.bait_button.setEnabled(False)
        self.bait_button.clicked.connect(lambda: self.select_action("bait"))

        self.rock_button = QPushButton("Throw Rock")
        self.rock_button.setObjectName("SecondaryButton")
        self.rock_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.rock_button.setMinimumHeight(46)
        self.rock_button.setEnabled(False)
        self.rock_button.clicked.connect(lambda: self.select_action("rock"))

        self.run_button = QPushButton("Run Away")
        self.run_button.setObjectName("SecondaryButton")
        self.run_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.run_button.setMinimumHeight(46)
        self.run_button.setEnabled(False)
        self.run_button.clicked.connect(lambda: self.select_action("run"))

        action_grid.addWidget(self.ball_button, 0, 0)
        action_grid.addWidget(self.bait_button, 0, 1)
        action_grid.addWidget(self.rock_button, 1, 0)
        action_grid.addWidget(self.run_button, 1, 1)

        layout.addLayout(action_grid)

        self.confirm_button = QPushButton("Confirm Action")
        self.confirm_button.setObjectName("PrimaryButton")
        self.confirm_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.confirm_button.setMinimumHeight(46)
        self.confirm_button.setEnabled(False)
        self.confirm_button.clicked.connect(self.confirm_action)
        layout.addWidget(self.confirm_button)

        result_row = QHBoxLayout()
        result_row.setSpacing(10)

        self.caught_button = QPushButton("Caught!")
        self.caught_button.setObjectName("PrimaryButton")
        self.caught_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.caught_button.setMinimumHeight(40)
        self.caught_button.hide()
        self.caught_button.clicked.connect(self.on_caught)

        self.broke_free_button = QPushButton("Broke Free")
        self.broke_free_button.setObjectName("SecondaryButton")
        self.broke_free_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.broke_free_button.setMinimumHeight(40)
        self.broke_free_button.hide()
        self.broke_free_button.clicked.connect(self.on_broke_free)

        self.stayed_button = QPushButton("Stayed")
        self.stayed_button.setObjectName("SecondaryButton")
        self.stayed_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stayed_button.setMinimumHeight(40)
        self.stayed_button.hide()
        self.stayed_button.clicked.connect(self.on_stayed)

        self.fled_button = QPushButton("Fled!")
        self.fled_button.setObjectName("SecondaryButton")
        self.fled_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.fled_button.setMinimumHeight(40)
        self.fled_button.hide()
        self.fled_button.clicked.connect(self.on_fled)

        result_row.addWidget(self.caught_button)
        result_row.addWidget(self.broke_free_button)
        result_row.addWidget(self.stayed_button)
        result_row.addWidget(self.fled_button)

        layout.addLayout(result_row)

        self.result_message_label = QLabel("")
        self.result_message_label.setObjectName("SectionTitle")
        self.result_message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_message_label.hide()
        layout.addWidget(self.result_message_label)

        return section

    def on_game_changed(self, index):
        game_key = self.game_combo.currentData()
        self.pokemon_combo.clear()

        if game_key:
            for poke in get_pokemon_list(game_key):
                self.pokemon_combo.addItem(get_display_name(poke), poke)
            self.pokemon_combo.setEnabled(True)
            if self.pokemon_combo.count() > 0:
                self.on_pokemon_changed(0)
        else:
            self.pokemon_combo.setEnabled(False)
            self.start_button.setEnabled(False)

    def on_pokemon_changed(self, index):
        self.start_button.setEnabled(
            bool(self.game_combo.currentData() and self.pokemon_combo.currentData())
        )

    def select_action(self, action):
        if not self.sim or not self.sim.active:
            return

        self.pending_action = action

        action_buttons = {
            "ball": self.ball_button,
            "bait": self.bait_button,
            "rock": self.rock_button,
            "run": self.run_button,
        }
        for key, btn in action_buttons.items():
            if key == action:
                btn.setObjectName("PrimaryButton")
            else:
                btn.setObjectName("SecondaryButton")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        match action:
            case "ball":
                cf = self.sim.catch_factor
                ef = self.sim.escape_factor
            case "bait":
                cf = modify_catch_factor(self.sim.catch_factor, "bait")
                ef = modify_escape_factor(self.sim.escape_factor, "bait")
            case "rock":
                cf = modify_catch_factor(self.sim.catch_factor, "rock")
                ef = modify_escape_factor(self.sim.escape_factor, "rock")
            case "run":
                self.confirm_button.setEnabled(True)
                self.update_preview_bars(None, None)
                return

        preview_catch = catch_percentage(cf)
        preview_flee = flee_percentage(ef)
        self.update_preview_bars(preview_catch, preview_flee)
        self.confirm_button.setEnabled(True)

    def update_preview_bars(self, catch_pct, flee_pct):
        if catch_pct is None:
            self.catch_pct_label.setText("--%")
            self.catch_bar.setValue(0)
            self.flee_pct_label.setText("--%")
            self.flee_bar.setValue(0)
            return

        self.catch_pct_label.setText(f"{catch_pct}%")
        self.catch_bar.setValue(int(catch_pct * 10))
        self.update_bar_color(self.catch_bar, catch_pct, "catch")

        self.flee_pct_label.setText(f"{flee_pct}%")
        self.flee_bar.setValue(int(flee_pct * 10))
        self.update_bar_color(self.flee_bar, flee_pct, "flee")

    def confirm_action(self):
        if not self.pending_action or not self.sim or not self.sim.active:
            return

        action = self.pending_action
        self.pending_action = None
        self.confirm_button.setEnabled(False)

        for btn in [
            self.ball_button,
            self.bait_button,
            self.rock_button,
            self.run_button,
        ]:
            btn.setObjectName("SecondaryButton")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        match action:
            case "ball":
                self.sim.throw_ball()
                self.update_stats()
                self.set_actions_enabled(False)
                self.hide_result_buttons()
                self.caught_button.show()
                self.broke_free_button.show()
            case "bait":
                self.sim.throw_bait()
                self.update_stats()
                self.prompt_flee_check()
            case "rock":
                self.sim.throw_rock()
                self.update_stats()
                self.prompt_flee_check()
            case "run":
                self.sim.run_away()
                self.end_battle_ui("ran")

    def start_battle(self):
        game = self.game_combo.currentData()
        poke = self.pokemon_combo.currentData()
        self.sim = BattleSimulator(game, poke)
        self.pending_action = None

        self.pokemon_name_label.setText(get_display_name(poke))
        self.update_stats()
        self.set_actions_enabled(True)
        self.hide_result_buttons()
        self.confirm_button.setEnabled(False)
        self.result_message_label.hide()

        self.game_combo.setEnabled(False)
        self.pokemon_combo.setEnabled(False)
        self.start_button.setEnabled(False)

    def on_caught(self):
        self.sim.caught()
        self.end_battle_ui("caught")

    def on_broke_free(self):
        self.sim.broke_free()
        self.hide_result_buttons()
        self.prompt_flee_check()

    def on_stayed(self):
        self.sim.pokemon_stayed()
        self.hide_result_buttons()
        self.set_actions_enabled(True)

    def on_fled(self):
        self.sim.pokemon_fled()
        self.end_battle_ui("fled")

    def prompt_flee_check(self):
        self.set_actions_enabled(False)
        self.hide_result_buttons()
        self.stayed_button.show()
        self.fled_button.show()

    def end_battle_ui(self, result):
        self.hide_result_buttons()
        self.set_actions_enabled(False)
        self.confirm_button.setEnabled(False)
        self.pending_action = None

        pokemon_name = get_display_name(self.pokemon_combo.currentData())

        color_map = {
            "caught": "success-color",
            "fled": "danger-color",
            "ran": "warning-color",
        }
        message_map = {
            "caught": f"Congratulations on catching {pokemon_name}!",
            "fled": f"Oh no! Looks like {pokemon_name} got away!",
            "ran": "You ran away from the battle.",
        }

        color = self.get_theme_color(color_map[result])
        self.pokemon_name_label.setStyleSheet(f"color: {color};")
        self.result_message_label.setText(message_map[result])
        self.result_message_label.setStyleSheet(f"color: {color};")
        self.result_message_label.show()

        self.game_combo.setEnabled(True)
        self.pokemon_combo.setEnabled(True)
        self.start_button.setEnabled(True)
        self.start_button.setText("New Battle")

    def update_stats(self):
        if not self.sim:
            return

        catch_pct = self.sim.get_catch_pct()
        flee_pct = self.sim.get_flee_pct()

        self.catch_pct_label.setText(f"{catch_pct}%")
        self.catch_bar.setValue(min(int(catch_pct * 10), 1000))
        self.update_bar_color(self.catch_bar, catch_pct, "catch")

        self.flee_pct_label.setText(f"{flee_pct}%")
        self.flee_bar.setValue(min(int(flee_pct * 10), 1000))
        self.update_bar_color(self.flee_bar, flee_pct, "flee")

        self.turn_label.setText(f"Turn {self.sim.turn}")

    def update_bar_color(self, bar, pct, kind):
        if kind == "catch":
            if pct < 15:
                color = self.get_theme_color("danger-color")
            elif pct < 35:
                color = self.get_theme_color("warning-color")
            else:
                color = self.get_theme_color("success-color")
        else:
            if pct >= 40:
                color = self.get_theme_color("danger-color")
            elif pct >= 20:
                color = self.get_theme_color("warning-color")
            else:
                color = self.get_theme_color("success-color")

        border_radius = themes["general"]["border-radius"]
        bar.setStyleSheet(
            f"QProgressBar::chunk {{ background-color: {color}; border-radius: {border_radius}; }}"
        )

    def set_actions_enabled(self, enabled):
        self.ball_button.setEnabled(enabled)
        self.bait_button.setEnabled(enabled)
        self.rock_button.setEnabled(enabled)
        self.run_button.setEnabled(enabled)

    def hide_result_buttons(self):
        self.caught_button.hide()
        self.broke_free_button.hide()
        self.stayed_button.hide()
        self.fled_button.hide()

    def toggle_theme(self):
        self.theme_name = "light" if self.theme_name == "dark" else "dark"
        self.apply_theme(self.theme_name)

    def apply_theme(self, theme_name):
        self.theme_name = theme_name if theme_name in themes else "dark"
        self.theme_toggle.setText(
            "Switch to light" if self.theme_name == "dark" else "Switch to dark"
        )

        tokens = {**themes[self.theme_name], **themes["general"]}
        stylesheet = qss
        for key, value in tokens.items():
            stylesheet = stylesheet.replace("{{" + key + "}}", str(value))

        self.setStyleSheet(stylesheet)

        if self.sim and self.sim.active:
            self.update_stats()

    def get_theme_color(self, key):
        return themes[self.theme_name].get(key, themes["general"].get(key, "#88c0d0"))


def main():
    app = QApplication(sys.argv)
    window = SafariBattleTracker()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
