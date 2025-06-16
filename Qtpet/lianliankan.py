import pygame
import random
import sys
import math
# 初始化 Pygame
pygame.init()

font_path = "cfg\zxf.ttf"  # 比如黑体
font_size = 18
font = pygame.font.Font(font_path, font_size)  # None 表示使用默认字体，但不支持中文

# 配置参数
SCREEN_WIDTH, SCREEN_HEIGHT = 640, 720  # 增加高度容纳状态栏
STATUS_BAR_HEIGHT = 80
GRID_SIZE = 10
ICON_SIZE = 64
DIFFICULTY = 9
TOTAL_TIME = 300  # 倒计时总时间（秒）

# 颜色定义
WHITE = (255, 255, 255)
BG_COLOR = (240, 240, 240)
GRID_BORDER = (200, 200, 200)
SELECT_COLOR = (75, 192, 192)
HIGHLIGHT_COLOR = (255, 215, 0)
STATUS_BG = (220, 220, 220)
TEXT_COLOR = (30, 30, 30)
WIN_COLOR = (255, 223, 0)
LOSE_COLOR = (255, 99, 71)


# 创建窗口
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("连连看 - doro版")

# 加载资源
def load_images():
    images = []
    for i in range(1, DIFFICULTY + 1):
        path = f"games/images/{str(i).zfill(2)}.png"
        try:
            img = pygame.image.load(path).convert_alpha()
            img = pygame.transform.scale(img, (ICON_SIZE, ICON_SIZE))
            images.append(img)
        except FileNotFoundError:
            print(f"未找到图片：{path}")
            sys.exit()
    return images


# 创建网格
def create_grid():
    icons = load_images()
    total_icons = GRID_SIZE * GRID_SIZE
    pairs_needed = total_icons // 2
    icon_pool = (icons * (pairs_needed // len(icons) + 1))[:pairs_needed]
    icon_pool *= 2
    random.shuffle(icon_pool)
    return [icon_pool[i*GRID_SIZE:(i+1)*GRID_SIZE] for i in range(GRID_SIZE)]

# 绘制网格
def draw_grid(grid, selected):
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            x = col * ICON_SIZE
            y = row * ICON_SIZE + STATUS_BAR_HEIGHT
            icon = grid[row][col]
            
            # 绘制背景方块
            pygame.draw.rect(screen, BG_COLOR, (x, y, ICON_SIZE, ICON_SIZE))
            
            # 绘制图标
            if icon is not None:
                screen.blit(icon, (x, y))
            
            # 绘制边框
            pygame.draw.rect(screen, GRID_BORDER, (x, y, ICON_SIZE, ICON_SIZE), 1)
            
            # 绘制选中效果
            if (row, col) in selected:
                color = SELECT_COLOR if len(selected) == 1 else HIGHLIGHT_COLOR
                pygame.draw.rect(screen, color, (x, y, ICON_SIZE, ICON_SIZE), 3)

# 绘制文本
def draw_text(surface, text, position, size=24, color=TEXT_COLOR):
    # font = pygame.font.SysFont(font_path, size)
    text_surface = font.render(text, True, color)
    surface.blit(text_surface, position)

def draw_connection(path):
    if not path:
        return
    points = [
        (col * ICON_SIZE + ICON_SIZE // 2, row * ICON_SIZE + STATUS_BAR_HEIGHT + ICON_SIZE // 2)
        for row, col in path
    ]
    if len(points) >= 2:
        pygame.draw.lines(screen, (255, 0, 0), False, points, 3)

# 检查连接线
def check_line(grid, pos1, pos2):
    r1, c1 = pos1
    r2, c2 = pos2
    points = []

    if r1 == r2:
        min_col, max_col = sorted([c1, c2])
        for col in range(min_col, max_col + 1):
            points.append((r1, col))
        if all(grid[r1][col] is None for col in range(min_col + 1, max_col)):
            return points
    elif c1 == c2:
        min_row, max_row = sorted([r1, r2])
        for row in range(min_row, max_row + 1):
            points.append((row, c1))
        if all(grid[row][c1] is None for row in range(min_row + 1, max_row)):
            return points
    return []

# 检查一个拐角
# def check_one_corner(grid, r1, c1, r2, c2):
#     for mid_row, mid_col in [(r1, c2), (r2, c1)]:
#         if 0 <= mid_row < GRID_SIZE and 0 <= mid_col < GRID_SIZE:
#             if grid[mid_row][mid_col] is None:
#                 line1 = check_line(grid, (r1, c1), (mid_row, mid_col))
#                 line2 = check_line(grid, (mid_row, mid_col), (r2, c2))
#                 if line1 and line2:
#                     return line1[:-1] + line2  # 合并路径，去重中间点
#     return []
def check_one_corner(grid, r1, c1, r2, c2):
    for mid_row, mid_col in [(r1, c2), (r2, c1)]:
        if 0 <= mid_row < GRID_SIZE and 0 <= mid_col < GRID_SIZE:
            if grid[mid_row][mid_col] is None:
                line1 = check_line(grid, (r1, c1), (mid_row, mid_col))
                line2 = check_line(grid, (mid_row, mid_col), (r2, c2))
                if line1 and line2:
                    # 确保 line1 以中间点结尾，line2 以中间点开头
                    if line1[-1] != (mid_row, mid_col):
                        line1 = list(reversed(line1))  # 反转 line1
                    if line2[0] != (mid_row, mid_col):
                        line2 = list(reversed(line2))  # 反转 line2
                    return line1 + line2[1:]  # 拼接路径
    return []

# 检查两个拐角
def check_two_corners(grid, r1, c1, r2, c2):
    # 遍历行，垂直方向寻找中间点
    for row in range(GRID_SIZE):
        mid_point = (row, c1)
        if grid[row][c1] is None:
            line1 = check_line(grid, (r1, c1), mid_point)
            if line1:
                # 确保 line1 以 mid_point 结尾
                if line1[-1] != mid_point:
                    line1 = list(reversed(line1))
                line2 = check_one_corner(grid, row, c1, r2, c2)
                if line2:
                    # 确保 line2 以 mid_point 开头
                    if line2[0] != mid_point:
                        line2 = list(reversed(line2))
                    # 拼接路径，去重中间点
                    return line1 + line2[1:]

    # 遍历列，水平方向寻找中间点
    for col in range(GRID_SIZE):
        mid_point = (r1, col)
        if grid[r1][col] is None:
            line1 = check_line(grid, (r1, c1), mid_point)
            if line1:
                # 确保 line1 以 mid_point 结尾
                if line1[-1] != mid_point:
                    line1 = list(reversed(line1))
                line2 = check_one_corner(grid, r1, col, r2, c2)
                if line2:
                    # 确保 line2 以 mid_point 开头
                    if line2[0] != mid_point:
                        line2 = list(reversed(line2))
                    # 拼接路径，去重中间点
                    return line1 + line2[1:]

    return []

# 主检测函数
def is_connected(grid, r1, c1, r2, c2):
    line = check_line(grid, (r1, c1), (r2, c2))
    if line:
        return line
    one_corner = check_one_corner(grid, r1, c1, r2, c2)
    if one_corner:
        return one_corner
    two_corners = check_two_corners(grid, r1, c1, r2, c2)
    if two_corners:
        return two_corners
    return []

# 胜利检测
def check_win(grid):
    return all(icon is None for row in grid for icon in row)

# 游戏状态绘制
def draw_game_state(game_over, win, elapsed_time):
    if game_over:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill(WHITE if win else TEXT_COLOR)
        overlay.set_alpha(200)
        screen.blit(overlay, (0, 0))
        
        color = WIN_COLOR if win else LOSE_COLOR
        text = "胜利！" if win else "游戏结束"
        draw_text(screen, text, (SCREEN_WIDTH//2 - 60, SCREEN_HEIGHT//2 - 30), 48, color)
        
        # 动画效果
        for i in range(5):
            angle = i * 72
            x = SCREEN_WIDTH//2 + int(math.cos(math.radians(angle)) * 100)
            y = SCREEN_HEIGHT//2 + int(math.sin(math.radians(angle)) * 100)
            pygame.draw.circle(screen, color, (x, y), 10)

# 主函数
def main():
    grid = create_grid()
    selected = []
    clock = pygame.time.Clock()
    
    # 状态栏元素
    reset_rect = pygame.Rect(SCREEN_WIDTH - 120, 20, 100, 40)
    status_rect = pygame.Rect(0, 0, SCREEN_WIDTH, STATUS_BAR_HEIGHT)
    
    # 倒计时
    start_ticks = pygame.time.get_ticks()
    game_over = False
    win = False
    
    current_path = []
    path_start_time = 0
    PATH_DURATION = 500  # 毫秒

    running = True
    while running:
        # 计算剩余时间
        seconds_passed = (pygame.time.get_ticks() - start_ticks) // 1000
        remaining_time = max(0, TOTAL_TIME - seconds_passed)
        if remaining_time == 0 and not game_over:
            game_over = True
            win = False
        
        # 胜利检测
        if check_win(grid) and not game_over:
            game_over = True
            win = True
        
        # 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and not game_over:
                x, y = pygame.mouse.get_pos()
                
                # 检查按钮点击
                if reset_rect.collidepoint((x, y)):
                    grid = create_grid()
                    selected.clear()
                    start_ticks = pygame.time.get_ticks()
                    game_over = False
                    win = False
                    continue
                
                # 处理网格点击
                col = x // ICON_SIZE
                row = (y - STATUS_BAR_HEIGHT) // ICON_SIZE
                if 0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE:
                    selected.append((row, col))
                    
                    # 处理配对检查
                    if len(selected) == 2:
                        (r1, c1), (r2, c2) = selected
                        if (r1 != r2 or c1 != c2) and grid[r1][c1] == grid[r2][c2] and  grid[r1][c1] != None and grid[r2][c2] != None:
                            current_path = is_connected(grid, r1, c1, r2, c2)
                            if current_path:
                                path_start_time = pygame.time.get_ticks()
                                grid[r1][c1] = None
                                grid[r2][c2] = None
                        selected.clear()
        
        # 绘制界面
        screen.fill(BG_COLOR)
        
        # 绘制状态栏背景
        pygame.draw.rect(screen, STATUS_BG, status_rect)
        
        # 绘制网格
        draw_grid(grid, selected)
        
        # 绘制连接线
        if current_path and pygame.time.get_ticks() - path_start_time < PATH_DURATION:
            draw_connection(current_path)
        else:
            current_path = []

        # 绘制UI元素
        draw_text(screen, f"剩余配对: {sum(1 for row in grid for icon in row if icon is not None)//2}", (10, 25))
        draw_text(screen, f"剩余时间: {remaining_time//60:02d}:{remaining_time%60:02d}", (200, 25))
        
        # 绘制重新开始按钮
        pygame.draw.rect(screen, WHITE, reset_rect)
        pygame.draw.rect(screen, GRID_BORDER, reset_rect, 2)
        draw_text(screen, "重新开始", (reset_rect.x + 10, reset_rect.y + 10), size=18)
        
        # 绘制游戏状态效果
        draw_game_state(game_over, win, seconds_passed)
        
        # 更新显示
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()