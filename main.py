from collections import deque
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ListProperty
from kivy.graphics.texture import Texture
from kivy.graphics.vertex_instructions import SmoothLine
from kivy.graphics import Rectangle, Line, Color, Point
from kivy.clock import Clock

from cymaze import Maze, eDirection_Up, eDirection_Down, eDirection_Right, eDirection_Left

def show_direction(n):
    return (n & eDirection_Up and 'up' or '',
            n & eDirection_Right and 'right' or '',
            n & eDirection_Down and 'down' or '',
            n & eDirection_Left and 'left' or '',
           )

def left_hand_order(last_pos, (x,y)):
    l = [eDirection_Up, eDirection_Right, eDirection_Down, eDirection_Left] * 2
    if not last_pos:
        offset = 0
    else:
        lx, ly = last_pos
        if lx > x:
            #left
            offset = 2
        elif lx < x:
            # right
            offset = 0
        elif ly > y:
            # up
            offset = 3
        elif ly < y:
            # down
            offset = 1
        else:
            assert False
    return l[offset:offset+4]

class MazeView(Widget):
    points = ListProperty([])

    def __init__(self, mazeSize, **kwargs):
        super(MazeView, self).__init__(**kwargs)

        self.mazeSize = mazeSize
        self.maze = Maze(mazeSize)
        self.maze.generate()

        self.texture = None
        with self.canvas:
            self.rectangle = Rectangle(pos=self.pos, size=self.size)
            Color(1., 0, 0)
            self.lines = Line(points=self.points, pointsize=1)

        Clock.schedule_once(self.search)
        self.step_event = None

    def search(self, dt):
        target = (self.mazeSize-1, self.mazeSize-1)
        data = self.maze.maze
        direction = {
            eDirection_Up : (0, -1),
            eDirection_Down : (0, 1),
            eDirection_Left : (-1, 0),
            eDirection_Right : (1, 0),
        }

        remember = set()

        def get(x,y):
            return data[x+self.mazeSize*y]

        q = deque()
        q.append( ((0,0), self.translate_grid((0,0)), None) )
        def step(dt=None):
            if not q:
                #Clock.unschedule(step)
                print 'no way'
                return False
            (x,y), path, last_pos = q.popleft()
            if (x,y) == target:
                #Clock.unschedule(step)
                self.points = path
                print 'success'
                return False

            n = get(x, y)
            # left hand principle
            for d in left_hand_order(last_pos, (x,y)):
                if n & d:
                    dx,dy = direction[d]
                    nx = x+dx
                    ny = y+dy
                    if (nx,ny) in remember:
                        continue
                    if 0<=nx<self.mazeSize and 0<=ny<self.mazeSize:
                        q.append(((nx,ny), path+self.translate_grid((nx,ny)), (x,y)))
                        remember.add((nx,ny))
            return True
        while step():
            pass
        #self.step_event = Clock.schedule_interval(step, 0)

    def translate_grid(self, (x,y)):
        #y = self.mazeSize-y-1
        cellSize = int(self.size[0] / self.mazeSize)
        offset = cellSize / 2 + 1
        return (cellSize * x + offset + self.pos[0], self.size[0] - (cellSize * y + offset)-1 + self.pos[1])

    def on_size(self, instance, value):
        Clock.schedule_once(self.init_texture)

    def on_points(self, instance, value):
        self.lines.points = value

    def init_texture(self, dt):
        print 'pos', self.pos
        self.texture = Texture.create(size=self.size, colorfmt='rgb')
        self.rectangle.size = self.size
        self.rectangle.texture = self.texture

        self.texture.add_reload_observer(self.populate_texture)
        self.populate_texture(self.texture)

        self.maze.save_bmp('/tmp/test.bmp', self.size[0])

    def render_buffer(self, imageSize):
        buf = bytearray(imageSize*imageSize*3)
        self.maze.render(buf, imageSize)
        return buf
    
    def populate_texture(self, texture):
        buf = self.render_buffer(self.size[0])
        texture.blit_buffer(buf)

    def on_touch_down(self, touch):
        if self.step_event:
            self.step_event.cancel()
        self.points = []
        self.maze.generate()
        self.populate_texture(self.texture)
        # restart search
        Clock.schedule_once(self.search)
        return True

class MainApp(App):
    def build(self):
        root = Widget()
        view = MazeView(63, size=(512, 512))
        root.add_widget(view)
        return root

if __name__ == '__main__':
    MainApp().run()
