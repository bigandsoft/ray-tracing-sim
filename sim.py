import pygame
import sys

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

    def leng(self):
        return ((self.x)**2+(self.y)**2)**(1/2)

    @staticmethod
    def direction_between(A, B):
        return (B-A).normalize()
    
    def normalize(self):
        length = self.leng()
        if length > 0:
            return Vec2(self.x / length, self.y / length)
        return Vec2(0, 0)

def rebuild_scene(rays, objects):
    screen.fill((0, 0, 0))
    for obj in objects:
        type(obj).draw(obj)
    for ray in rays:
        order = [ray]
        i = 0
        while order and i < 500:
            i += 1
            ray = order.pop(0)
            t = ray_max_length
            closest_obj = None
            for obj in objects:
                t_current = obj.intersect(ray)
                if t_current is not None and t_current < t and t_current > 0:
                    t = t_current
                    closest_obj = obj
            if t > 0:
                end_point = ray.at(t)
                pygame.draw.line(screen, (255, 255, 0), (ray.origin.x, ray.origin.y), (end_point.x, end_point.y), 2)
                if t != ray_max_length:
                    order.append(closest_obj.reflect(ray, t))
    return 0


class Ray:
    def __init__(self, origin, direction):
        self.origin = origin
        self.direction = direction

    def at(self, t):
        return self.origin + self.direction*t
    
    @staticmethod
    def from_points(A, B):
        return Ray(A, Vec2.direction_between(A, B))
    
class Wall:

    def __init__(self, start, end):
        self.start = start
        self.end = end

    def draw(self):
        pygame.draw.line(screen, (50,205,50), (self.start.x, self.start.y), (self.end.x, self.end.y), 2)
        return

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
    def reflect(self, ray, t):
        wall_dir = Vec2.direction_between(self.start, self.end)
        n = Vec2(wall_dir.y, -wall_dir.x)
        if Vec2.dot(n, ray.direction) > 0:
            n = Vec2(-wall_dir.y, wall_dir.x)
        reflected_ray = Ray(ray.at(t)+n*0.0001, ray.direction - 2*(Vec2.dot(ray.direction, n)*n))
        return reflected_ray
        
pygame.init()

screen = pygame.display.set_mode((1900, 1000))
objects = []
null_v = Vec2(0,0)
rays = [Ray.from_points(null_v, null_v)]
ray_max_length = (screen.get_width()**2 + screen.get_height()**2)**0.5
refl_rays = []
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 3:
                start = Vec2(*event.pos)
            elif event.button == 1:
                A = Vec2(*event.pos)
            elif event.button == 2:
                rays = []
                objects = []
                screen.fill((0, 0, 0))
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 3:
                end = Vec2(*event.pos)
                wall = Wall(start, end)
                objects.append(wall)
                rebuild_scene(rays, objects)
            elif event.button == 1:
                B = Vec2(*event.pos)
                ray = Ray.from_points(A, B)
                rays.append(ray)
                rebuild_scene(rays, objects)

    pygame.display.flip()