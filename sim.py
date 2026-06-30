import pygame
import sys
from pygame.locals import *

class Vec2:

    def __init__(self, x, y):
        self.x = x
        self.y = y
    
    def __add__(self, other):
        return Vec2(self.x+other.x, self.y+other.y)
    
    def __sub__(self, other):
        return Vec2(self.x - other.x, self.y - other.y)
    
    def __neg__(self):
        return Vec2(-self.x, -self.y)
    
    def __mul__(self, scalar):
        return Vec2(self.x * scalar, self.y * scalar)
    
    def __rmul__(self, scalar):
        return self.__mul__(scalar)
    
    def dot (self, other):
        return (self.x*other.x + self.y*other.y)

    def length(self):
        return ((self.x)**2+(self.y)**2)**(1/2)
    
    def normalize(self):
        length = self.length()
        if length > 0:
            return Vec2(self.x / length, self.y / length)
        return Vec2(0, 0)

    @staticmethod
    def direction_between(a, b):
        return (b-a).normalize()
    
class Ray:

    def __init__(self, origin, direction):
        self.origin = origin
        self.direction = direction
        self.point = None
        self.big_square = None
        self.small_square = None

    def at(self, t):
        return self.origin + self.direction*t
    
    @staticmethod
    def from_points(a, b):
        return Ray(a, Vec2.direction_between(a, b))
    
class Wall:

    def __init__(self, start, end):
        self.start = start
        self.end = end

    def draw(self, screen, mirror_color, width):
        pygame.draw.line(screen, mirror_color, (self.start.x, self.start.y), (self.end.x, self.end.y), width)

    def intersect(self, ray):
        wall_dir = self.end-self.start
        a = ray.origin.x
        b = ray.direction.x
        c = self.start.x
        d = wall_dir.x
        e = ray.origin.y
        f = ray.direction.y
        g = self.start.y
        h = wall_dir.y
        if  (b*h - f*d) == 0:
            return None
        t = ((c-a)*h - (g-e)*d) / (b*h - f*d)
        s = ((c-a)*f - (g-e)*b) / (b*h - f*d)
        if t >= 0 and 0 <= s <= 1:
            return t
        return None
    
    def reflect(self, ray, t, eps):
        wall_dir = Vec2.direction_between(self.start, self.end)
        n = Vec2(wall_dir.y, -wall_dir.x)
        if Vec2.dot(n, ray.direction) > 0:
            n = Vec2(-wall_dir.y, wall_dir.x)
        reflected_ray = Ray(ray.at(t)+n*eps, ray.direction - 2*(Vec2.dot(ray.direction, n)*n))
        return reflected_ray

class Circle:

    def __init__(self, center, dot):
        self.center = center
        self.dot = dot
        self.radius = (dot-center).length()
    
    def draw(self, screen, mirror_color, width):
        pygame.draw.circle(screen, mirror_color, (self.center.x, self.center.y), self.radius, width)
    
    def intersect(self, ray):
        B = 2*(ray.direction.x*(ray.origin.x-self.center.x)+ray.direction.y*(ray.origin.y-self.center.y))
        C = (ray.origin.x-self.center.x)**2 + (ray.origin.y-self.center.y)**2 - self.radius**2
        D = B**2 - 4*C
        if D<0:
            return None
        t1 = (-B + D**(0.5))/2
        t2 = (-B - D**(0.5))/2
        if t2 >= 0:
            return t2
        elif t1 >= 0:
            return t1
        return None
    
    def reflect(self, ray, t, eps):
        n = Vec2.direction_between(self.center, ray.at(t))
        if Vec2.dot(n, ray.direction) > 0:
            n = -n
        reflected_ray = Ray(ray.at(t)+n*eps, ray.direction - 2*(Vec2.dot(ray.direction, n)*n))
        return reflected_ray

class App:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((1000, 600))
        pygame.display.set_caption("Симуляция лучей")
        self.font = pygame.font.Font(None, 18)
        self.width = self.screen.get_width()
        self.height = self.screen.get_height()
        self.ray_max_length = (self.width**2+self.height**2)**0.5
        self.grid_size = 5
        self.eps = 1e-4
        self.max_bounces = 500
        self.grid_color = (127,146,146)
        self.ray_color = (255,255,0)
        self.mirror_color = (255,255,255)
        self.squares_color = (255,0,0)
        self.text_color = (255,255,255)
        self.ray_width = 1
        self.objects_width = 2
        self.drawing_tool = False
        self.drawing_rays = False
        self.show_grid = False
        self.enable_magnetism = False
        self.clear = False
        self.show_squares = True
        self.temp_obj = None
        self.current_tool = 'flat_mirror'
        self.rays = []
        self.objects = []
        self.temp_rays = []
        self.rays_to_draw = []
        self.all_rays = []
        self.tool_classes = {
    'flat_mirror': Wall,
    'circular_mirror': Circle
}
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == KEYDOWN:
                mods = pygame.key.get_mods()
                if event.key == K_1:
                    self.current_tool = 'flat_mirror'
                elif event.key == K_2:
                    self.current_tool = 'circular_mirror'
                elif event.key == K_z and (mods and KMOD_CTRL):
                    if self.objects != []:
                        self.objects.pop()
                elif event.key == K_x and (mods and KMOD_CTRL):
                    if self.rays != []:
                        self.rays.pop()
                elif event.key == K_q:
                    self.show_squares = not(self.show_squares)
                elif event.key == K_m:
                    self.enable_magnetism = not(self.enable_magnetism)
                    self.show_grid = not(self.show_grid)

            if event.type == MOUSEBUTTONDOWN:
                if event.button == 3:
                    if self.drawing_tool == False:
                        self.tool_start = self.mouse_pos(event)
                        self.drawing_tool = True
                    else: 
                        self.tool_dot()
                elif event.button == 1:
                    if self.drawing_rays == False:
                        self.ray_origin = self.mouse_pos(event)
                        self.drawing_rays = True
                    else:
                        self.ray_dot()
                elif event.button == 2:
                    self.clear = True

            if event.type == MOUSEMOTION:
                if self.drawing_rays:
                    self.ray_point = self.mouse_pos(event)
                    self.temp_rays.clear()
                    if self.not_same(self.ray_origin, self.ray_point):
                        temp_ray = Ray.from_points(self.ray_origin, self.ray_point)
                        self.temp_rays.clear()
                        temp_ray.big_square = (temp_ray.origin.x-3, temp_ray.origin.y-3, 6, 6)
                        temp_ray.small_square = (self.ray_point.x-2, self.ray_point.y-2, 4, 4)
                        self.temp_rays = [temp_ray]
                        temp_ray.point = self.ray_point
                        
                elif self.drawing_tool:
                    self.temp_obj = None
                    self.tool_end = self.mouse_pos(event)
                    self.temp_obj = self.tool_classes[self.current_tool](self.tool_start, self.tool_end)

            if event.type == MOUSEBUTTONUP:
                if event.button == 3:
                    self.tool_end = self.mouse_pos(event)
                    self.tool_dot()
                elif event.button == 1:
                    self.temp_rays.clear()
                    self.ray_point = self.mouse_pos(event)
                    self.ray_dot()
    
    def tool_dot(self):
        if self.not_same(self.tool_start, self.tool_end):
            obj = self.tool_classes[self.current_tool](self.tool_start, self.tool_end)
            self.temp_obj = None
            self.objects.append(obj)
            self.drawing_tool = False

    def ray_dot(self):
        if self.not_same(self.ray_point, self.ray_origin):
            ray = Ray.from_points(self.ray_origin, self.ray_point)
            ray.point = self.ray_point
            ray.big_square = (ray.origin.x-3, ray.origin.y-3, 6, 6)
            ray.small_square = (ray.point.x-2, ray.point.y-2, 4, 4)
            self.rays.append(ray)
            self.drawing_rays = False

    def update(self):
        self.rays_to_draw.clear()
        self.all_rays = self.rays + self.temp_rays
        for ray in self.all_rays:
            order = [ray]
            i = 0
            while order and i < self.max_bounces:
                i+=1
                ray = order.pop(0)
                t = self.ray_max_length
                closest_obj = None
                for obj in self.objects:
                    t_current = obj.intersect(ray)
                    if t_current is not None and t_current < t and t_current > 0:
                        t = t_current
                        closest_obj = obj
                if self.temp_obj is not None: 
                    t_temp = self.temp_obj.intersect(ray)
                    if t_temp is not None:
                        if t_temp > 0 and t_temp < t:
                            t = t_temp
                            closest_obj = self.temp_obj
                end_point = ray.at(t)
                self.rays_to_draw.append(((ray.origin.x, ray.origin.y), (end_point.x, end_point.y)))
                if t != self.ray_max_length:
                    order.append(closest_obj.reflect(ray, t, self.eps))
    
    def render(self):
        self.screen.fill((0,0,0))
        self._draw_grid()
        self._draw_objects()
        self._draw_rays()
        self._draw_ui()
        pygame.display.flip()

    def _draw_grid(self):
        if self.show_grid:
            for x in range(0, self.width, self.grid_size):
                pygame.draw.line(self.screen, self.grid_color, (x, 0), (x, self.height), 1)
            for y in range(0, self.height, self.grid_size):
                pygame.draw.line(self.screen, self.grid_color, (0, y), (self.width, y), 1)

    def _draw_objects(self):
        for obj in self.objects:
            obj.draw(self.screen, self.mirror_color, self.objects_width)
        if self.temp_obj is not None:
            self.temp_obj.draw(self.screen, self.mirror_color, self.objects_width)

    def _draw_rays(self):
        for ((a_x, a_y), (b_x, b_y)) in self.rays_to_draw:
            pygame.draw.line(self.screen, self.ray_color, (a_x, a_y), (b_x, b_y), self.ray_width)
        if self.show_squares:
            for ray in self.all_rays:
                if ray.big_square and ray.small_square:
                    pygame.draw.rect(self.screen, self.squares_color, ray.big_square)
                    pygame.draw.rect(self.screen, self.squares_color, ray.small_square)

    def _draw_ui(self):
        self.draw_text(f'Current tool is {self.current_tool}', 10, 10, self.text_color)
        self.draw_text(f'Magnetism is {self.enable_magnetism}', 10, 30, self.text_color)
    
    def draw_text(self, text, x, y, color):
        text_surface = self.font.render(text, True, color)
        self.screen.blit(text_surface, (x, y))

    def not_same(self, a, b):
        return a.x != b.x or a.y != b.y
                    
    def mouse_pos(self, event):
        point = Vec2(*event.pos)
        if self.enable_magnetism:
            x = round(point.x / self.grid_size) * self.grid_size
            y = round(point.y / self.grid_size) * self.grid_size
            return Vec2(x, y)
        return point
    
    def run(self):
        while True:
            self.handle_events()
            self.update()
            self.render()
    
if __name__ == "__main__":
    app = App()
    app.run()