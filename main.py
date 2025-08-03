import random
from pygame import Rect
import math

# --- Constants ---
WIDTH = 640
HEIGHT = 480
TITLE = "Dungeon Escape"
TILE_SIZE = 32
ROWS = HEIGHT // TILE_SIZE
COLS = WIDTH // TILE_SIZE

MAX_LEVELS = 3

# Game states
STATE_MENU = "menu"
STATE_DIFFICULTY_SELECTION = "difficulty_selection"
STATE_GAME = "game"
STATE_COMBAT = "combat"
STATE_GAME_OVER = "game_over"
STATE_VICTORY = "victory"
STATE_INSTRUCTIONS = "instructions"

# Difficulties with multipliers
DIFFICULTY_LEVELS = {
    "Easy": 1.0,
    "Normal": 1.5,
    "Hard": 3.0,
    "Legendary": 9.0
}
healing_zones = [
    {"grid_x": 5, "grid_y": 2},
    {"grid_x": 8, "grid_y": 6}
]
legendary_chests = []

# --- Global variables ---
current_state = STATE_MENU
current_level = 1
selected_difficulty = "Normal"
difficulty_multiplier = DIFFICULTY_LEVELS[selected_difficulty]
sound_enabled = True
inventory_visible = False
enemy_in_combat = None
selected_item_index = None
visible_start_index = 0
start_visible = 0
item_selected = None
items_per_page = 5
sound_enabled = True
money = 0

music.set_volume(0.5)  # Volume entre 0.0 e 1.0
music.play("background_music")
# --- Buttons ---
buttons = {
    "start": Rect(WIDTH // 2 - 80, 150, 160, 40),
    "sound": Rect(WIDTH // 2 - 80, 210, 160, 40),
    "quit": Rect(WIDTH // 2 - 80, 270, 160, 40),
    "instructions": Rect(WIDTH // 2 - 80, 330, 160, 40)
}

difficulty_buttons = {}
button_start_y = 150
button_height = 40
button_spacing = 15
for i, name in enumerate(DIFFICULTY_LEVELS.keys()):
    difficulty_buttons[name] = Rect(WIDTH // 2 - 80, button_start_y + i * (button_height + button_spacing), 160, button_height)
button_start_game = Rect(WIDTH // 2 - 80, button_start_y + len(DIFFICULTY_LEVELS) * (button_height + button_spacing) + 20, 160, 40)

# --- Classes ---

from pgzero.actor import Actor


class Character(Actor):
    def __init__(self, image_prefix, grid_x, grid_y, hp, strength, defense, speed):
        super().__init__(f"{image_prefix}_idle_0", (grid_x * TILE_SIZE, grid_y * TILE_SIZE))
        self.image_prefix = image_prefix
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.frame = 0
        self.hp = hp
        self.strength = strength
        self.defense = defense
        self.speed = speed
        self.moving = False

    def move(self, dx, dy):
        new_x = self.grid_x + dx
        new_y = self.grid_y + dy
        if 0 <= new_x < COLS and 0 <= new_y < ROWS:
            self.grid_x = new_x
            self.grid_y = new_y
            self.topleft = (self.grid_x * TILE_SIZE, self.grid_y * TILE_SIZE)
            self.moving = True

    def animate(self):
        self.frame += 1
        if self.moving:
            self.image = f"{self.image_prefix}_walk_{self.frame % 2}"
        else:
            self.image = f"{self.image_prefix}_idle_{self.frame % 2}"
        self.moving = False


class Hero(Character):
    def __init__(self, grid_x=1, grid_y=1):
        super().__init__("hero", grid_x, grid_y, hp=100, strength=10, defense=5, speed=5)
        self.exp = 0
        self.inventory = []
        self.equipment = {}

    def reset_stats(self):
        self.strength = 10
        self.defense = 5
        self.speed = 5

    def update_stats(self):
        self.reset_stats()
        for item in self.equipment.values():
            for stat, val in item["bonus"].items():
                if hasattr(self, stat):
                    setattr(self, stat, getattr(self, stat) + val)
    
   

    def equip_item(self, item):
        self.equipment[item["type"]] = item
        self.update_stats()

    def unequip_item(self, item_type):
        if item_type in self.equipment:
            del self.equipment[item_type]
        self.update_stats()


class Enemy(Character):
    def __init__(self, grid_x, grid_y, hp, strength, defense, speed, boss=False):
        super().__init__("enemy", grid_x, grid_y, hp, strength, defense, speed)
        self.boss = boss
        self.direction = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        self.can_summon = False
        self.summon_cooldown = 0

    def update_movement(self):
        if random.random() < 0.02:
            dx, dy = self.direction
            new_x = self.grid_x + dx
            new_y = self.grid_y + dy
            if 0 <= new_x < COLS and 0 <= new_y < ROWS:
                self.move(dx, dy)
            else:
                self.direction = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])


# --- Game variables ---
hero = Hero()
enemies = []
boss_enemy = None
combat_enemy = None

# Legendary chest example
legendary_chest = None


# --- Functions ---


def generate_legendary_chests():
    chests = []
    for i in range(3):  # 3 baús
        items = []
        quantity = random.randint(1, 8)
        for _ in range(quantity):
            item = generate_random_item()
            item["rarity"] = "Legendary"
            item["color"] = "red"
            item["level"] = max(current_level, item["level"])
            items.append(item)
        chest = {
            "pos_x": random.randint(1, COLS - 2),
            "pos_y": random.randint(1, ROWS - 2),
            "items": items,
            "opened": False
        }
        chests.append(chest)
    return chests


def draw_healing_zones():
    for zone in healing_zones:
        x = zone["grid_x"] * TILE_SIZE
        y = zone["grid_y"] * TILE_SIZE
        rect = Rect((x, y), (TILE_SIZE, TILE_SIZE))
        
        border_thickness = 1
        # Desenhar borda rosa grossa dentro do retângulo
        for i in range(border_thickness):
            inner_rect = rect.inflate(-2*i, -2*i)  # diminui o retângulo por dentro
            screen.draw.rect(inner_rect, (255, 105, 180))
        
        screen.draw.text("+", center=(x + TILE_SIZE // 2, y + TILE_SIZE // 2), fontsize=32, color="pink")


def draw_instructions():
    screen.clear()
    screen.draw.text("INSTRUCOES", center=(WIDTH // 2, 50), fontsize=50, color="yellow")

    instructions_text = [
        "Objetivo: Mate o chefe final para vencer o jogo.",
        "O chefe, um inimigo muito forte, com ataques devastadores.",
        "Use as setas do TECLADO para mover seu heroi pela dungeon.",
        "",
        "Pressione 'I' para abrir o inventario e equipar itens.",
        "Itens podem ser encontrados em baus lendarios.",
        "Cada item tem bônus de força, defesa e velocidade.",
        "Use 'E' para equipar um item selecionado no inventario.",
        'fique ATENTO ao tipo de item EQUIPADO, pois cada um AFETA atributos diferentes.',
        "Use 'W' e 'S' para navegar pelo inventario.",
        "Use 'D' para vender um item selecionado no inventario.",   
        "Quando encontrar um inimigo, o combate começara.",
        "No combate, pressione ESPACO para atacar.",
        "Derrote todos os inimigos e prepare-se para o chefe!",
        "",
        "Dicas:",
        "- Use itens de cura encontrados na dungeon [QUADRADOS ROSAS].",
        "- Explore bem a dungeon para encontrar baus lendarios.",
        "- Gerencie seu inventario e equipe os melhores itens.",
        "Pressione ENTER para voltar ao menu."
    ]

    y = 120
    for line in instructions_text:
        screen.draw.text(line, (10, y), fontsize=16, color="white")
        y += 16

def draw_legendary_chests():
    for chest in legendary_chests:
        x = chest["pos_x"] * TILE_SIZE
        y = chest["pos_y"] * TILE_SIZE
        color = "gold" if not chest["opened"] else "lightyellow"
        screen.draw.rect(Rect(x, y, TILE_SIZE, TILE_SIZE), color)
        screen.draw.text("C", (x + 10, y + 6), fontsize=24, color="black")



def check_legendary_chest_interaction():
    for chest in legendary_chests:
        if not chest["opened"] and hero.grid_x == chest["pos_x"] and hero.grid_y == chest["pos_y"]:
            chest["opened"] = True
            hero.inventory.extend(chest["items"])



def start_level():
    global legendary_chests
    hero.grid_x = 1
    hero.grid_y = 1
    hero.topleft = (hero.grid_x * TILE_SIZE, hero.grid_y * TILE_SIZE)
    legendary_chests = generate_legendary_chests()



def generate_random_item():
    types = ["Sword", "Shield", "Boots", "Gloves", "Ring"]
    rarities = [("Normal", "white"), ("Rare", "orange"), ("Excellent", "purple"), ("Legendary", "red")]
    item_type = random.choice(types)
    rarity, color = random.choice(rarities)
    level = random.randint(1, 5)

    base_bonus = {
        "Sword": {"strength": 2},
        "Shield": {"defense": 3},
        "Boots": {"speed": 1, "defense": 2},
        "Gloves": {"strength": 2, "speed": 1},
        "Ring": {"strength": 1, "defense": 2},
    }

    rarity_multipliers = {
        "Normal": 1.0,
        "Rare": 1.5,
        "Excellent": 2.0,
        "Legendary": 3.0
    }

    multiplier = rarity_multipliers[rarity]

    bonus = {}
    for stat, val in base_bonus[item_type].items():
        bonus[stat] = int(val * level * multiplier)

    name = f"{item_type} {rarity} Lv{level}"
    return {
        "name": name,
        "type": item_type,
        "rarity": rarity,
        "color": color,
        "level": level,
        "bonus": bonus
    }


def generate_enemies(level, difficulty, boss=False):
    new_enemies = []
    quantity = random.randint(1, 3) if not boss else 1
    for i in range(quantity):
        e = Enemy(
            grid_x=random.randint(1, COLS - 2),
            grid_y=random.randint(1, ROWS - 2),
            hp=int((30 + level * 5) * difficulty),
            strength=int((5 + level * 2) * difficulty),
            defense=2,
            speed=1,
            boss=boss
        )
        new_enemies.append(e)

    if boss:
        boss_enemy = new_enemies[0]
        boss_enemy.hp *= 5
        boss_enemy.strength *= 3
        boss_enemy.can_summon = True
        boss_enemy.summon_cooldown = 3
        return new_enemies, boss_enemy
    else:
        return new_enemies, None


def update_boss():
    global enemies, boss_enemy
    if boss_enemy and boss_enemy.can_summon:
        boss_enemy.summon_cooldown -= 1
        if boss_enemy.summon_cooldown <= 0:
            if len(enemies) < 6:
                summon = Enemy(
                    grid_x=random.randint(1, COLS - 2),
                    grid_y=random.randint(1, ROWS - 2),
                    hp=int(20 * difficulty_multiplier),
                    strength=int(5 * difficulty_multiplier),
                    defense=1,
                    speed=1,
                    boss=False
                )
                enemies.append(summon)
            boss_enemy.summon_cooldown = 3


def advance_level():
    global current_level, enemies, boss_enemy, current_state
    if current_level < MAX_LEVELS:
        current_level += 1
        if current_level == MAX_LEVELS:
            enemies, boss_enemy = generate_enemies(current_level, difficulty_multiplier, boss=True)
            try:
                music.play("boss_music")
            except:
                pass
        else:
            enemies, boss_enemy = generate_enemies(current_level, difficulty_multiplier)
            try:
                music.play("background_music")
            except:
                pass
        start_level()


def draw_menu():
    screen.clear()
    screen.draw.text("DUNGEON ESCAPE", center=(WIDTH // 2, 100), fontsize=48, color="white")
    for name, rect in buttons.items():
        color = "green" if (name == "sound" and not sound_enabled) else "gray"
        screen.draw.filled_rect(rect, color)

        label = "START" if name == "start" else ("SOUND ON" if sound_enabled else "SOUND OFF") if name == "sound" else "QUIT"
        if name == "instructions":
            label = "INSTRUCTIONS"
        screen.draw.text(label, center=rect.center, fontsize=26, color="black")


def draw_difficulty_selection():
    screen.clear()
    screen.draw.text("SELECT DIFFICULTY", center=(WIDTH // 2, 100), fontsize=40, color="white")
    for name, rect in difficulty_buttons.items():
        color = "yellow" if name == selected_difficulty else "gray"
        screen.draw.filled_rect(rect, color)
        screen.draw.text(name, center=rect.center, fontsize=30, color="black")

    if selected_difficulty:
        screen.draw.filled_rect(button_start_game, "green")
        screen.draw.text("START", center=button_start_game.center, fontsize=30, color="black")

def check_collision():

    global current_state, combat_enemy, enemies, hero, boss_enemy

    for enemy in enemies:
        if hero.grid_x == enemy.grid_x and hero.grid_y == enemy.grid_y:
            combat_enemy = enemy
            current_state = STATE_COMBAT
    

def draw_game():
    screen.clear()

    # Desenha o fundo da dungeon em dimgray (como antes)
    for y in range(ROWS):
        for x in range(COLS):
            screen.draw.filled_rect(Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE), "dimgray")

    # Agora desenha as linhas brancas da grade
    for y in range(ROWS + 1):
        y_pos = y * TILE_SIZE
        screen.draw.line((0, y_pos), (COLS * TILE_SIZE, y_pos), "white")
    for x in range(COLS + 1):
        x_pos = x * TILE_SIZE
        screen.draw.line((x_pos, 0), (x_pos, ROWS * TILE_SIZE), "white")

    # Desenha os baús e zonas de cura
    draw_legendary_chests()
    draw_healing_zones()

    # Anima e desenha o herói
    hero.animate()
    screen.blit(hero.image, hero.topleft)

    # Anima e desenha inimigos (com destaque para chefes)
    for enemy in enemies:
        enemy.animate()
        screen.blit(enemy.image, enemy.topleft)
        if enemy.boss:
            rect = Rect(enemy.topleft[0], enemy.topleft[1], TILE_SIZE, TILE_SIZE)
            for i in range(3):
                screen.draw.rect(rect.inflate(i * 4, i * 4), "red")

    # Desenha as estatísticas com espaçamento menor e cor branca
    y_start = 10
    y_spacing = 20  # menos espaçamento

    screen.draw.text(f"HP: {hero.hp}  EXP: {hero.exp}", (10, y_start), fontsize=20, color="white")
    screen.draw.text(f"Strength: {hero.strength}", (10, y_start + y_spacing), fontsize=20, color="white")
    screen.draw.text(f"Defense: {hero.defense}", (10, y_start + 2 * y_spacing), fontsize=20, color="white")
    screen.draw.text(f"Speed: {hero.speed}", (10, y_start + 3 * y_spacing), fontsize=20, color="white")
    screen.draw.text(f"Money: {money} coins", (10, y_start + 4 * y_spacing), fontsize=20, color="white")




check_collision()




def calculate_attributes_with_item(item):
    # Valores base do herói (pode usar herói atual para pegar base real)
    strength = 10
    defense = 5
    speed = 5

    # Soma bônus dos equipamentos atuais, exceto o slot do item que vamos testar
    for slot, equipped in hero.equipment.items():
        if slot != item["type"]:
            for stat, val in equipped["bonus"].items():
                if stat == "strength":
                    strength += val
                elif stat == "defense":
                    defense += val
                elif stat == "speed":
                    speed += val

    # Soma bônus do item hipotético
    for stat, val in item["bonus"].items():
        if stat == "strength":
            strength += val
        elif stat == "defense":
            defense += val
        elif stat == "speed":
            speed += val

    return strength, defense, speed



def draw_inventory():
    global start_visible, item_selected
    screen.draw.text("INVENTARIO (E = Equipar, D = Vender)", (400, 20), fontsize=18, color="yellow")

    global start_visible, item_selected

    total_items = len(hero.inventory)
    end_visible = min(start_visible + items_per_page, total_items)
    y = 60

        # Desenha somente os itens visíveis da "janela" do inventário
    for idx in range(start_visible, end_visible):
        item = hero.inventory[idx]
        color = item["color"]
        prefix = "-> " if item_selected == idx else "   "
        item_text = f"{prefix}{item['name']}"
        text_x, text_y = 400, y
        screen.draw.text(item_text, (text_x, text_y), fontsize=20, color=color)

        # Verifica se o item está equipado e desenha a linha verde
        if any(equipado.get("name") == item["name"] for equipado in hero.equipment.values()):
            text_width = screen.surface.get_rect().width  # largura da tela
            line_y = text_y + 14  # linha abaixo do texto
            screen.draw.line((text_x, line_y), (text_x + 160, line_y), "green")

        y += 30


    # Indicadores de scroll
    if end_visible < total_items:
        screen.draw.text("abaixo", (570, y - 5), fontsize=18, color="white")
    if start_visible > 0:
        screen.draw.text("acima", (570, 60 - 5), fontsize=18, color="white")

    # Equipamentos
    y_equip = y + 20
    screen.draw.text("EQUIPADO:", (400, y_equip), fontsize=18, color="cyan")
    for i, (slot, item) in enumerate(hero.equipment.items()):
        screen.draw.text(f"{slot}: {item['name']}", (400, y_equip + 25 + i * 25), fontsize=18, color=item["color"])

    # Preview do item selecionado (se estiver na janela visível)
    if item_selected is not None and start_visible <= item_selected < end_visible:
        item = hero.inventory[item_selected]
        nova_forca, nova_defesa, nova_velocidade = calculate_attributes_with_item(item)

        diff_strength = nova_forca - hero.strength
        diff_defense = nova_defesa - hero.defense
        diff_speed = nova_velocidade - hero.speed

        def text_diff(value, name):
            sign = "+" if value >= 0 else ""
            color = "green" if value > 0 else ("red" if value < 0 else "white")
            return f"{name}: {sign}{value}", color

        f_text, f_color = text_diff(diff_strength, "Força")
        d_text, d_color = text_diff(diff_defense, "Defesa")
        v_text, v_color = text_diff(diff_speed, "Velocidade")

        screen.draw.text("Com este item equipado:", (400, y_equip + 120), fontsize=18, color="yellow")
        screen.draw.text(f_text, (400, y_equip + 150), fontsize=18, color=f_color)
        screen.draw.text(d_text, (400, y_equip + 175), fontsize=18, color=d_color)
        screen.draw.text(v_text, (400, y_equip + 200), fontsize=18, color=v_color)


combat_log = []

def add_to_combat_log(message):
    global combat_log
    combat_log.append(message)
    # Mantém só as últimas 10 mensagens para não encher demais a tela
    if len(combat_log) > 10:
        combat_log.pop(0)



def clear_combat_log():
    global combat_log
    combat_log = []

MAX_LOG_LINES = 8  # número de linhas visíveis no histórico

def draw_combat():
    screen.clear()
    screen.draw.text("TURN-BASED COMBAT!", center=(WIDTH // 2, 60), fontsize=40, color="red")
    screen.draw.text(f"HERO HP: {hero.hp}", (100, 150), fontsize=30)
    screen.draw.text(f"ENEMY HP: {combat_enemy.hp}", (100, 200), fontsize=30)
    screen.draw.text("PRESS SPACE TO ATTACK", center=(WIDTH // 2, 400), fontsize=25, color="yellow")

    # Desenhar o histórico no canto superior direito
    x = WIDTH - 220  # distância da margem direita
    y = 100 
    for line in combat_log[-MAX_LOG_LINES:]:
        screen.draw.text(line, (x, y), fontsize=20, color="white")
        y += 22


def draw_game_over():
    screen.clear()
    screen.draw.text("GAME OVER", center=(WIDTH // 2, HEIGHT // 2), fontsize=60, color="red")


def draw_victory():
    screen.clear()
    screen.draw.text("CONGRATULATIONS! BOSS DEFEATED!", center=(WIDTH // 2, HEIGHT // 2 - 40), fontsize=40, color="yellow")
    screen.draw.text("PRESS ENTER TO RETURN TO MENU", center=(WIDTH // 2, HEIGHT // 2 + 20), fontsize=25, color="white")






def update():
    global current_state

   
    for zone in healing_zones:
        if hero.grid_x == zone["grid_x"] and hero.grid_y == zone["grid_y"]:
            if hero.hp < 100:
                hero.hp = min(hero.hp + 1, 100)
   

    if current_state == STATE_GAME:
        for enemy in enemies:
            enemy.update_movement()
        update_boss()
        check_collision()


def on_mouse_down(pos):
    global current_state, selected_difficulty, difficulty_multiplier, current_level, enemies, boss_enemy, sound_enabled

    if current_state == STATE_MENU:
        if buttons["start"].collidepoint(pos):
            current_state = STATE_DIFFICULTY_SELECTION
        elif buttons["sound"].collidepoint(pos):
            sound_enabled = not sound_enabled
            if sound_enabled:
                music.play("background_music")
            else:
                music.stop()
        elif buttons["instructions"].collidepoint(pos):
            current_state = STATE_INSTRUCTIONS
        elif buttons["quit"].collidepoint(pos):
            exit()


    elif current_state == STATE_DIFFICULTY_SELECTION:
        for name, rect in difficulty_buttons.items():
            if rect.collidepoint(pos):
                selected_difficulty = name
                difficulty_multiplier = DIFFICULTY_LEVELS[selected_difficulty]
        if selected_difficulty and button_start_game.collidepoint(pos):
            current_level = 1
            enemies, boss_enemy = generate_enemies(current_level, difficulty_multiplier)
            start_level()
            current_state = STATE_GAME
    

def move_hero(dx, dy):
    global hero, sound_enabled
    new_x = hero.grid_x + dx
    new_y = hero.grid_y + dy

    if 0 <= new_x < COLS and 0 <= new_y < ROWS:
        hero.move(dx, dy)
        if sound_enabled:
            sounds.step.play()
        check_collision()
        check_legendary_chest_interaction()
        check_healing_zone(hero)



def draw():
    global current_state, inventory_visible, selected_item_index, visible_start_index, items_per_page
    if current_state == STATE_MENU:
        draw_menu()
    elif current_state == STATE_DIFFICULTY_SELECTION:
        draw_difficulty_selection()
    elif current_state == STATE_GAME:
        draw_game()
        draw_healing_zones()
        if inventory_visible:
            draw_inventory()
        if current_level == MAX_LEVELS:
            screen.draw.text("DERROTE O CHEFE!", center=(WIDTH//2, 10), fontsize=30, color="red")
    
    elif current_state == STATE_INSTRUCTIONS:
        draw_instructions()
    elif current_state == STATE_COMBAT:
        draw_combat()
    elif current_state == STATE_GAME_OVER:
        draw_game_over()
    elif current_state == STATE_VICTORY:
        draw_victory()
   

def calculate_sell_price(item):
    # Função exemplo para calcular preço de venda
    base_price = item.get("level", 1) * 10
    rarity_multiplier = {"Normal": 1, "Rare": 2, "Excellent": 3, "Legendary": 5}
    return base_price * rarity_multiplier.get(item.get("rarity", "Normal"), 1)

def check_healing_zone(hero):
    for zone in healing_zones:
        if hero.grid_x == zone["grid_x"] and hero.grid_y == zone["grid_y"]:
            if hero.hp < 100:
                hero.hp = min(hero.hp + 15, 100)
                print("Cura recebida! HP atual:", hero.hp)


def reset_hero():
    global hero
    # Reseta atributos do heroi, inventario, hp, etc
    hero.hp = 100
    hero.exp = 0
    hero.inventory = []
    hero.equipment = {}
    hero.strength = 10
    hero.defense = 5
    hero.speed = 5




def update_hero_attributes():
    # Atributos base
    hero.strength = 10
    hero.defense = 5
    hero.speed = 5

    # Somar bônus dos equipamentos
    for item in hero.equipment.values():
        for stat, val in item["bonus"].items():
            if hasattr(hero, stat):
                setattr(hero, stat, getattr(hero, stat) + val)



def calculate_sale_price(item):
    base_valor = {
        "Normal": 10,
        "Raro": 30,
        "Excelente": 60,
        "Lendario": 100
    }

    preco = base_valor.get(item["rarity"], 10)

    preco *= item["level"]
    return preco


def on_key_down(key):
    global current_state, hero, enemies, combat_enemy, current_level
    global difficulty_selected, difficulty_multiplier, sound_enabled, music, legendary_chest
    global selected_item_index, visible_start_index, items_per_page
    global inventory_visible, selected_difficulty
    global boss_enemy, enemy_in_combat
    global item_selected, start_visible, difficulties
    global difficulties




    if current_state == STATE_DIFFICULTY_SELECTION:
        options = list(difficulties.keys())
        if difficulty_selected not in options:
            difficulty_selected = options[0]

        index = options.index(difficulty_selected)

        if key == keys.UP:
            index = (index - 1) % len(options)
            difficulty_selected = options[index]

        elif key == keys.DOWN:
            index = (index + 1) % len(options)
            difficulty_selected = options[index]

        elif key == keys.RETURN:
            difficulty_multiplier = difficulties[difficulty_selected]
            current_level = 1
            enemies = generate_enemies(current_level, difficulty_multiplier)
            start_level()
            current_state = STATE_GAME

        return
    
   
        
    if current_state == STATE_GAME:
        dx, dy = 0, 0
        if key == keys.UP:
            dy = -1
        elif key == keys.DOWN:
            dy = 1
        elif key == keys.LEFT:
            dx = -1
        elif key == keys.RIGHT:
            dx = 1

        if dx != 0 or dy != 0:
            new_x = hero.grid_x + dx
            new_y = hero.grid_y + dy
            if 0 <= new_x < COLS and 0 <= new_y < ROWS:
                hero.move(dx, dy)
                if sound_enabled:
                    sounds.step.play()
                check_collision()
                check_legendary_chest_interaction()
        elif key == keys.I:
            inventory_visible = not inventory_visible
            if inventory_visible:
                item_selected = 0 if hero.inventory else None
                start_visible = 0

        if inventory_visible:
                if key == keys.W and item_selected is not None:
                    if item_selected > 0:
                        item_selected -= 1
                        # Ajusta a janela de itens visíveis para cima
                        if item_selected < start_visible:
                            start_visible = item_selected

                elif key == keys.S and item_selected is not None:
                    if item_selected < len(hero.inventory) - 1:
                        item_selected += 1
                        # Ajusta a janela de itens visíveis para baixo
                        if item_selected >= start_visible + items_per_page:
                            start_visible = item_selected - items_per_page + 1

                elif key == keys.E and item_selected is not None:
                    item = hero.inventory[item_selected]
                    hero.equipment[item["type"]] = item
                    update_hero_attributes()
                    inventory_visible = False
                    item_selected = None

                elif key == keys.D and item_selected is not None:
                    item = hero.inventory.pop(item_selected)
                    sale_price = calculate_sale_price(item)
                    global money
                    money += sale_price
                    print(f"Item vendido por {sale_price} moedas: {item['name']}")
                    # Ajusta seleção
                    if item_selected >= len(hero.inventory):
                        item_selected = len(hero.inventory) - 1 if hero.inventory else None
                    # Ajusta janela se necessário
                    if start_visible > 0 and start_visible + items_per_page > len(hero.inventory):
                        start_visible = max(0, len(hero.inventory) - items_per_page)

    if current_state == STATE_INSTRUCTIONS:
        if key == keys.RETURN:
            current_state = STATE_MENU

    elif current_state == STATE_COMBAT:
       
        if key == keys.SPACE:
            damage_hero = random.randint(hero.strength // 2, hero.strength)
            combat_enemy.hp -= damage_hero

            add_to_combat_log(f"Hero dealt {damage_hero} damage to {combat_enemy.image_prefix}!")
            print(f"Hero dealt {damage_hero} damage!")

            if combat_enemy.hp <= 0:
                hero.exp += 10
                clear_combat_log()
                drop = generate_random_item()
                hero.inventory.append(drop)
                if getattr(combat_enemy, "boss", False):
                    print("Boss defeated! You won the game!")
                    current_state = STATE_VICTORY
                    try:
                        music.play("victory_music")
                    except:
                        pass
                    enemies.clear()
                else:
                    enemies.remove(combat_enemy)
                    update_boss()

                    if not enemies or (len(enemies) == 1 and any(getattr(i, "boss", False) for i in enemies)):
                        print("All enemies defeated! Advancing level...")
                        advance_level()
                    current_state = STATE_GAME
            else:
                damage_enemy = random.randint(3, 30) - hero.defense // 2
                damage_enemy = max(1, damage_enemy)
                hero.hp -= damage_enemy

                add_to_combat_log(f"{combat_enemy.image_prefix} dealt {damage_enemy} damage to Hero!")
                print(f"Enemy dealt {damage_enemy} damage!")

            if hero.hp <= 0:
                current_state = STATE_GAME_OVER

    elif current_state == STATE_VICTORY:
        if key == keys.RETURN:
            current_state = STATE_MENU
            current_level = 1
            enemies = generate_enemies(current_level, difficulty_multiplier)
            reset_hero()
            try:
                music.play("background_music")
            except:
                pass




def animate():
    hero.frame += 1
    for enemy in enemies:
        enemy.frame += 1

clock.schedule_interval(animate, 0.3)