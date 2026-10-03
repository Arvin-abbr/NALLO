import pygame
import random
import math
import sys
from pygame.locals import *

# 初始化pygame
pygame.init()
pygame.font.init()

# =========修复：规避 pygame2.6.1 windows sysfont bug，禁止 SysFont(None,size)=========
font = None
try:
    # 优先尝试直接打开simhei.ttf，Windows一般自带这个文件
    font = pygame.font.Font("simhei.ttf", 24)
except Exception:
    pass

# 如果上面失败，尝试系统命名字体，注意：绝不使用 SysFont(None,24)
if font is None:
    font_candidates = ["SimHei", "Microsoft YaHei", "WenQuanYi Micro Hei", "Heiti TC"]
    for fname in font_candidates:
        try:
            font = pygame.font.SysFont(fname, 24)
            # 测试渲染中文，看是否方框
            test_surf = font.render("测", True, (255, 255, 255))
            if test_surf.get_width() > 5:
                break
        except Exception:
            font = None
            continue

# 终极兜底：如果全部系统字体都挂掉，禁用中文，使用英文文字
CHINESE_OK = True
if font is None:
    CHINESE_OK = False
    # 这里不能用SysFont(None,24)! 我们直接用 pygame.font.Font() 内置极简字体
    # 使用pygame内置的默认字体文件
    font = pygame.font.Font(pygame.font.get_default_font(), 24)


# 游戏常量
WIDTH, HEIGHT = 800, 600
GRID_SIZE = 20
GRID_WIDTH = WIDTH // GRID_SIZE
GRID_HEIGHT = HEIGHT // GRID_SIZE

# 颜色定义 - 彩虹色系列
RAINBOW_COLORS = [
    (255, 94, 94),    # 红色渐变
    (255, 125, 94),   # 橙红色
    (255, 179, 71),   # 橙色
    (255, 242, 117),  # 黄色
    (147, 255, 150),  # 绿色
    (66, 215, 245),   # 蓝色
    (125, 95, 255),   # 靛蓝色
    (199, 116, 232)   # 紫色
]

# 方向常量
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

# 设置游戏窗口
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Snake Game")
clock = pygame.time.Clock()
FPS_BASE = 60  # 基础帧率上限

class Snake:
    def __init__(self):
        self.reset()

    def reset(self):
        # 初始位置和方向
        self.positions = [(GRID_WIDTH // 2, GRID_HEIGHT // 2)]
        self.direction = RIGHT
        self.next_direction = RIGHT
        self.length = 3

        # 初始化蛇身
        for i in range(1, self.length):
            self.positions.append((self.positions[0][0] - i, self.positions[0][1]))

        # 颜色和速度属性
        self.color_index = 0
        self.speed = 10

    def get_head_position(self):
        return self.positions[0]

    def turn(self, new_direction):
        # 防止180度转向
        if (new_direction[0] * -1, new_direction[1] * -1) == self.direction:
            return
        self.next_direction = new_direction

    def move(self):
        self.direction = self.next_direction
        head = self.get_head_position()
        x, y = self.direction
        new_head = ((head[0] + x) % GRID_WIDTH, (head[1] + y) % GRID_HEIGHT)

        # 检查是否撞到自己
        if new_head in self.positions[1:]:
            return False

        self.positions.insert(0, new_head)

        # 如果长度不够，移除尾部
        while len(self.positions) > self.length:
            self.positions.pop()

        return True

    def increase_length(self):
        self.length += 1
        # 增加速度，但有上限
        self.speed = min(20, self.speed + 0.5)
        # 切换到下一个彩虹色
        self.color_index = (self.color_index + 1) % len(RAINBOW_COLORS)

    def draw(self, surface):
        # 绘制蛇身
        for i, p in enumerate(self.positions):
            # 计算颜色渐变（从头部到尾部逐渐变化）
            color_index = (self.color_index - i // 3) % len(RAINBOW_COLORS)
            color = RAINBOW_COLORS[color_index]

            rect = pygame.Rect((p[0] * GRID_SIZE, p[1] * GRID_SIZE), (GRID_SIZE - 1, GRID_SIZE - 1))
            pygame.draw.rect(surface, color, rect, border_radius=5)

            if i == 0:
                self.draw_eyes(surface, p)

    def draw_eyes(self, surface, position):
        x, y = position
        eye_size = 3
        if self.direction == RIGHT:
            eye_pos1 = (x * GRID_SIZE + GRID_SIZE - eye_size * 2, y * GRID_SIZE + eye_size)
            eye_pos2 = (x * GRID_SIZE + GRID_SIZE - eye_size * 2, y * GRID_SIZE + GRID_SIZE - eye_size * 2)
        elif self.direction == LEFT:
            eye_pos1 = (x * GRID_SIZE + eye_size, y * GRID_SIZE + eye_size)
            eye_pos2 = (x * GRID_SIZE + eye_size, y * GRID_SIZE + GRID_SIZE - eye_size * 2)
        elif self.direction == UP:
            eye_pos1 = (x * GRID_SIZE + eye_size, y * GRID_SIZE + eye_size)
            eye_pos2 = (x * GRID_SIZE + GRID_SIZE - eye_size * 2, y * GRID_SIZE + eye_size)
        else:  # DOWN
            eye_pos1 = (x * GRID_SIZE + eye_size, y * GRID_SIZE + GRID_SIZE - eye_size * 2)
            eye_pos2 = (x * GRID_SIZE + GRID_SIZE - eye_size * 2, y * GRID_SIZE + GRID_SIZE - eye_size * 2)

        pygame.draw.circle(surface, (255, 255, 255), eye_pos1, eye_size)
        pygame.draw.circle(surface, (255, 255, 255), eye_pos2, eye_size)
        pupil_size = 1
        pygame.draw.circle(surface, (0, 0, 0), eye_pos1, pupil_size)
        pygame.draw.circle(surface, (0, 0, 0), eye_pos2, pupil_size)


class Food:
    def __init__(self, snake_positions):
        self.position = (0, 0)
        self.rotation = 0.0
        self.randomize_position(snake_positions)

    def randomize_position(self, snake_positions):
        while True:
            self.position = (random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))
            if self.position not in snake_positions:
                break

    def draw(self, surface):
        self.rotation += 0.12
        x, y = self.position
        cx = GRID_SIZE // 2
        cy = GRID_SIZE // 2
        radius = GRID_SIZE // 2 - 2
        star_points = []
        for i in range(10):
            angle = self.rotation + i * math.pi / 5
            r = radius if i % 2 == 0 else radius // 2
            sx = cx + r * math.cos(angle)
            sy = cy + r * math.sin(angle)
            star_points.append((sx, sy))

        temp_surface = pygame.Surface((GRID_SIZE, GRID_SIZE), pygame.SRCALPHA)
        pygame.draw.polygon(temp_surface, (255, 215, 0), star_points)
        surface.blit(temp_surface, (x * GRID_SIZE, y * GRID_SIZE))


def draw_grid(surface):
    for y in range(0, HEIGHT, GRID_SIZE):
        for x in range(0, WIDTH, GRID_SIZE):
            rect = pygame.Rect(x, y, GRID_SIZE, GRID_SIZE)
            pygame.draw.rect(surface, (40, 40, 40), rect, 1)


def show_game_over(surface, score):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    surface.blit(overlay, (0, 0))

    if CHINESE_OK:
        t_gameover = "游戏结束!"
        t_score = f"最终分数: {score}"
        t_restart = "按空格键重新开始"
    else:
        t_gameover = "GAME OVER!"
        t_score = f"Score: {score}"
        t_restart = "Press SPACE to restart"

    game_over_text = font.render(t_gameover, True, (255, 0, 0))
    score_text = font.render(t_score, True, (255, 255, 255))
    restart_text = font.render(t_restart, True, (255, 255, 255))

    game_over_rect = game_over_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
    score_rect = score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    restart_rect = restart_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))

    surface.blit(game_over_text, game_over_rect)
    surface.blit(score_text, score_rect)
    surface.blit(restart_text, restart_rect)


def main():
    snake = Snake()
    food = Food(snake.positions)
    score = 0
    game_over = False

    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == KEYDOWN:
                if game_over:
                    if event.key == K_SPACE:
                        snake.reset()
                        food = Food(snake.positions)
                        score = 0
                        game_over = False
                    continue
                if event.key == K_UP:
                    snake.turn(UP)
                elif event.key == K_DOWN:
                    snake.turn(DOWN)
                elif event.key == K_LEFT:
                    snake.turn(LEFT)
                elif event.key == K_RIGHT:
                    snake.turn(RIGHT)
                elif event.key == K_ESCAPE:
                    pygame.quit()
                    sys.exit()

        if not game_over:
            if not snake.move():
                game_over = True
            if snake.get_head_position() == food.position:
                score += 10
                snake.increase_length()
                food = Food(snake.positions)

        screen.fill((10, 10, 30))
        draw_grid(screen)
        snake.draw(screen)
        food.draw(screen)

        score_label = "分数:" if CHINESE_OK else "Score:"
        score_text = font.render(f"{score_label} {score}", True, (255, 255, 255))
        screen.blit(score_text, (10, 10))

        if game_over:
            show_game_over(screen, score)

        pygame.display.update()
        if game_over:
            clock.tick(FPS_BASE)
        else:
            clock.tick(snake.speed)


if __name__ == "__main__":
    main()
