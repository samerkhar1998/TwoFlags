import pygame as p

TRANSLATIONS = {
    "en": {
        "play_vs_ai": "Play vs AI",
        "play_vs_player": "Play vs Player",
        "exit": "Exit",
        "back": "Back",
        "start": "Start",
        "beginner": "Beginner",
        "moderate": "Moderate",
        "hard": "Hard",
        "two_flags": "Two-Flags",
        "choose_mode": "Choose a game mode",
        "game_setup": "Game Setup",
        "mode_human_ai": "Mode: Human (White) vs AI (Black)",
        "mode_human_human": "Mode: Human vs Human",
        "game_time": "Game Time (minutes)",
        "ai_difficulty": "AI Difficulty",
        "custom_setup": "Custom Setup",
        "difficulty_only_ai": "Difficulty is only used in Play vs AI mode.",
        "setup_help": "Format: Wb4 Wa3 Bg7 ... (leave as default if unsure)",
        "minutes_placeholder": "Minutes (e.g. 5)",
        "setup_placeholder": "Board setup (optional)",
        "notice": "Notice",
        "ok": "OK",
        "invalid_time": "Please enter a valid game time in whole minutes.",
        "restart": "Restart",
        "menu": "Menu",
        "main_menu": "Main Menu",
        "game_over": "Game Over",
        "coach_mode": "Coach Mode",
        "status": "Status",
        "coach_on": "ON (C)",
        "coach_off": "OFF (C)",
        "hint": "Hint",
        "analyze": "Analyze",
        "try_again": "Try Again",
        "best_move": "Best Move:",
        "move_grade": "Move Grade:",
        "arabic_explanation": "Explanation:",
        "coach_default_explain": "Press C to enable Coach Mode.",
        "language": "Language",
        "english": "English",
        "arabic": "Arabic",
        "username": "Username",
        "profile_stats": "Progress",
        "level": "Level",
        "xp": "XP",
        "rating": "Rating",
        "games": "Games",
        "wins": "Wins",
        "losses": "Losses",
        "streak": "Streak",
        "best_streak": "Best",
        "difficulty": "Diff",
        "xp_gained": "XP Gained",
        "rating_change": "Rating Change",
        "updated_streak": "Updated Streak",
        "coach_bonus": "Coach Bonus",
        "profile": "Profile",
    },
    "ar": {
        "play_vs_ai": "العب ضد الذكاء",
        "play_vs_player": "العب ضد لاعب",
        "exit": "خروج",
        "back": "رجوع",
        "start": "ابدأ",
        "beginner": "مبتدئ",
        "moderate": "متوسط",
        "hard": "صعب",
        "two_flags": "تو فلاغز",
        "choose_mode": "اختر نمط اللعب",
        "game_setup": "إعداد اللعبة",
        "mode_human_ai": "النمط: لاعب (الأبيض) ضد الذكاء",
        "mode_human_human": "النمط: لاعب ضد لاعب",
        "game_time": "وقت اللعبة (بالدقائق)",
        "ai_difficulty": "مستوى الذكاء",
        "custom_setup": "إعداد مخصص",
        "difficulty_only_ai": "المستوى يستخدم فقط عند اللعب ضد الذكاء.",
        "setup_help": "الصيغة: Wb4 Wa3 Bg7 ... (اتركها افتراضية إن لم تكن متأكدًا)",
        "minutes_placeholder": "الدقائق (مثال: 5)",
        "setup_placeholder": "إعداد الرقعة (اختياري)",
        "notice": "تنبيه",
        "ok": "موافق",
        "invalid_time": "أدخل وقتًا صحيحًا بالدقائق.",
        "restart": "إعادة",
        "menu": "القائمة",
        "main_menu": "القائمة الرئيسية",
        "game_over": "انتهت اللعبة",
        "coach_mode": "وضع المدرب",
        "status": "الحالة",
        "coach_on": "مفعل - C",
        "coach_off": "غير مفعل - C",
        "hint": "تلميح",
        "analyze": "تحليل",
        "try_again": "حاول مرة أخرى",
        "best_move": "أفضل نقلة:",
        "move_grade": "تقييم النقلة:",
        "arabic_explanation": "الشرح:",
        "coach_default_explain": "اضغط C لتفعيل وضع المدرب.",
        "language": "اللغة",
        "english": "English",
        "arabic": "العربية",
        "username": "اسم اللاعب",
        "profile_stats": "التقدم",
        "level": "المستوى",
        "xp": "الخبرة",
        "rating": "التصنيف",
        "games": "الألعاب",
        "wins": "فوز",
        "losses": "خسارة",
        "streak": "السلسلة",
        "best_streak": "أفضل سلسلة",
        "difficulty": "الصعوبة",
        "xp_gained": "الخبرة المكتسبة",
        "rating_change": "تغير التصنيف",
        "updated_streak": "السلسلة الحالية",
        "coach_bonus": "مكافأة المدرب",
        "profile": "الملف",
    },
}


def t(lang, key):
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, key)


class Button:
    """Simple reusable button used across menus and in-game overlays."""

    def __init__(self, rect, label, bg=(58, 81, 107), fg=(245, 247, 250), radius=12):
        self.rect = p.Rect(rect)
        self.label = label
        self.bg = bg
        self.fg = fg
        self.radius = radius

    def draw(self, screen, font, hover=False, language="en"):
        color = tuple(min(255, c + 18) for c in self.bg) if hover else self.bg
        p.draw.rect(screen, color, self.rect, border_radius=self.radius)
        p.draw.rect(screen, (28, 37, 46), self.rect, width=2, border_radius=self.radius)
        text = font.render(_ui_text(self.label, language), True, self.fg)
        text_rect = text.get_rect(center=self.rect.center)
        screen.blit(text, text_rect)

    def contains(self, position):
        return self.rect.collidepoint(position)


class TextInput:
    """Minimal text input field for settings entered in pygame-only UI."""

    def __init__(self, rect, text="", placeholder="", max_chars=120):
        self.rect = p.Rect(rect)
        self.text = text
        self.placeholder = placeholder
        self.active = False
        self.max_chars = max_chars

    def set_active(self, active):
        self.active = active

    def handle_event(self, event):
        if event.type == p.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
            return
        if event.type == p.KEYDOWN and self.active:
            if event.key == p.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key in (p.K_RETURN, p.K_KP_ENTER):
                self.active = False
            elif event.unicode and event.unicode.isprintable() and len(self.text) < self.max_chars:
                self.text += event.unicode

    def draw(self, screen, font, language="en"):
        fill = (249, 250, 252) if self.active else (238, 241, 245)
        p.draw.rect(screen, fill, self.rect, border_radius=8)
        border = (50, 85, 120) if self.active else (165, 176, 190)
        p.draw.rect(screen, border, self.rect, width=2, border_radius=8)

        content = self.text if self.text else self.placeholder
        color = (30, 38, 46) if self.text else (122, 132, 143)
        # Keep input text inside the field when window size changes.
        content = _fit_text_to_width(content, font, self.rect.width - 20)
        txt = font.render(_ui_text(content, language), True, color)
        screen.blit(txt, (self.rect.x + 10, self.rect.y + (self.rect.height - txt.get_height()) // 2))


class Popup:
    """Blocking modal popup used for validation feedback previously shown by PSG."""

    def __init__(self, message, language="en"):
        self.message = message
        self.language = language
        self.ok_button = None

    def draw(self, screen, title_font, body_font, button_font):
        overlay = p.Surface(screen.get_size(), p.SRCALPHA)
        overlay.fill((16, 20, 25, 165))
        screen.blit(overlay, (0, 0))

        width, height = screen.get_size()
        card = p.Rect(width // 2 - 230, height // 2 - 110, 460, 220)
        p.draw.rect(screen, (250, 251, 253), card, border_radius=14)
        p.draw.rect(screen, (44, 57, 74), card, width=2, border_radius=14)

        title = title_font.render(_ui_text(t(self.language, "notice"), self.language), True, (28, 37, 48))
        screen.blit(title, (card.x + 20, card.y + 18))

        wrapped = _wrap_text(self.message, body_font, card.width - 40)
        y = card.y + 62
        for line in wrapped[:4]:
            rendered = body_font.render(_ui_text(line, self.language), True, (62, 72, 84))
            screen.blit(rendered, (card.x + 20, y))
            y += rendered.get_height() + 5

        self.ok_button = Button((card.centerx - 60, card.bottom - 60, 120, 40), t(self.language, "ok"), bg=(67, 104, 145))
        self.ok_button.draw(screen, button_font, hover=self.ok_button.contains(p.mouse.get_pos()), language=self.language)


class startApp:
    """Pregame launcher screen implemented in pygame (no PySimpleGUI dependency)."""

    def __init__(self, username="Player"):
        self.playerOne = True
        self.playerTwo = True
        self.Ip = '127.0.0.1'
        self.Port = 65432
        self.Online = False
        self.time = 5
        self.difficulty = "Moderate"
        self.language = "en"
        self.username = username or "Player"
        self.setup = "Setup Ba7 Bb7 Bc7 Bd7 Be7 Bf7 Bg7 Bh7 Wa2 Wb2 Wc2 Wd2 We2 Wf2 Wg2 Wh2"
        self.exit_requested = False

    def Begin(self):
        p.init()
        screen = p.display.set_mode((1100, 720), p.RESIZABLE)
        p.display.set_caption("Two-Flags")
        clock = p.time.Clock()

        title_font = p.font.SysFont("arial", 54, True)
        body_font = p.font.SysFont("arial", 24)
        small_font = p.font.SysFont("arial", 18)
        button_font = p.font.SysFont("arial", 22, True)

        mode = "menu"
        popup = None

        play_ai_btn = Button((0, 0, 220, 60), t(self.language, "play_vs_ai"))
        play_pvp_btn = Button((0, 0, 220, 60), t(self.language, "play_vs_player"), bg=(72, 106, 91))
        exit_btn = Button((0, 0, 220, 60), t(self.language, "exit"), bg=(125, 69, 69))
        lang_en_btn = Button((0, 0, 118, 38), t("en", "english"), bg=(68, 112, 88))
        lang_ar_btn = Button((0, 0, 118, 38), t("ar", "arabic"), bg=(73, 103, 139))

        back_btn = Button((0, 0, 190, 54), t(self.language, "back"), bg=(93, 101, 113))
        start_btn = Button((0, 0, 190, 54), t(self.language, "start"), bg=(68, 112, 88))
        beginner_btn = Button((0, 0, 130, 42), t(self.language, "beginner"), bg=(91, 110, 130))
        moderate_btn = Button((0, 0, 130, 42), t(self.language, "moderate"), bg=(66, 114, 90))
        hard_btn = Button((0, 0, 130, 42), t(self.language, "hard"), bg=(126, 87, 72))

        time_field = TextInput((0, 0, 380, 46), str(self.time), t(self.language, "minutes_placeholder"), max_chars=3)
        username_field = TextInput((0, 0, 380, 46), self.username, t(self.language, "username"), max_chars=24)
        setup_default = self.setup[6:] if self.setup.startswith("Setup ") else self.setup
        setup_field = TextInput((0, 0, 380, 46), setup_default, t(self.language, "setup_placeholder"), max_chars=110)
        mode_label_key = ""
        ai_mode = False

        running = True
        while running:
            p.display.set_caption(_ui_text(t(self.language, "two_flags"), self.language))
            width, height = screen.get_size()

            # Responsive layout calculations happen once per frame before event handling.
            menu_btn_w = max(220, min(320, int(width * 0.24)))
            menu_btn_h = 60
            menu_x = width // 2 - menu_btn_w // 2
            menu_top = max(220, height // 2 - 80)
            play_ai_btn.rect = p.Rect(menu_x, menu_top, menu_btn_w, menu_btn_h)
            play_pvp_btn.rect = p.Rect(menu_x, menu_top + 78, menu_btn_w, menu_btn_h)
            exit_btn.rect = p.Rect(menu_x, menu_top + 156, menu_btn_w, menu_btn_h)
            lang_en_btn.rect = p.Rect(width - 262, 22, 112, 36)
            lang_ar_btn.rect = p.Rect(width - 138, 22, 112, 36)

            panel_w = max(640, min(760, width - 140))
            panel_h = max(560, min(640, height - 90))
            panel = p.Rect(width // 2 - panel_w // 2, height // 2 - panel_h // 2, panel_w, panel_h)
            field_x = panel.x + 36
            field_w = panel.w - 72

            time_field.rect = p.Rect(field_x, panel.y + 128, field_w, 46)
            username_field.rect = p.Rect(field_x, panel.y + 218, field_w, 46)
            difficulty_y = panel.y + 304
            gap = 14
            diff_w = (field_w - gap * 2) // 3
            beginner_btn.rect = p.Rect(field_x, difficulty_y, diff_w, 42)
            moderate_btn.rect = p.Rect(field_x + diff_w + gap, difficulty_y, diff_w, 42)
            hard_btn.rect = p.Rect(field_x + 2 * (diff_w + gap), difficulty_y, diff_w, 42)

            setup_field.rect = p.Rect(field_x, panel.y + 390, field_w, 46)
            back_btn.rect = p.Rect(field_x, panel.bottom - 78, (field_w - 20) // 2, 54)
            start_btn.rect = p.Rect(back_btn.rect.right + 20, panel.bottom - 78, (field_w - 20) // 2, 54)

            mouse_pos = p.mouse.get_pos()
            for event in p.event.get():
                if event.type == p.QUIT:
                    self.exit_requested = True
                    return
                if event.type == p.VIDEORESIZE:
                    new_w = max(900, event.w)
                    new_h = max(620, event.h)
                    screen = p.display.set_mode((new_w, new_h), p.RESIZABLE)
                    continue

                if popup is not None:
                    if event.type == p.MOUSEBUTTONDOWN and popup.ok_button and popup.ok_button.contains(event.pos):
                        popup = None
                    continue

                if event.type == p.MOUSEBUTTONDOWN:
                    if lang_en_btn.contains(event.pos):
                        self.language = "en"
                        continue
                    if lang_ar_btn.contains(event.pos):
                        self.language = "ar"
                        continue

                if mode == "menu":
                    if event.type == p.MOUSEBUTTONDOWN:
                        if play_ai_btn.contains(event.pos):
                            self.playerOne = True
                            self.playerTwo = False
                            mode_label_key = "mode_human_ai"
                            ai_mode = True
                            mode = "config"
                        elif play_pvp_btn.contains(event.pos):
                            self.playerOne = True
                            self.playerTwo = True
                            mode_label_key = "mode_human_human"
                            ai_mode = False
                            mode = "config"
                        elif exit_btn.contains(event.pos):
                            self.exit_requested = True
                            return
                else:
                    time_field.handle_event(event)
                    username_field.handle_event(event)
                    setup_field.handle_event(event)
                    if event.type == p.MOUSEBUTTONDOWN:
                        if back_btn.contains(event.pos):
                            mode = "menu"
                        elif ai_mode and beginner_btn.contains(event.pos):
                            self.difficulty = "Beginner"
                        elif ai_mode and moderate_btn.contains(event.pos):
                            self.difficulty = "Moderate"
                        elif ai_mode and hard_btn.contains(event.pos):
                            self.difficulty = "Hard"
                        elif start_btn.contains(event.pos):
                            parsed = _parse_minutes(time_field.text) if time_field.text.strip() else self.time
                            if parsed is None:
                                popup = Popup(t(self.language, "invalid_time"), self.language)
                                continue
                            self.time = parsed
                            self.username = username_field.text.strip() or "Player"
                            setup_text = setup_field.text.strip()
                            if setup_text:
                                self.setup = setup_text if setup_text.startswith("Setup ") else "Setup " + setup_text
                            self.Online = False
                            return

            _draw_menu_background(screen)
            width, height = screen.get_size()
            play_ai_btn.label = t(self.language, "play_vs_ai")
            play_pvp_btn.label = t(self.language, "play_vs_player")
            exit_btn.label = t(self.language, "exit")
            back_btn.label = t(self.language, "back")
            start_btn.label = t(self.language, "start")
            beginner_btn.label = t(self.language, "beginner")
            moderate_btn.label = t(self.language, "moderate")
            hard_btn.label = t(self.language, "hard")
            time_field.placeholder = t(self.language, "minutes_placeholder")
            setup_field.placeholder = t(self.language, "setup_placeholder")
            username_field.placeholder = t(self.language, "username")

            if mode == "menu":
                title = title_font.render(_ui_text(t(self.language, "two_flags"), self.language), True, (240, 244, 249))
                subtitle = body_font.render(_ui_text(t(self.language, "choose_mode"), self.language), True, (215, 224, 234))
                screen.blit(title, (width // 2 - title.get_width() // 2, max(82, height // 2 - 210)))
                screen.blit(subtitle, (width // 2 - subtitle.get_width() // 2, max(146, height // 2 - 148)))

                play_ai_btn.draw(screen, button_font, hover=play_ai_btn.contains(mouse_pos), language=self.language)
                play_pvp_btn.draw(screen, button_font, hover=play_pvp_btn.contains(mouse_pos), language=self.language)
                exit_btn.draw(screen, button_font, hover=exit_btn.contains(mouse_pos), language=self.language)
            else:
                p.draw.rect(screen, (245, 247, 250), panel, border_radius=16)
                p.draw.rect(screen, (44, 57, 74), panel, width=2, border_radius=16)

                hdr = p.font.SysFont("arial", 46, True).render(_ui_text(t(self.language, "game_setup"), self.language), True, (30, 42, 56))
                mode_txt = small_font.render(_ui_text(t(self.language, mode_label_key), self.language), True, (87, 101, 116))
                t_label = small_font.render(_ui_text(t(self.language, "game_time"), self.language), True, (30, 42, 56))
                u_label = small_font.render(_ui_text(t(self.language, "username"), self.language), True, (30, 42, 56))
                d_label = small_font.render(_ui_text(t(self.language, "ai_difficulty"), self.language), True, (30, 42, 56))
                s_label = small_font.render(_ui_text(t(self.language, "custom_setup"), self.language), True, (30, 42, 56))

                screen.blit(hdr, (panel.x + 36, panel.y + 24))
                screen.blit(mode_txt, (panel.x + 36, panel.y + 78))
                screen.blit(t_label, (panel.x + 36, panel.y + 104))
                screen.blit(u_label, (panel.x + 36, panel.y + 194))
                screen.blit(d_label, (panel.x + 36, panel.y + 278))
                screen.blit(s_label, (panel.x + 36, panel.y + 364))

                time_field.draw(screen, body_font, language=self.language)
                username_field.draw(screen, body_font, language=self.language)
                setup_field.draw(screen, body_font, language=self.language)
                if ai_mode:
                    beginner_btn.bg = (58, 81, 107) if self.difficulty == "Beginner" else (91, 110, 130)
                    moderate_btn.bg = (51, 100, 77) if self.difficulty == "Moderate" else (66, 114, 90)
                    hard_btn.bg = (113, 74, 60) if self.difficulty == "Hard" else (126, 87, 72)
                    beginner_btn.draw(screen, small_font, hover=beginner_btn.contains(mouse_pos), language=self.language)
                    moderate_btn.draw(screen, small_font, hover=moderate_btn.contains(mouse_pos), language=self.language)
                    hard_btn.draw(screen, small_font, hover=hard_btn.contains(mouse_pos), language=self.language)
                else:
                    ai_text = small_font.render(_ui_text(t(self.language, "difficulty_only_ai"), self.language), True, (102, 113, 125))
                    screen.blit(ai_text, (panel.x + 36, panel.y + 314))

                help_lines = _wrap_text(t(self.language, "setup_help"), small_font, field_w)
                y = panel.y + 446
                for line in help_lines[:2]:
                    help_txt = small_font.render(_ui_text(line, self.language), True, (102, 113, 125))
                    screen.blit(help_txt, (panel.x + 36, y))
                    y += help_txt.get_height() + 2

                back_btn.draw(screen, button_font, hover=back_btn.contains(mouse_pos), language=self.language)
                start_btn.draw(screen, button_font, hover=start_btn.contains(mouse_pos), language=self.language)

            lang_label = small_font.render(_ui_text(t(self.language, "language"), self.language), True, (215, 224, 234))
            screen.blit(lang_label, (width - 380, 28))
            lang_en_btn.bg = (54, 95, 75) if self.language == "en" else (68, 112, 88)
            lang_ar_btn.bg = (56, 83, 115) if self.language == "ar" else (73, 103, 139)
            lang_en_btn.draw(screen, small_font, hover=lang_en_btn.contains(mouse_pos), language=self.language)
            lang_ar_btn.draw(screen, small_font, hover=lang_ar_btn.contains(mouse_pos), language=self.language)

            if popup is not None:
                popup.draw(screen, body_font, small_font, button_font)

            p.display.flip()
            clock.tick(60)


class GameUI:
    """UI renderer for board, side panel, restart controls and game-over overlays."""

    def __init__(self, board_width, board_height, move_log_width, move_log_height, sq_size, dimension, images,
                 language="en"):
        self.board_width = board_width
        self.board_height = board_height
        self.move_log_width = move_log_width
        self.move_log_height = move_log_height
        self.sq_size = sq_size
        self.dimension = dimension
        self.images = images
        self.language = language
        self.side_width = 230
        self.coach_width = 320
        self.total_width = self.board_width + self.side_width + self.move_log_width + self.coach_width
        self.total_height = self.board_height

        self.colors = [(245, 248, 252), (192, 204, 217)]
        self.selected_color = (73, 131, 198, 120)
        self.moves_color = (255, 212, 95, 120)

        self.restart_button = Button((self.board_width + 14, 20, self.side_width - 28, 42), t(self.language, "restart"), bg=(67, 104, 145))
        self.menu_button = Button((self.board_width + 14, 72, self.side_width - 28, 42), t(self.language, "menu"), bg=(73, 103, 139))
        self.over_restart_button = Button((self.board_width // 2 - 200, self.board_height // 2 + 50, 180, 50),
                                          t(self.language, "restart"), bg=(68, 112, 88))
        self.over_menu_button = Button((self.board_width // 2 + 20, self.board_height // 2 + 50, 180, 50),
                                       t(self.language, "main_menu"), bg=(73, 103, 139))
        coach_x = self.board_width + self.side_width + self.move_log_width
        self.coach_panel_rect = p.Rect(coach_x, 0, self.coach_width, self.board_height)
        self.lang_en_button = Button((coach_x + self.coach_width - 196, 20, 86, 34), t("en", "english"), bg=(68, 112, 88))
        self.lang_ar_button = Button((coach_x + self.coach_width - 102, 20, 86, 34), t("ar", "arabic"), bg=(73, 103, 139))
        self.coach_hint_button = Button((coach_x + 20, 92, self.coach_width - 40, 42), t(self.language, "hint"), bg=(67, 104, 145))
        self.coach_analyze_button = Button((coach_x + 20, 144, self.coach_width - 40, 42), t(self.language, "analyze"), bg=(72, 106, 91))
        self.coach_try_again_button = Button((coach_x + 20, 196, self.coach_width - 40, 42), t(self.language, "try_again"),
                                             bg=(125, 88, 75))

    def draw_game_state(self, screen, move_log, gs, valid_moves, sq_selected, move_log_font):
        self._draw_board(screen)
        self._highlight_squares(screen, gs, valid_moves, sq_selected)
        self._draw_pieces(screen, gs)
        self._draw_board_coordinates(screen)
        self._draw_move_log(screen, move_log, move_log_font)

    def draw_side_panel(self, screen, timer_font, white_timer, black_timer, progression_data=None, mouse_pos=None):
        mouse = mouse_pos if mouse_pos is not None else p.mouse.get_pos()
        panel = p.Rect(self.board_width, 0, self.side_width, self.board_height)
        p.draw.rect(screen, (229, 235, 242), panel)
        p.draw.line(screen, (154, 166, 179), (self.board_width, 0), (self.board_width, self.board_height), 2)
        p.draw.line(screen, (154, 166, 179), (self.board_width + self.side_width, 0),
                    (self.board_width + self.side_width, self.board_height), 2)

        self.restart_button.label = t(self.language, "restart")
        self.menu_button.label = t(self.language, "menu")
        self.restart_button.draw(screen, p.font.SysFont("arial", 18, True),
                                 hover=self.restart_button.contains(mouse), language=self.language)
        self.menu_button.draw(screen, p.font.SysFont("arial", 18, True),
                              hover=self.menu_button.contains(mouse), language=self.language)

        # Timers have fixed non-overlapping zones above and below progression block.
        black = timer_font.render(black_timer, True, (32, 41, 52))
        white = timer_font.render(white_timer, True, (32, 41, 52))
        black_y = 150
        white_y = self.board_height - 92
        screen.blit(black, (self.board_width + (self.side_width - black.get_width()) // 2, black_y))
        screen.blit(white, (self.board_width + (self.side_width - white.get_width()) // 2, white_y))

        if progression_data:
            self._draw_progression_block(screen, progression_data)

    def draw_game_over(self, screen, message, progression_result=None, mouse_pos=None):
        mouse = mouse_pos if mouse_pos is not None else p.mouse.get_pos()
        overlay = p.Surface((self.board_width, self.board_height), p.SRCALPHA)
        overlay.fill((16, 23, 31, 180))
        screen.blit(overlay, (0, 0))

        card = p.Rect(self.board_width // 2 - 260, self.board_height // 2 - 155, 520, 320)
        p.draw.rect(screen, (250, 251, 253), card, border_radius=16)
        p.draw.rect(screen, (38, 51, 66), card, width=2, border_radius=16)

        title_font = p.font.SysFont("arial", 32, True)
        body_font = p.font.SysFont("arial", 20)
        button_font = p.font.SysFont("arial", 21, True)

        title = title_font.render(_ui_text(t(self.language, "game_over"), self.language), True, (33, 43, 54))
        screen.blit(title, (card.centerx - title.get_width() // 2, card.y + 24))

        wrapped = _wrap_text(message, body_font, card.width - 40)
        y = card.y + 84
        for line in wrapped[:3]:
            msg = body_font.render(_ui_text(line, self.language), True, (68, 79, 92))
            screen.blit(msg, (card.centerx - msg.get_width() // 2, y))
            y += msg.get_height() + 4

        if progression_result:
            s_font = p.font.SysFont("arial", 18)
            detail_lines = [
                f"{t(self.language, 'xp_gained')}: {progression_result.get('xp_gain', 0)}",
                f"{t(self.language, 'coach_bonus')}: {progression_result.get('coach_bonus', 0):+d}",
                f"{t(self.language, 'rating_change')}: {progression_result.get('rating_delta', 0):+d}",
                f"{t(self.language, 'updated_streak')}: {progression_result.get('win_streak', 0)}",
            ]
            dy = y + 8
            for line in detail_lines:
                msg = s_font.render(_ui_text(line, self.language), True, (56, 68, 82))
                screen.blit(msg, (card.centerx - msg.get_width() // 2, dy))
                dy += msg.get_height() + 2

        self.over_restart_button.label = t(self.language, "restart")
        self.over_menu_button.label = t(self.language, "main_menu")
        self.over_restart_button.draw(screen, button_font, hover=self.over_restart_button.contains(mouse),
                                      language=self.language)
        self.over_menu_button.draw(screen, button_font, hover=self.over_menu_button.contains(mouse),
                                   language=self.language)

    def _draw_progression_block(self, screen, data):
        left = self.board_width + 14
        top = 220
        width = self.side_width - 28
        block = p.Rect(left, top, width, 190)
        p.draw.rect(screen, (236, 241, 246), block, border_radius=10)
        p.draw.rect(screen, (167, 178, 191), block, width=1, border_radius=10)

        title_font = p.font.SysFont("arial", 18, True)
        text_font = p.font.SysFont("arial", 15)
        small_font = p.font.SysFont("arial", 13)

        username = str(data.get("username", "Player"))
        level = int(data.get("level", 1))
        xp = int(data.get("xp", 0))
        next_xp = max(1, int(data.get("next_level_xp", 100)))
        rating = int(data.get("rating", 800))
        diff = str(data.get("difficulty", "moderate"))
        stats = data.get("stats", {})

        y = top + 8
        title = title_font.render(_ui_text(t(self.language, "profile"), self.language), True, (44, 56, 71))
        screen.blit(title, (left + 8, y))
        y += 22
        uline = text_font.render(_ui_text(f"{t(self.language, 'username')}: {username}", self.language), True, (52, 64, 79))
        screen.blit(uline, (left + 8, y))
        y += 18
        lline = text_font.render(_ui_text(f"{t(self.language, 'level')}: {level}   {t(self.language, 'xp')}: {xp}/{next_xp}", self.language), True, (52, 64, 79))
        screen.blit(lline, (left + 8, y))
        y += 20

        bar_bg = p.Rect(left + 8, y, width - 16, 10)
        p.draw.rect(screen, (202, 211, 220), bar_bg, border_radius=5)
        fill = int((bar_bg.width * max(0, min(xp, next_xp))) / next_xp)
        if fill > 0:
            p.draw.rect(screen, (79, 145, 105), p.Rect(bar_bg.x, bar_bg.y, fill, bar_bg.height), border_radius=5)
        y += 16

        rline = text_font.render(_ui_text(f"{t(self.language, 'rating')}: {rating} ({diff})", self.language), True, (52, 64, 79))
        screen.blit(rline, (left + 8, y))
        y += 18
        gline = small_font.render(
            _ui_text(
                f"{t(self.language, 'games')}: {stats.get('games_vs_ai', 0)}   "
                f"{t(self.language, 'wins')}: {stats.get('wins_vs_ai', 0)}   "
                f"{t(self.language, 'losses')}: {stats.get('losses_vs_ai', 0)}",
                self.language,
            ),
            True,
            (76, 89, 103),
        )
        sline = small_font.render(
            _ui_text(
                f"{t(self.language, 'streak')}: {stats.get('win_streak', 0)}   "
                f"{t(self.language, 'best_streak')}: {stats.get('best_streak', 0)}",
                self.language,
            ),
            True,
            (76, 89, 103),
        )
        for rendered in (gline, sline):
            screen.blit(rendered, (left + 8, y))
            y += rendered.get_height() + 2

    def draw_coach_panel(self, screen, coach_state, mouse_pos=None):
        mouse = mouse_pos if mouse_pos is not None else p.mouse.get_pos()
        """
        Draw coach mode controls and educational feedback panel.
        coach_state keys: enabled, best_move, grade, explanation, status
        """
        p.draw.rect(screen, (238, 243, 247), self.coach_panel_rect)
        p.draw.line(screen, (154, 166, 179), (self.coach_panel_rect.x, 0),
                    (self.coach_panel_rect.x, self.coach_panel_rect.height), 2)

        title_font = p.font.SysFont("arial", 24, True)
        small_font = p.font.SysFont("arial", 18)
        body_font = p.font.SysFont("arial", 20)
        button_font = p.font.SysFont("arial", 20, True)

        self.lang_en_button.bg = (54, 95, 75) if self.language == "en" else (68, 112, 88)
        self.lang_ar_button.bg = (56, 83, 115) if self.language == "ar" else (73, 103, 139)
        self.lang_en_button.draw(screen, p.font.SysFont("arial", 14, True),
                                 hover=self.lang_en_button.contains(mouse), language=self.language)
        self.lang_ar_button.draw(screen, p.font.SysFont("arial", 14, True),
                                 hover=self.lang_ar_button.contains(mouse), language=self.language)

        title = title_font.render(_ui_text(t(self.language, "coach_mode"), self.language), True, (37, 49, 62))
        screen.blit(title, (self.coach_panel_rect.x + 20, 62))

        status_text = t(self.language, "coach_on") if coach_state.get("enabled") else t(self.language, "coach_off")
        status = small_font.render(_ui_text(f"{t(self.language, 'status')}: {status_text}", self.language), True, (85, 98, 112))
        screen.blit(status, (self.coach_panel_rect.x + 20, 96))

        self.coach_hint_button.label = t(self.language, "hint")
        self.coach_analyze_button.label = t(self.language, "analyze")
        self.coach_try_again_button.label = t(self.language, "try_again")
        self.coach_hint_button.draw(screen, button_font, hover=self.coach_hint_button.contains(mouse),
                                    language=self.language)
        self.coach_analyze_button.draw(screen, button_font, hover=self.coach_analyze_button.contains(mouse),
                                       language=self.language)
        self.coach_try_again_button.draw(screen, button_font, hover=self.coach_try_again_button.contains(mouse),
                                         language=self.language)

        y = 304
        p.draw.line(screen, (176, 186, 196), (self.coach_panel_rect.x + 20, y - 10),
                    (self.coach_panel_rect.right - 20, y - 10), 1)

        best_move = coach_state.get("best_move", "--")
        grade = coach_state.get("grade", "--")
        explanation = coach_state.get("explanation", t(self.language, "coach_default_explain"))
        status_line = coach_state.get("status", "")

        best_label = small_font.render(_ui_text(t(self.language, "best_move"), self.language), True, (52, 63, 75))
        best_value = body_font.render(_ui_text(best_move, self.language), True, (26, 37, 49))
        grade_label = small_font.render(_ui_text(t(self.language, "move_grade"), self.language), True, (52, 63, 75))
        grade_value = body_font.render(_ui_text(grade, self.language), True, (26, 37, 49))

        screen.blit(best_label, (self.coach_panel_rect.x + 20, y))
        screen.blit(best_value, (self.coach_panel_rect.x + 20, y + 22))
        screen.blit(grade_label, (self.coach_panel_rect.x + 20, y + 66))
        screen.blit(grade_value, (self.coach_panel_rect.x + 20, y + 88))

        explain_label = small_font.render(_ui_text(t(self.language, "arabic_explanation"), self.language), True,
                                          (52, 63, 75))
        if self.language == "ar":
            screen.blit(explain_label, (self.coach_panel_rect.right - 20 - explain_label.get_width(), y + 132))
        else:
            screen.blit(explain_label, (self.coach_panel_rect.x + 20, y + 132))
        lines = _wrap_text(explanation, small_font, self.coach_panel_rect.width - 40)
        text_y = y + 156
        for line in lines[:4]:
            text = small_font.render(_ui_text(line, self.language), True, (37, 48, 61))
            if self.language == "ar":
                screen.blit(text, (self.coach_panel_rect.right - 20 - text.get_width(), text_y))
            else:
                screen.blit(text, (self.coach_panel_rect.x + 20, text_y))
            text_y += text.get_height() + 3

        if status_line:
            footer_lines = _wrap_text(status_line, small_font, self.coach_panel_rect.width - 40)
            footer_y = max(text_y + 8, self.coach_panel_rect.bottom - 52)
            for line in footer_lines[:2]:
                footer = small_font.render(_ui_text(line, self.language), True, (85, 98, 112))
                screen.blit(footer, (self.coach_panel_rect.x + 20, footer_y))
                footer_y += footer.get_height() + 2

    def _draw_board(self, screen):
        for r in range(self.dimension):
            for c in range(self.dimension):
                color = self.colors[(r + c) % 2]
                p.draw.rect(screen, color, p.Rect(c * self.sq_size, r * self.sq_size, self.sq_size, self.sq_size))

    def _draw_board_coordinates(self, screen):
        """
        Draw rank/file guides on the board so players can read rows/columns quickly.
        Files: a-h on bottom row. Ranks: 8-1 on left column.
        """
        font = p.font.SysFont("arial", 14, True)
        files = "abcdefgh"
        ranks = "87654321"

        for col in range(self.dimension):
            text = font.render(files[col], True, (68, 80, 94))
            x = col * self.sq_size + self.sq_size - text.get_width() - 4
            y = self.board_height - text.get_height() - 2
            screen.blit(text, (x, y))

        for row in range(self.dimension):
            text = font.render(ranks[row], True, (68, 80, 94))
            x = 4
            y = row * self.sq_size + 2
            screen.blit(text, (x, y))

    def _highlight_squares(self, screen, gs, valid_moves, sq_selected):
        if sq_selected == ():
            return

        r, c = sq_selected
        if gs.whiteBoard[r * 8 + c] != 1 and gs.blackBoard[r * 8 + c] != 1:
            return

        selected = p.Surface((self.sq_size, self.sq_size), p.SRCALPHA)
        selected.fill(self.selected_color)
        screen.blit(selected, (c * self.sq_size, r * self.sq_size))

        moves = p.Surface((self.sq_size, self.sq_size), p.SRCALPHA)
        moves.fill(self.moves_color)
        for move in valid_moves:
            if move.startRow == r and move.startCol == c:
                screen.blit(moves, (move.endCol * self.sq_size, move.endRow * self.sq_size))

    def _draw_pieces(self, screen, gs):
        for r in range(self.dimension):
            for c in range(self.dimension):
                piece = gs.whiteBoard[r * 8 + c]
                if piece == 1:
                    screen.blit(self.images["wP"], p.Rect(c * self.sq_size, r * self.sq_size, self.sq_size, self.sq_size))
                piece = gs.blackBoard[r * 8 + c]
                if piece == 1:
                    screen.blit(self.images["bP"], p.Rect(c * self.sq_size, r * self.sq_size, self.sq_size, self.sq_size))

    def _draw_move_log(self, screen, move_log, font):
        move_log_rect = p.Rect(self.board_width + self.side_width, 0, self.move_log_width, self.move_log_height)
        p.draw.rect(screen, (34, 39, 47), move_log_rect)

        move_text = []
        for i in range(0, len(move_log), 2):
            move_string = str(i // 2 + 1) + ". " + move_log[i].getFlagsNotation() + " "
            if i + 1 < len(move_log):
                move_string += move_log[i + 1].getFlagsNotation()
            move_text.append(move_string)

        moves_per_row = 3
        padding = 8
        line_spacing = 3
        text_y = padding
        for i in range(0, len(move_text), moves_per_row):
            text = ""
            for j in range(moves_per_row):
                if i + j < len(move_text):
                    text += move_text[i + j] + "    "
            text_object = font.render(text, True, (237, 242, 247))
            text_location = move_log_rect.move(padding, text_y)
            screen.blit(text_object, text_location)
            text_y += text_object.get_height() + line_spacing


def _parse_minutes(value):
    value = value.strip()
    if not value:
        return None
    if not value.isdigit():
        return None
    minutes = int(value)
    if minutes <= 0 or minutes > 180:
        return None
    return minutes


def _draw_menu_background(screen):
    width, height = screen.get_size()
    top = p.Color(26, 39, 56)
    bottom = p.Color(49, 69, 92)

    for y in range(height):
        ratio = y / max(1, height - 1)
        r = int(top.r + (bottom.r - top.r) * ratio)
        g = int(top.g + (bottom.g - top.g) * ratio)
        b = int(top.b + (bottom.b - top.b) * ratio)
        p.draw.line(screen, (r, g, b), (0, y), (width, y))

    p.draw.circle(screen, (72, 94, 122), (width - 80, 90), 130)
    p.draw.circle(screen, (39, 55, 73), (95, height - 90), 160)


def _wrap_text(text, font, max_width):
    words = text.split()
    if not words:
        return [""]

    lines = []
    current = words[0]
    for word in words[1:]:
        test = current + " " + word
        if font.size(test)[0] <= max_width:
            current = test
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def _fit_text_to_width(text, font, max_width):
    """Trim from the left so the latest part of typed text remains visible."""
    if font.size(text)[0] <= max_width:
        return text

    display = text
    while display and font.size(display)[0] > max_width:
        display = display[1:]
    return display


# Minimal Arabic shaping + RTL visual conversion for pygame text rendering.
# pygame does not perform Arabic shaping/bidi by default.
ARABIC_FORMS = {
    "ا": ("\uFE8D", "\uFE8E", None, None),
    "أ": ("\uFE83", "\uFE84", None, None),
    "إ": ("\uFE87", "\uFE88", None, None),
    "آ": ("\uFE81", "\uFE82", None, None),
    "ب": ("\uFE8F", "\uFE90", "\uFE91", "\uFE92"),
    "ت": ("\uFE95", "\uFE96", "\uFE97", "\uFE98"),
    "ث": ("\uFE99", "\uFE9A", "\uFE9B", "\uFE9C"),
    "ج": ("\uFE9D", "\uFE9E", "\uFE9F", "\uFEA0"),
    "ح": ("\uFEA1", "\uFEA2", "\uFEA3", "\uFEA4"),
    "خ": ("\uFEA5", "\uFEA6", "\uFEA7", "\uFEA8"),
    "د": ("\uFEA9", "\uFEAA", None, None),
    "ذ": ("\uFEAB", "\uFEAC", None, None),
    "ر": ("\uFEAD", "\uFEAE", None, None),
    "ز": ("\uFEAF", "\uFEB0", None, None),
    "س": ("\uFEB1", "\uFEB2", "\uFEB3", "\uFEB4"),
    "ش": ("\uFEB5", "\uFEB6", "\uFEB7", "\uFEB8"),
    "ص": ("\uFEB9", "\uFEBA", "\uFEBB", "\uFEBC"),
    "ض": ("\uFEBD", "\uFEBE", "\uFEBF", "\uFEC0"),
    "ط": ("\uFEC1", "\uFEC2", "\uFEC3", "\uFEC4"),
    "ظ": ("\uFEC5", "\uFEC6", "\uFEC7", "\uFEC8"),
    "ع": ("\uFEC9", "\uFECA", "\uFECB", "\uFECC"),
    "غ": ("\uFECD", "\uFECE", "\uFECF", "\uFED0"),
    "ف": ("\uFED1", "\uFED2", "\uFED3", "\uFED4"),
    "ق": ("\uFED5", "\uFED6", "\uFED7", "\uFED8"),
    "ك": ("\uFED9", "\uFEDA", "\uFEDB", "\uFEDC"),
    "ل": ("\uFEDD", "\uFEDE", "\uFEDF", "\uFEE0"),
    "م": ("\uFEE1", "\uFEE2", "\uFEE3", "\uFEE4"),
    "ن": ("\uFEE5", "\uFEE6", "\uFEE7", "\uFEE8"),
    "ه": ("\uFEE9", "\uFEEA", "\uFEEB", "\uFEEC"),
    "و": ("\uFEED", "\uFEEE", None, None),
    "ؤ": ("\uFE85", "\uFE86", None, None),
    "ي": ("\uFEF1", "\uFEF2", "\uFEF3", "\uFEF4"),
    "ى": ("\uFEEF", "\uFEF0", None, None),
    "ئ": ("\uFE89", "\uFE8A", "\uFE8B", "\uFE8C"),
    "ة": ("\uFE93", "\uFE94", None, None),
}

NON_CONNECT_NEXT = {"ا", "أ", "إ", "آ", "د", "ذ", "ر", "ز", "و", "ؤ", "ى", "ة"}


def _arabic_visual(text):
    """Return a visually-correct (shaped + RTL) string for pygame rendering."""
    chars = list(text)
    shaped = []

    for i, ch in enumerate(chars):
        forms = ARABIC_FORMS.get(ch)
        if forms is None:
            shaped.append(ch)
            continue

        prev_ch = chars[i - 1] if i > 0 else ""
        next_ch = chars[i + 1] if i + 1 < len(chars) else ""

        prev_join = (
            prev_ch in ARABIC_FORMS
            and prev_ch not in NON_CONNECT_NEXT
            and forms[1] is not None
        )
        next_join = (
            next_ch in ARABIC_FORMS
            and ch not in NON_CONNECT_NEXT
            and ARABIC_FORMS[next_ch][1] is not None
        )

        isolated, final, initial, medial = forms
        if prev_join and next_join and medial is not None:
            shaped.append(medial)
        elif prev_join and final is not None:
            shaped.append(final)
        elif next_join and initial is not None:
            shaped.append(initial)
        else:
            shaped.append(isolated)

    # Reverse for RTL visual ordering in a non-bidi renderer.
    return "".join(shaped)[::-1]


def _ui_text(text, language):
    """Render-safe UI text according to selected language."""
    return _arabic_visual(text) if _contains_arabic(text) else text


def _contains_arabic(text):
    for ch in text:
        if '\u0600' <= ch <= '\u06FF' or '\u0750' <= ch <= '\u077F' or '\u08A0' <= ch <= '\u08FF':
            return True
    return False
