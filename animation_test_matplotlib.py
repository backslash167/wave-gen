import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation


class BlitManager:
    def __init__(self, canvas, animated_artists=()):
        self.canvas = canvas
        self._bg = None
        self._artists = list(animated_artists)
        canvas.mpl_connect("draw_event", self.on_draw)

    def on_draw(self, event):
        cv = self.canvas
        if event is not None and event.canvas != cv:
            return  # Ignore events from a different canvas
        if self._bg is None:
            self._bg = cv.copy_from_bbox(cv.figure.bbox)
        self._draw_animated()

    def _draw_animated(self):
        for a in self._artists:
            self.canvas.figure.draw_artist(a)

    def update(self):
        if self._bg is None:
            self.on_draw(None)
        else:
            self.canvas.restore_region(self._bg)
            self._draw_animated()
            self.canvas.blit(self.canvas.figure.bbox)

fig, ax = plt.subplots()
x = np.linspace(0, 2 * np.pi, 500)
y = 0.5 * np.sin(x)
line, = ax.plot(x, y, animated=True)
ax.set_xlim(0, 2 * np.pi)
ax.set_ylim(-1, 1)

bm = BlitManager(fig.canvas, [line])

def update(frame):
    y = 0.5 * np.sin(x + frame / 10)
    line.set_ydata(y)
    bm.update()

ani = FuncAnimation(fig, update, frames=np.arange(0, 1000), interval=16, repeat=True)
plt.show()

