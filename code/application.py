import pygame as p


class Button:
    """Simple reusable button used across menus and in-game overlays."""

    def __init__(self, rect, label, bg=(58, 81, 107), fg=(245, 247, 250), radius=12):
        self.rect = p.Rect(rect)
        self.label = label
        self.bg = bg
        self.fg = fg
        self.radius = radius

    def draw(self, screen, font, hover=False):
        color = tuple(min(255, c + 18) for c in self.bg) if hover else self.bg
        p.draw.rect(screen, color, self.rect, border_radius=self.radius)
        p.draw.rect(screen, (28, 37, 46), self.rect, width=2, border_radius=self.radius)
        text = font.render(self.label, True, self.fg)
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

    def draw(self, screen, font):
        fill = (249, 250, 252) if self.active else (238, 241, 245)
        p.draw.rect(screen, fill, self.rect, border_radius=8)
        border = (50, 85, 120) if self.active else (165, 176, 190)
        p.draw.rect(screen, border, self.rect, width=2, border_radius=8)

        content = self.text if self.text else self.placeholder
        color = (30, 38, 46) if self.text else (122, 132, 143)
        # Keep input text inside the field when window size changes.
        content = _fit_text_to_width(content, font, self.rect.width - 20)
        txt = font.render(content, True, color)
        screen.blit(txt, (self.rect.x + 10, self.rect.y + (self.rect.height - txt.get_height()) // 2))


class Popup:
    """Blocking modal popup used for validation feedback previously shown by PSG."""

    def __init__(self, message):
        self.message = message
        self.ok_button = None

    def draw(self, screen, title_font, body_font, button_font):
        overlay = p.Surface(screen.get_size(), p.SRCALPHA)
        overlay.fill((16, 20, 25, 165))
        screen.blit(overlay, (0, 0))

        width, height = screen.get_size()
        card = p.Rect(width // 2 - 230, height // 2 - 110, 460, 220)
        p.draw.rect(screen, (250, 251, 253), card, border_radius=14)
        p.draw.rect(screen, (44, 57, 74), card, width=2, border_radius=14)

        title = title_font.render("Notice", True, (28, 37, 48))
        screen.blit(title, (card.x + 20, card.y + 18))

        wrapped = _wrap_text(self.message, body_font, card.width - 40)
        y = card.y + 62
        for line in wrapped[:4]:
            rendered = body_font.render(line, True, (62, 72, 84))
            screen.blit(rendered, (card.x + 20, y))
            y += rendered.get_height() + 5

        self.ok_button = Button((card.centerx - 60, card.bottom - 60, 120, 40), "OK", bg=(67, 104, 145))
        self.ok_button.draw(screen, button_font, hover=self.ok_button.contains(p.mouse.get_pos()))


class startApp:
    """Pregame launcher screen implemented in pygame (no PySimpleGUI dependency)."""

    def __init__(self):
        self.playerOne = True
        self.playerTwo = True
        self.Ip = '127.0.0.1'
        self.Port = 65432
        self.Online = False
        self.time = 5
        self.difficulty = "Moderate"
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

        play_ai_btn = Button((0, 0, 220, 60), "Play vs AI")
        play_pvp_btn = Button((0, 0, 220, 60), "Play vs Player", bg=(72, 106, 91))
        exit_btn = Button((0, 0, 220, 60), "Exit", bg=(125, 69, 69))

        back_btn = Button((0, 0, 190, 54), "Back", bg=(93, 101, 113))
        start_btn = Button((0, 0, 190, 54), "Start", bg=(68, 112, 88))
        beginner_btn = Button((0, 0, 130, 42), "Beginner", bg=(91, 110, 130))
        moderate_btn = Button((0, 0, 130, 42), "Moderate", bg=(66, 114, 90))
        hard_btn = Button((0, 0, 130, 42), "Hard", bg=(126, 87, 72))

        time_field = TextInput((0, 0, 380, 46), str(self.time), "Minutes (e.g. 5)", max_chars=3)
        setup_default = self.setup[6:] if self.setup.startswith("Setup ") else self.setup
        setup_field = TextInput((0, 0, 380, 46), setup_default, "Board setup (optional)", max_chars=110)
        mode_label = ""
        ai_mode = False

        running = True
        while running:
            width, height = screen.get_size()

            # Responsive layout calculations happen once per frame before event handling.
            menu_btn_w = max(220, min(320, int(width * 0.24)))
            menu_btn_h = 60
            menu_x = width // 2 - menu_btn_w // 2
            menu_top = max(220, height // 2 - 80)
            play_ai_btn.rect = p.Rect(menu_x, menu_top, menu_btn_w, menu_btn_h)
            play_pvp_btn.rect = p.Rect(menu_x, menu_top + 78, menu_btn_w, menu_btn_h)
            exit_btn.rect = p.Rect(menu_x, menu_top + 156, menu_btn_w, menu_btn_h)

            panel_w = max(640, min(760, width - 140))
            panel_h = max(480, min(560, height - 120))
            panel = p.Rect(width // 2 - panel_w // 2, height // 2 - panel_h // 2, panel_w, panel_h)
            field_x = panel.x + 36
            field_w = panel.w - 72

            time_field.rect = p.Rect(field_x, panel.y + 128, field_w, 46)
            difficulty_y = panel.y + 214
            gap = 14
            diff_w = (field_w - gap * 2) // 3
            beginner_btn.rect = p.Rect(field_x, difficulty_y, diff_w, 42)
            moderate_btn.rect = p.Rect(field_x + diff_w + gap, difficulty_y, diff_w, 42)
            hard_btn.rect = p.Rect(field_x + 2 * (diff_w + gap), difficulty_y, diff_w, 42)

            setup_field.rect = p.Rect(field_x, panel.y + 318, field_w, 46)
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

                if mode == "menu":
                    if event.type == p.MOUSEBUTTONDOWN:
                        if play_ai_btn.contains(event.pos):
                            self.playerOne = True
                            self.playerTwo = False
                            mode_label = "Mode: Human (White) vs AI (Black)"
                            ai_mode = True
                            mode = "config"
                        elif play_pvp_btn.contains(event.pos):
                            self.playerOne = True
                            self.playerTwo = True
                            mode_label = "Mode: Human vs Human"
                            ai_mode = False
                            mode = "config"
                        elif exit_btn.contains(event.pos):
                            self.exit_requested = True
                            return
                else:
                    time_field.handle_event(event)
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
                                popup = Popup("Please enter a valid game time in whole minutes.")
                                continue
                            self.time = parsed
                            setup_text = setup_field.text.strip()
                            if setup_text:
                                self.setup = setup_text if setup_text.startswith("Setup ") else "Setup " + setup_text
                            self.Online = False
                            return

            _draw_menu_background(screen)
            width, height = screen.get_size()

            if mode == "menu":
                title = title_font.render("Two-Flags", True, (240, 244, 249))
                subtitle = body_font.render("Choose a game mode", True, (215, 224, 234))
                screen.blit(title, (width // 2 - title.get_width() // 2, max(82, height // 2 - 210)))
                screen.blit(subtitle, (width // 2 - subtitle.get_width() // 2, max(146, height // 2 - 148)))

                play_ai_btn.draw(screen, button_font, hover=play_ai_btn.contains(mouse_pos))
                play_pvp_btn.draw(screen, button_font, hover=play_pvp_btn.contains(mouse_pos))
                exit_btn.draw(screen, button_font, hover=exit_btn.contains(mouse_pos))
            else:
                p.draw.rect(screen, (245, 247, 250), panel, border_radius=16)
                p.draw.rect(screen, (44, 57, 74), panel, width=2, border_radius=16)

                hdr = p.font.SysFont("arial", 46, True).render("Game Setup", True, (30, 42, 56))
                mode_txt = small_font.render(mode_label, True, (87, 101, 116))
                t_label = small_font.render("Game Time (minutes)", True, (30, 42, 56))
                d_label = small_font.render("AI Difficulty", True, (30, 42, 56))
                s_label = small_font.render("Custom Setup", True, (30, 42, 56))

                screen.blit(hdr, (panel.x + 36, panel.y + 24))
                screen.blit(mode_txt, (panel.x + 36, panel.y + 78))
                screen.blit(t_label, (panel.x + 36, panel.y + 104))
                screen.blit(d_label, (panel.x + 36, panel.y + 188))
                screen.blit(s_label, (panel.x + 36, panel.y + 292))

                time_field.draw(screen, body_font)
                setup_field.draw(screen, body_font)
                if ai_mode:
                    beginner_btn.bg = (58, 81, 107) if self.difficulty == "Beginner" else (91, 110, 130)
                    moderate_btn.bg = (51, 100, 77) if self.difficulty == "Moderate" else (66, 114, 90)
                    hard_btn.bg = (113, 74, 60) if self.difficulty == "Hard" else (126, 87, 72)
                    beginner_btn.draw(screen, small_font, hover=beginner_btn.contains(mouse_pos))
                    moderate_btn.draw(screen, small_font, hover=moderate_btn.contains(mouse_pos))
                    hard_btn.draw(screen, small_font, hover=hard_btn.contains(mouse_pos))
                else:
                    ai_text = small_font.render("Difficulty is only used in Play vs AI mode.", True, (102, 113, 125))
                    screen.blit(ai_text, (panel.x + 36, panel.y + 224))

                help_lines = _wrap_text("Format: Wb4 Wa3 Bg7 ... (leave as default if unsure)", small_font, field_w)
                y = panel.y + 374
                for line in help_lines[:2]:
                    help_txt = small_font.render(line, True, (102, 113, 125))
                    screen.blit(help_txt, (panel.x + 36, y))
                    y += help_txt.get_height() + 2

                back_btn.draw(screen, button_font, hover=back_btn.contains(mouse_pos))
                start_btn.draw(screen, button_font, hover=start_btn.contains(mouse_pos))

            if popup is not None:
                popup.draw(screen, body_font, small_font, button_font)

            p.display.flip()
            clock.tick(60)


class GameUI:
    """UI renderer for board, side panel, restart controls and game-over overlays."""

    def __init__(self, board_width, board_height, move_log_width, move_log_height, sq_size, dimension, images):
        self.board_width = board_width
        self.board_height = board_height
        self.move_log_width = move_log_width
        self.move_log_height = move_log_height
        self.sq_size = sq_size
        self.dimension = dimension
        self.images = images
        self.side_width = 128
        self.total_width = self.board_width + self.side_width + self.move_log_width
        self.total_height = self.board_height

        self.colors = [(245, 248, 252), (192, 204, 217)]
        self.selected_color = (73, 131, 198, 120)
        self.moves_color = (255, 212, 95, 120)

        self.restart_button = Button((self.board_width + 14, 20, self.side_width - 28, 42), "Restart", bg=(67, 104, 145))
        self.menu_button = Button((self.board_width + 14, 72, self.side_width - 28, 42), "Menu", bg=(73, 103, 139))
        self.over_restart_button = Button((self.board_width // 2 - 200, self.board_height // 2 + 50, 180, 50),
                                          "Restart", bg=(68, 112, 88))
        self.over_menu_button = Button((self.board_width // 2 + 20, self.board_height // 2 + 50, 180, 50),
                                       "Main Menu", bg=(73, 103, 139))

    def draw_game_state(self, screen, move_log, gs, valid_moves, sq_selected, move_log_font):
        self._draw_board(screen)
        self._highlight_squares(screen, gs, valid_moves, sq_selected)
        self._draw_pieces(screen, gs)
        self._draw_move_log(screen, move_log, move_log_font)

    def draw_side_panel(self, screen, timer_font, white_timer, black_timer):
        panel = p.Rect(self.board_width, 0, self.side_width, self.board_height)
        p.draw.rect(screen, (229, 235, 242), panel)
        p.draw.line(screen, (154, 166, 179), (self.board_width, 0), (self.board_width, self.board_height), 2)
        p.draw.line(screen, (154, 166, 179), (self.board_width + self.side_width, 0),
                    (self.board_width + self.side_width, self.board_height), 2)

        self.restart_button.draw(screen, p.font.SysFont("arial", 18, True),
                                 hover=self.restart_button.contains(p.mouse.get_pos()))
        self.menu_button.draw(screen, p.font.SysFont("arial", 18, True),
                              hover=self.menu_button.contains(p.mouse.get_pos()))

        # Place timers away from the top buttons so they stay readable.
        black = timer_font.render(black_timer, True, (32, 41, 52))
        white = timer_font.render(white_timer, True, (32, 41, 52))
        black_y = 145
        white_y = self.board_height - 125
        screen.blit(black, (self.board_width + (self.side_width - black.get_width()) // 2, black_y))
        screen.blit(white, (self.board_width + (self.side_width - white.get_width()) // 2, white_y))

    def draw_game_over(self, screen, message):
        overlay = p.Surface((self.board_width, self.board_height), p.SRCALPHA)
        overlay.fill((16, 23, 31, 180))
        screen.blit(overlay, (0, 0))

        card = p.Rect(self.board_width // 2 - 250, self.board_height // 2 - 120, 500, 250)
        p.draw.rect(screen, (250, 251, 253), card, border_radius=16)
        p.draw.rect(screen, (38, 51, 66), card, width=2, border_radius=16)

        title_font = p.font.SysFont("arial", 32, True)
        body_font = p.font.SysFont("arial", 20)
        button_font = p.font.SysFont("arial", 21, True)

        title = title_font.render("Game Over", True, (33, 43, 54))
        screen.blit(title, (card.centerx - title.get_width() // 2, card.y + 24))

        wrapped = _wrap_text(message, body_font, card.width - 40)
        y = card.y + 84
        for line in wrapped[:3]:
            msg = body_font.render(line, True, (68, 79, 92))
            screen.blit(msg, (card.centerx - msg.get_width() // 2, y))
            y += msg.get_height() + 4

        self.over_restart_button.draw(screen, button_font, hover=self.over_restart_button.contains(p.mouse.get_pos()))
        self.over_menu_button.draw(screen, button_font, hover=self.over_menu_button.contains(p.mouse.get_pos()))

    def _draw_board(self, screen):
        for r in range(self.dimension):
            for c in range(self.dimension):
                color = self.colors[(r + c) % 2]
                p.draw.rect(screen, color, p.Rect(c * self.sq_size, r * self.sq_size, self.sq_size, self.sq_size))

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
