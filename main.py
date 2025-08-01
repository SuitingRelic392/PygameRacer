import pygame
import sys
import io
import math

pygame.init()

# Constants
WIDTH, HEIGHT = 1000, 700
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (30, 30, 30)
DARK_GRAY = (20, 20, 20)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
BLUE = (0, 100, 255)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)
LIGHT_GRAY = (128, 128, 128)
CYAN = (0, 255, 255)
FONT = pygame.font.SysFont("calibri", 20)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Python IDE Racer")
clock = pygame.time.Clock()

# Modes
mode = "ide"  # 'ide', 'race'

# Original premade code (to revert to)
original_code_lines = [
    "# AI Car Controller - No infinite loops needed!",
    "# This function runs once per frame automatically",
    "",
    "def control_car():",
    "    front = get_Forwardsensordata()",
    "    left = get_Leftsensordata()",
    "    right = get_Rightsensordata()",
    "    ",
    "    # If obstacle ahead, turn away from it",
    "    if front < 40:",
    "        if left > right:",
    "            turn_left(50)",
    "        else:",
    "            turn_right(50)",
    "    else:",
    "        # Drive forward and follow the track",
    "        drive_forward()",
    "        ",
    "        # Keep centered on track",
    "        if left < 50:",
    "            turn_right(15)",
    "        elif right < 50:",
    "            turn_left(15)",
    "",
    "# Call the function",
    "control_car()"
]

# Editor state
code_lines = original_code_lines.copy()
current_line = 0
cursor_pos = 0
scroll_offset = 0
output_text = ""

# Backspace handling
backspace_held = False
backspace_pressed = False
backspace_timer = 0
backspace_repeat_delay = 500  # ms
backspace_repeat_rate = 50    # ms

# Car state
car_x, car_y = WIDTH // 2, HEIGHT - 150
car_angle = 0  # Start facing right
car_speed = 0

# Run-time injected functions
sensor_data = {"front": 0, "left": 0, "right": 0}

# User code execution globals
user_globals = {}
user_code_compiled = None

def reset_car():
    global car_x, car_y, car_angle, car_speed
    car_x = WIDTH // 2
    car_y = HEIGHT - 150
    car_angle = 0
    car_speed = 0

def get_Forwardsensordata():
    return sensor_data["front"]

def get_Leftsensordata():
    return sensor_data["left"]

def get_Rightsensordata():
    return sensor_data["right"]

def drive_forward():
    global car_x, car_y
    rad = math.radians(car_angle)
    car_x += math.cos(rad) * 3
    car_y += math.sin(rad) * 3

def turn_left(percent):
    global car_angle
    car_angle -= percent * 0.8

def turn_right(percent):
    global car_angle
    car_angle += percent * 0.8

def is_on_track(x, y):
    center_x, center_y = WIDTH // 2, HEIGHT // 2
    outer_a, outer_b = 350, 250
    inner_a, inner_b = 200, 150
    outer_dist = ((x - center_x) ** 2) / (outer_a ** 2) + ((y - center_y) ** 2) / (outer_b ** 2)
    inner_dist = ((x - center_x) ** 2) / (inner_a ** 2) + ((y - center_y) ** 2) / (inner_b ** 2)
    return outer_dist <= 1.0 and inner_dist >= 1.0

def update_sensors():
    global sensor_data
    for angle_offset, key in [(0, "front"), (-90, "left"), (90, "right")]:
        dist = 0
        for dist in range(1, 150):
            check_x = int(car_x + dist * math.cos(math.radians(car_angle + angle_offset)))
            check_y = int(car_y + dist * math.sin(math.radians(car_angle + angle_offset)))
            if 0 <= check_x < WIDTH and 0 <= check_y < HEIGHT:
                if not is_on_track(check_x, check_y):
                    break
            else:
                break
        sensor_data[key] = dist

def draw_editor():
    global scroll_offset
    screen.fill((25, 25, 30))
    editor_rect = pygame.Rect(50, 50, 900, 300)
    pygame.draw.rect(screen, (35, 35, 40), editor_rect)
    pygame.draw.rect(screen, CYAN, editor_rect, 2)
    pygame.draw.rect(screen, (20, 20, 25), (50, 50, 40, 300))
    pygame.draw.line(screen, LIGHT_GRAY, (90, 50), (90, 350), 1)
    lines_per_screen = 12
    
    # Ensure scroll_offset valid and adjust for current line visibility
    if current_line < scroll_offset:
        scroll_offset = current_line
    elif current_line >= scroll_offset + lines_per_screen:
        scroll_offset = current_line - lines_per_screen + 1

    scroll_offset = max(0, min(scroll_offset, max(0, len(code_lines) - lines_per_screen)))
    
    start_line = scroll_offset
    end_line = min(len(code_lines), start_line + lines_per_screen)
    
    # Line numbers
    for i in range(start_line, end_line):
        display_line = i - start_line
        line_num = FONT.render(str(i + 1), True, LIGHT_GRAY)
        screen.blit(line_num, (55, 60 + display_line * 22))
    
    # Code lines with simple syntax highlight
    for i in range(start_line, end_line):
        display_line = i - start_line
        line = code_lines[i]
        y_pos = 60 + display_line * 22
        
        if i == current_line:
            pygame.draw.rect(screen, (50, 50, 60), (95, y_pos - 2, 850, 22))
        
        if line.strip().startswith('#'):
            color = (120, 120, 120)
        elif any(keyword in line for keyword in ['if', 'else', 'elif', 'while', 'for', 'def']):
            color = ORANGE
        elif any(func in line for func in ['drive_forward', 'turn_left', 'turn_right']):
            color = (100, 255, 100)
        elif any(func in line for func in ['get_Forwardsensordata', 'get_Leftsensordata', 'get_Rightsensordata']):
            color = CYAN
        else:
            color = WHITE
            
        rendered = FONT.render(line, True, color)
        screen.blit(rendered, (100, y_pos))
    
    # Cursor blinking
    if start_line <= current_line < end_line and pygame.time.get_ticks() // 400 % 2 == 0:
        display_line = current_line - start_line
        cursor_x = FONT.size(code_lines[current_line][:cursor_pos])[0]
        cursor_y = display_line * 22
        pygame.draw.line(screen, CYAN, (100 + cursor_x, 60 + cursor_y), (100 + cursor_x, 60 + cursor_y + 18), 2)

    # Scroll bar
    if len(code_lines) > lines_per_screen:
        scroll_bar_height = max(10, int((lines_per_screen / len(code_lines)) * 290))
        scroll_bar_pos = int((scroll_offset / (len(code_lines) - lines_per_screen)) * (290 - scroll_bar_height)) if len(code_lines) > lines_per_screen else 0
        pygame.draw.rect(screen, LIGHT_GRAY, (940, 55 + scroll_bar_pos, 5, scroll_bar_height))
    
    # Console output
    console_rect = pygame.Rect(50, 370, 900, 200)
    pygame.draw.rect(screen, (15, 15, 20), console_rect)
    pygame.draw.rect(screen, GREEN, console_rect, 2)
    pygame.draw.rect(screen, (0, 50, 0), (50, 370, 900, 25))
    header_text = FONT.render(">>> CONSOLE OUTPUT", True, GREEN)
    screen.blit(header_text, (60, 375))
    
    output_lines = output_text.split('\n')
    for i, line in enumerate(output_lines[:8]):
        rendered = FONT.render(line, True, GREEN)
        screen.blit(rendered, (60, 400 + i * 20))
    
    # Buttons
    clear_button_rect = pygame.Rect(650, 580, 120, 50)
    pygame.draw.rect(screen, (150, 0, 0), clear_button_rect)
    pygame.draw.rect(screen, RED, clear_button_rect, 3)
    clear_text = pygame.font.SysFont("consolas", 24, bold=True).render("Clear Code", True, WHITE)
    clear_text_rect = clear_text.get_rect(center=clear_button_rect.center)
    screen.blit(clear_text, clear_text_rect)

    revert_button_rect = pygame.Rect(490, 580, 140, 50)
    pygame.draw.rect(screen, (0, 0, 150), revert_button_rect)
    pygame.draw.rect(screen, BLUE, revert_button_rect, 3)
    revert_text = pygame.font.SysFont("consolas", 22, bold=True).render("Revert Code", True, WHITE)
    revert_text_rect = revert_text.get_rect(center=revert_button_rect.center)
    screen.blit(revert_text, revert_text_rect)

    run_button_rect = pygame.Rect(820, 580, 120, 50)
    pygame.draw.rect(screen, (0, 150, 50), run_button_rect)
    pygame.draw.rect(screen, GREEN, run_button_rect, 3)
    btn_text = pygame.font.SysFont("consolas", 24, bold=True).render("▶ RUN", True, WHITE)
    text_rect = btn_text.get_rect(center=run_button_rect.center)
    screen.blit(btn_text, text_rect)

def draw_track():
    screen.fill(DARK_GRAY)
    center_x, center_y = WIDTH // 2, HEIGHT // 2
    
    pygame.draw.ellipse(screen, WHITE, (center_x - 350, center_y - 250, 700, 500), 4)
    pygame.draw.ellipse(screen, WHITE, (center_x - 200, center_y - 150, 400, 300), 4)

    start_y = center_y + 200
    pygame.draw.line(screen, YELLOW, (center_x - 30, start_y), (center_x + 30, start_y), 6)

    car_points = [
        (12, 0),
        (-10, -6),
        (-10, 6)
    ]
    rotated_points = []
    for px, py in car_points:
        cos_a = math.cos(math.radians(car_angle))
        sin_a = math.sin(math.radians(car_angle))
        rx = px * cos_a - py * sin_a
        ry = px * sin_a + py * cos_a
        rotated_points.append((car_x + rx, car_y + ry))
    pygame.draw.polygon(screen, RED, rotated_points)
    pygame.draw.polygon(screen, WHITE, rotated_points, 2)

    sensor_colors = [YELLOW, BLUE, GREEN]
    sensor_keys = ["front", "left", "right"]
    sensor_angles = [0, -90, 90]

    for i, (angle_offset, key) in enumerate(zip(sensor_angles, sensor_keys)):
        end_x = car_x + sensor_data[key] * math.cos(math.radians(car_angle + angle_offset))
        end_y = car_y + sensor_data[key] * math.sin(math.radians(car_angle + angle_offset))
        pygame.draw.line(screen, sensor_colors[i], (car_x, car_y), (end_x, end_y), 2)

    back_rect = pygame.Rect(10, 10, 80, 30)
    pygame.draw.rect(screen, (100, 100, 100), back_rect)
    pygame.draw.rect(screen, WHITE, back_rect, 2)
    back_text = FONT.render("Back", True, WHITE)
    screen.blit(back_text, (20, 15))
    
    info_y = 50
    for i, key in enumerate(sensor_keys):
        text = f"{key}: {sensor_data[key]:.0f}"
        rendered = FONT.render(text, True, sensor_colors[i])
        screen.blit(rendered, (WIDTH - 150, info_y))
        info_y += 25

def get_clicked_line_and_col(mx, my):
    global scroll_offset
    if 50 <= mx <= 950 and 50 <= my <= 350:
        display_line = (my - 60) // 22
        actual_line = display_line + scroll_offset
        if 0 <= actual_line < len(code_lines):
            text_x = 100
            for col in range(len(code_lines[actual_line]) + 1):
                part = code_lines[actual_line][:col]
                px = text_x + FONT.size(part)[0]
                if px > mx:
                    return actual_line, col - 1 if col > 0 else 0
            return actual_line, len(code_lines[actual_line])
    return None, None

def run_code(code):
    global output_text, user_globals, user_code_compiled
    try:
        old_stdout = sys.stdout
        redirected_output = sys.stdout = io.StringIO()
        exec_globals = {
            "drive_forward": drive_forward,
            "get_Forwardsensordata": get_Forwardsensordata,
            "get_Leftsensordata": get_Leftsensordata,
            "get_Rightsensordata": get_Rightsensordata,
            "turn_left": turn_left,
            "turn_right": turn_right,
            "__builtins__": __builtins__,
            "print": print,
            "range": range,
            "len": len,
            "abs": abs,
            "min": min,
            "max": max,
        }
        user_code_compiled = compile(code, "<user_code>", "exec")
        user_globals = exec_globals
        sys.stdout = old_stdout
        output_text = "Code compiled successfully. Car is ready to race!"
    except Exception as e:
        sys.stdout = old_stdout
        output_text = f"Error: {str(e)}"
        user_globals = {}
        user_code_compiled = None

def execute_user_code():
    global user_code_compiled, user_globals
    if user_code_compiled and user_globals:
        try:
            exec(user_code_compiled, user_globals)
        except Exception:
            pass

def handle_backspace():
    global current_line, cursor_pos, code_lines
    line = code_lines[current_line]
    if cursor_pos > 0:
        code_lines[current_line] = line[:cursor_pos - 1] + line[cursor_pos:]
        cursor_pos -= 1
    elif current_line > 0:
        prev_line = code_lines[current_line - 1]
        cursor_pos = len(prev_line)
        code_lines[current_line - 1] += line
        code_lines.pop(current_line)
        current_line -= 1

reset_car()

running = True
while running:
    current_time = pygame.time.get_ticks()

    if mode == "ide":
        keys = pygame.key.get_pressed()
        if keys[pygame.K_BACKSPACE]:
            if not backspace_held:
                backspace_held = True
                backspace_pressed = True
                backspace_timer = current_time + backspace_repeat_delay
            elif current_time >= backspace_timer:
                backspace_timer = current_time + backspace_repeat_rate
                handle_backspace()
        else:
            backspace_held = False
            backspace_pressed = False
        
        draw_editor()
        
    elif mode == "race":
        update_sensors()
        execute_user_code()
        draw_track()

    pygame.display.flip()
    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if mode == "ide":
            if event.type == pygame.KEYDOWN:
                line = code_lines[current_line]
                mods = pygame.key.get_mods()

                if event.key == pygame.K_RETURN and (mods & pygame.KMOD_SHIFT):
                    code = "\n".join(code_lines)
                    reset_car()
                    run_code(code)
                    mode = "race"

                elif event.key == pygame.K_BACKSPACE:
                    if not backspace_pressed:
                        handle_backspace()
                        backspace_pressed = True

                elif event.key == pygame.K_TAB:
                    code_lines[current_line] = line[:cursor_pos] + "    " + line[cursor_pos:]
                    cursor_pos += 4

                elif event.key == pygame.K_LEFT:
                    if cursor_pos > 0:
                        cursor_pos -= 1
                    elif current_line > 0:
                        current_line -= 1
                        cursor_pos = len(code_lines[current_line])

                elif event.key == pygame.K_RIGHT:
                    if cursor_pos < len(line):
                        cursor_pos += 1
                    elif current_line < len(code_lines) - 1:
                        current_line += 1
                        cursor_pos = 0

                elif event.key == pygame.K_UP:
                    if current_line > 0:
                        current_line -= 1
                        cursor_pos = min(cursor_pos, len(code_lines[current_line]))

                elif event.key == pygame.K_DOWN:
                    if current_line + 1 < len(code_lines):
                        current_line += 1
                        cursor_pos = min(cursor_pos, len(code_lines[current_line]))

                elif event.key == pygame.K_PAGEUP:
                    current_line = max(0, current_line - 10)
                    cursor_pos = min(cursor_pos, len(code_lines[current_line]))

                elif event.key == pygame.K_PAGEDOWN:
                    current_line = min(len(code_lines) - 1, current_line + 10)
                    cursor_pos = min(cursor_pos, len(code_lines[current_line]))

                elif event.key == pygame.K_HOME:
                    cursor_pos = 0

                elif event.key == pygame.K_END:
                    cursor_pos = len(line)

                elif event.key == pygame.K_ESCAPE:
                    code = "\n".join(code_lines)
                    reset_car()
                    run_code(code)
                    mode = "race"

                elif event.key == pygame.K_v and (mods & pygame.KMOD_CTRL):
                    try:
                        clipboard_text = pygame.scrap.get(pygame.SCRAP_TEXT)
                        if clipboard_text:
                            insert_text = clipboard_text.decode("utf-8")
                            line = code_lines[current_line]
                            code_lines[current_line] = line[:cursor_pos] + insert_text + line[cursor_pos:]
                            cursor_pos += len(insert_text)
                    except Exception:
                        pass

                elif event.unicode and event.unicode.isprintable():
                    line = code_lines[current_line]
                    code_lines[current_line] = line[:cursor_pos] + event.unicode + line[cursor_pos:]
                    cursor_pos += 1

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_BACKSPACE:
                    backspace_pressed = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                # Click in editor area?
                clicked_line, clicked_col = get_clicked_line_and_col(mx, my)
                if clicked_line is not None:
                    current_line = clicked_line
                    cursor_pos = clicked_col
                
                # Buttons click detection
                if 490 <= mx <= 630 and 580 <= my <= 630:
                    # Revert code
                    code_lines = original_code_lines.copy()
                    current_line = 0
                    cursor_pos = 0
                    output_text = "Code reverted to original."
                elif 650 <= mx <= 770 and 580 <= my <= 630:
                    # Clear code
                    code_lines = [""]
                    current_line = 0
                    cursor_pos = 0
                    output_text = "Code cleared."
                elif 820 <= mx <= 940 and 580 <= my <= 630:
                    # Run button
                    code = "\n".join(code_lines)
                    reset_car()
                    run_code(code)
                    mode = "race"

            # Mouse wheel scrolling
            if event.type == pygame.MOUSEWHEEL:
                scroll_offset -= event.y * 3
                max_scroll = max(0, len(code_lines) - 12)
                scroll_offset = max(0, min(scroll_offset, max_scroll))

        elif mode == "race":
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                back_rect = pygame.Rect(10, 10, 80, 30)
                if back_rect.collidepoint(mx, my):
                    mode = "ide"
            
            keys = pygame.key.get_pressed()
            if keys[pygame.K_ESCAPE]:
                mode = "ide"

pygame.quit()
sys.exit()
