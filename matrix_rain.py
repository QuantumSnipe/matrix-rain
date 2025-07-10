import curses
import random
import time

# Character list for the rain matrix
CHAR_LIST = list("0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ｡｢｣､･ｦｧｨｩｪｫｬｭｮｯｰｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝﾞﾟ")

FPS = 30
FRAME_DELAY = 1 / FPS 


def matrix_intro(stdscr):
	"""Display a brief intro sequence filling the screen with random 0s and 1s."""
	height, width = stdscr.getmaxyx()
	curses.start_color()
	curses.init_pair(5, curses.COLOR_GREEN, curses.COLOR_BLACK)
	stdscr.nodelay(True) 

	start_time = time.time()

	while True:
		for y in range(height):
			for x in range(width):
				char = random.choice(['0', '1'])
				try:
					stdscr.attron(curses.color_pair(5) | curses.A_BOLD)
					stdscr.addstr(y, x, char)
					stdscr.attroff(curses.color_pair(5) | curses.A_BOLD)
				except curses.error:
					pass
		stdscr.refresh()
		time.sleep(0.04)
		key = stdscr.getch()
		if key != -1 or (time.time() - start_time > 3):
			break


def init_colors():
	"""Initialize color pairs for the matrix rain effect, with custom shades, if supported."""
	curses.start_color()

	# Standard color pairs
	curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
	curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)

	# Default head color
	head_color = curses.color_pair(1) | curses.A_BOLD

	# Default trail shades
	trail_shades = [curses.color_pair(2) for _ in range(6)]

	# Gradient
	if curses.can_change_color():
		curses.init_color(20, 600, 1000, 900)
		curses.init_pair(20, 20, curses.COLOR_BLACK)
		head_color = curses.color_pair(20) | curses.A_BOLD

		# Custom trail shades: from less dim to bright green for smoother fade
		for i in range(1, 7):
			intensity = min(1000, int(200 * i) + 200)
			curses.init_color(10 + i, 0, intensity, 0)
			curses.init_pair(10 + i, 10 + i, curses.COLOR_BLACK)
		trail_shades = [curses.color_pair(10 + i) for _ in range(1, 7)]

	return trail_shades, head_color


class Column:
	"""Represents a single column in the matrix rain."""
	def __init__(self, height):
		self.height = height
		self.head_y = None
		self.trail = [] # List of (y, char) tuples
		self.length = None
		self.speed = None
		self.state = 'dead' # States: 'active', 'fading', 'dead'
		self.dead_time = 0

	def reset(self):
		"""Resets the column to start new stream from the top."""
		self.head_y = 0
		self.trail = []
		self.length = random.randint(6, 16)
		self.speed = random.randint(1, 3)
		self.state = 'active'


def main(stdscr):
	curses.curs_set(0) # Hide the cursor
	stdscr.nodelay(True)
	trail_shades, head_color = init_colors()
	matrix_intro(stdscr)

	height, width = stdscr.getmaxyx()

	# Create the columns
	columns = [Column(height) for _ in range(width)]

	# Stagger initial starts
	for c in columns:
		c.state = 'dead'
		c.dead_time = random.randint(0, 100)

	frame = 0

	while True:
		try:
			key = stdscr.getch()
			if key == ord('q'):
					break
			
			for x, c in enumerate(columns):
				if c.state == 'dead':
					c.dead_time = max(0, c.dead_time - 1)
					if c.dead_time <= 0:
						c.reset()
					continue # No drawing in dead state
				
				# This makes slower streams to update less frequently, creating varied falling speeds. 
				if frame % c.speed != 0:
					continue
				
				if c.state == 'active':
					if random.random() < 0.001:
						c.state = 'fading'
						continue

					# Add new char at head
					char = random.choice(CHAR_LIST)
					c.trail.append((c.head_y, char))

					# Remove oldest if trail too long
					if len(c.trail) > c.length:
						old_y, _ = c.trail.pop(0)
						try:
							stdscr.addstr(old_y, x, ' ')
						except curses.error:
							pass

					# Occasionaly change a char in the trail
					for i in range(len(c.trail)):
						if random.random() < 0.005:
							y, _ = c.trail[i]
							c.trail[i] = (y, random.choice(CHAR_LIST))

					# Advance stream head
					c.head_y += 1 
					if c.head_y >= c.height:
						c.state = 'fading'

				elif c.state == 'fading':
					# Pop oldest character to fade out
					if c.trail:
						old_y, _ = c.trail.pop(0)
						try:
							stdscr.addstr(old_y, x, ' ')
						except curses.error:
							pass
					if not c.trail:
						c.state = 'dead'
						c.dead_time = random.randint(10, 40)

				# Draw the trail
				if c.trail:
					trail_len = len(c.trail)
					# Draw body
					for idx, (y, char) in enumerate(c.trail[:-1] if c.state == 'active' else c.trail):
						ratio = idx / max(1, trail_len - 2 if c.state == 'active' else trail_len - 1)
						shade_index = min(len(trail_shades) - 1, int(ratio * (len(trail_shades) - 1)))
						color_attr = trail_shades[shade_index]
						try:
							stdscr.attron(color_attr)
							stdscr.addstr(y, x, char)
							stdscr.attroff(color_attr)
						except curses.error:
							pass

					# Draw head if active
					if c.state == 'active' and c.trail:
						head_y, head_char = c.trail[-1]
						try:
							stdscr.attron(head_color)
							stdscr.addstr(head_y, x, head_char)
							stdscr.attroff(head_color)
						except curses.error:
							pass
			
			stdscr.noutrefresh()
			curses.doupdate()
			time.sleep(FRAME_DELAY)
			frame += 1

		except KeyboardInterrupt:
			break

if __name__ == "__main__":
	curses.wrapper(main)


