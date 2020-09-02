import os
import sys
import time
import re
import selectors


def atoi(text):
    return int(text) if text.isdigit() else text

def natural_keys(text):
    '''
    alist.sort(key=natural_keys) sorts in human order
    http://nedbatchelder.com/blog/200712/human_sorting.html
    (See Toothy's implementation in the comments)
    '''
    return [ atoi(c) for c in re.split(r'(\d+)', text) ]


class Viewer: 
	maxLengthHexText = 0
	splitAt = 8
	currentLine = 0
	second_buffer = []
	first_buffer = []
	f1 = ""
	f2 = ""
	f1_data = None
	f2_data = None
	opt_txt = ""
	only_changed = False

	def load(self, f1, f2, opt_txt=""):
		self.f1 = f1
		self.f2 = f2
		self.opt_txt = opt_txt
		data1 = open(f1, "rb")
		data2 = open(f2, "rb")

		self.f1_data = data1.read()
		self.f2_data = data2.read()

		printer.render()
		printer.draw()

	def render(self): # actually load the buffer
		size = 16
		self.second_buffer.clear()
		prevparts = reshape(self.f1_data, size)
		nextparts = reshape(self.f2_data, size)

		longest_prefix = len(hex(len(nextparts) * size)[2:])
		prefixes = [hex(x * size)[2:] for x in range(len(nextparts))]
		adjusted_prefixes = ["0x" + ("0" * (longest_prefix - len(x))) + x for x in prefixes]

		for i in range(len(nextparts)):
			if self.only_changed and prevparts[i] == nextparts[i]:
				continue
			self.second_buffer.append(self._show(adjusted_prefixes[i], prevparts[i], nextparts[i]))
		self.first_buffer = self.second_buffer.copy()

	def draw(self): # print the text out
		rows, columns = self.getsize()
		out = chr(27) + "[2J"
		time.sleep(0.05)
		out += self.opt_txt + "\n"

		file_text = self.f1 + " -> " + self.f2
		surrounding_space = columns - len(file_text)
		centered_text = (" " * (surrounding_space // 2)) + file_text + "\n\n"
		out += centered_text

		targetRows = self.first_buffer[self.currentLine : self.currentLine + rows]

		for ln in targetRows:
			out += ln + "\n"
		sys.stdout.write(out)
		sys.stdout.flush()

	def _show(self, prefix, prev, next):
		visible_length = 0
		out = prefix + "   "
		visible_length += len(out)
		for i in range(len(next)):
			is_same = prev[i] == next[i]
			
			if i % self.splitAt == 0 and i > 0:
				out += "- "
				visible_length += 2
				
			leading = "0" if next[i] < 16 else ""
			hex_byte = leading + hex(next[i])[2:].upper()
			if is_same:
				out += hex_byte + " "
			else:
				out += red(hex_byte) + " "
			visible_length += len(hex_byte) + 1
				
		width = visible_length
		if width > self.maxLengthHexText:
			self.maxLengthHexText = width
		if width < self.maxLengthHexText:
			out += " " * (self.maxLengthHexText - width)
			
		out += "\t"

		for i in range(len(next)):
			out += chr(next[i]) if 32 <= next[i] <= 126 else "."

		return out

	def scrolldown(self, dist=3):
		rows, _ = self.getsize()
		max = len(self.first_buffer) - rows  # lowest the buffer cursor can go, after accounting for displayed rows

		if self.currentLine == max:
			return

		if self.currentLine + dist <= max:
			self.currentLine += dist
		else:
			self.currentLine = max

		self.draw()

	def scrollup(self, dist=3):
		if self.currentLine == 0:
			return

		if self.currentLine - dist >= 0:
			self.currentLine -= dist
		else:
			self.currentLine = 0
		self.draw()

	def getsize(self):
		rows, columns = os.popen('stty size', 'r').read().split()
		return (int(rows) - 5, int(columns))

			
	
def reshape(lst, n):
	return [lst[i*n:(i+1)*n] for i in range(len(lst)//n)]


def red(text):
	return '\u001b[38;5;1m' + text + '\u001b[0m'

def processKeyboardKey(stdin, mask):
	global current_file, printer, file_count
	c = stdin.read(8)
	if c:
		if c == "\x1b[B":  # Up arrow
			printer.scrolldown()
		if c == "\x1b[A":  # Up arrow
			printer.scrollup()
		if c == "\x1b[6~":  # Pg Down
			rows, _ = printer.getsize()
			printer.scrolldown(rows)
		if c == "\x1b[5~":  # Pg Up
			rows, _ = printer.getsize()
			printer.scrollup(rows)
		if c == ".":
			printer.only_changed = not printer.only_changed
			printer.render()
			printer.draw()
		if c == "+":
			if current_file + 2 >= file_count:
				return
			current_file += 1
			printer.load(sys.argv[1] + "//" + patterened_files[current_file], sys.argv[1] + "//" + patterened_files[current_file + 1], processed_opcodes[current_file])
		if c == "-":
			if current_file == 0:
				return
			current_file -= 1
			printer.load(sys.argv[1] + "//" + patterened_files[current_file], sys.argv[1] + "//" + patterened_files[current_file + 1], processed_opcodes[current_file])
		#print(repr(c))
		#print(str(c))


files = os.listdir(sys.argv[1])
patterened_files = [x for x in files if x.startswith(sys.argv[2])]
patterened_files.sort(key=natural_keys)
current_file = 0
file_count = len(patterened_files)

opcodetext = [0x0, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x15, 0x15, 0x15, 0x15, 0x15, 0x15, 0x15, 0x15, 0x12, 0x3, 0x3, 0x3, 0x3, 0x3, 0x3, 0x3, 0x5, 0x13, 0x12, 0x4, 0x16, 0x13, 0x12, 0x4, 0x3, 0x16, 0x13, 0x12, 0x4, 0x3, 0x3, 0x5, 0x3, 0xb, 0xb, 0x7, 0x3, 0x15, 0x14, 0x13, 0x12, 0x4, 0x13, 0x12, 0x4, 0x3, 0x13, 0x12, 0x4, 0x3, 0x7, 0x3, 0x5, 0x3, 0xb, 0xb, 0x3, 0x15, 0x3, 0x13, 0x12, 0x4, 0x13, 0x12, 0x4, 0x3, 0x13, 0x12, 0x4, 0x3, 0x1, 0x3, 0x5, 0x3, 0xb, 0xb, 0x3, 0x15, 0x3, 0x13, 0x12, 0x4, 0x13, 0x12, 0x4, 0x3, 0x13, 0x12, 0x4, 0x3, 0x2, 0x3, 0x5, 0x3, 0xb, 0xb, 0x3, 0x15, 0x3, 0x13, 0x12, 0x4, 0x13, 0x12, 0x4, 0x3, 0x13, 0x12, 0x4, 0x3, 0x3, 0x5, 0x3, 0xb, 0xb, 0x3, 0x15, 0x3, 0x13, 0x12, 0x4, 0x13, 0x12, 0x4, 0x3, 0x13, 0x12, 0x4, 0x3, 0x3, 0x5, 0x3, 0xb, 0xb, 0x3, 0x15, 0x3, 0x14, 0x13, 0x12, 0x4, 0x13, 0x12, 0x4, 0x3, 0x13, 0x12, 0x4, 0x3, 0x3, 0x5, 0x3, 0xb, 0xb, 0x3, 0x15, 0x3, 0x13, 0x12, 0x4, 0x13, 0x12, 0x4, 0x3, 0x13, 0x12, 0x4, 0x3, 0x15, 0x3, 0x5, 0x3, 0xb, 0xb, 0x3, 0x15, 0x3, 0x11, 0x5, 0x11]
processed_opcodes = ["Opcode: " + hex(x) for x in opcodetext]

printer = Viewer()
printer.load(sys.argv[1] + "//" + patterened_files[current_file], sys.argv[1] + "//" + patterened_files[current_file + 1], processed_opcodes[current_file])





##############################################################
import sys
import fcntl
import os
import selectors
import termios
# set sys.stdin non-blocking


fd = sys.stdin.fileno()

oldterm = termios.tcgetattr(fd)
newattr = oldterm[:]
newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
termios.tcsetattr(fd, termios.TCSANOW, newattr)

oldflags = fcntl.fcntl(fd, fcntl.F_GETFL)
fcntl.fcntl(fd, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)

mysel = selectors.DefaultSelector()
mysel.register(sys.stdin, selectors.EVENT_READ, processKeyboardKey)
while True:
    #print('waiting for I/O')
    for key, mask in mysel.select():
        callback = key.data
        callback(key.fileobj, mask)
