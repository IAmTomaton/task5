import base64
import socket
import ssl
import random
import string


host_addr = 'smtp.mail.ru'
port = 465


class Mail:
	def __init__(self):
		self.user_mail = ''
		self.to = []
		self.password = ''
		self.last_command = ''
		self.text_path = ''
		self.attachments = []
		self.subject = ''

	def parse_config(self, path):
		with open(path, encoding='utf-8') as file:
			for line in file.readlines():
				command = line.split(' ')
				command[-1] = command[-1][0:-1]
				if len(command) == 1: self.one_command(command)
				if len(command) == 2: self.two_command(command)
					
	def one_command(self, command):
		self.two_command([self.last_command] + command)
		
	def two_command(self, command):
		self.last_command = command[0]
		if command[0] == 'from':
			self.user_mail = command[1]
		elif command[0] == 'to':
			self.to.append(command[1])
		elif command[0] == 'password':
			self.password = command[1]
		elif command[0] == 'text':
			self.text_path = command[1]
		elif command[0] == 'attach':
			self.attachments.append(command[1])
		elif command[0] == 'subject':
			self.subject = command[1]
		else:
			raise Exception('Unknown command: ' + command[0])

	def create_msg(self):
		boundary = random_boundary()
		text = screen_msg(read_msg(self.text_path))
		msg = ''
		msg += 'To: mrhomka.com@gmail.com\n'
		if self.subject: msg += 'Subject: ' + self.subject + '\n'
		msg += 'MME-Version: 1.0' + '\n'
		msg += 'Content-Type: multipart/mixed; boundary="' + boundary + '"' + '\n'
		msg += '\n'
		msg += '--' + boundary + '\n'
		msg += 'Content-Transfer-Encoding: 7bit' + '\n'
		msg += 'Content-Type: text/plain' + '\n' + '\n'
		msg += text + '\n'
		for attach in self.attachments:
			msg += '--' + boundary + '\n'
			data = read_file(attach)
			name = attach.split('/')[-1]
			msg += 'Content-Disposition: attachment; filename="' + name +'"' + '\n'
			msg += 'Content-Transfer-Encoding: base64\n'
			msg += 'Content-Type: text/txt; name="' + name + '"' + '\n' + '\n'
			msg += data + '\n'
		msg += '--' + boundary + '--' + '\n'
		msg += '.' + '\n'
		return msg

	def send(self):
		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
			client.connect((host_addr, port))
			client = ssl.wrap_socket(client)
			client.recv(1024)
			user_name = self.user_mail.split('@')[0]
			request(client, 'EHLO ' + user_name)
			base64login = base(user_name)
			base64password = base(self.password)
			request(client, 'AUTH LOGIN')
			request(client, base64login)
			request(client, base64password)
			request(client, 'MAIL FROM:' + self.user_mail)
			for to in self.to:
				request(client, 'RCPT TO:' + to)
			request(client, 'DATA')
			request(client, self.create_msg())


def log(recv):
	if int(recv[:3]) >= 500:
		print(recv)


def request(socket, request, print_log=True):
	socket.send((request + '\n').encode())
	recv = socket.recv(65535).decode()
	if print_log: log(recv)
	return recv


def screen_msg(msg):
	start = -1
	stop = -1
	i = 0
	while i < len(msg):
		if msg[i] == '.' and start == -1:
			start = i
		if start != -1 and msg[i] != '.':
			stop = i - 1;
		if stop != -1:
			prestart = start == 0 or msg[start - 1] == '\n'
			poststop = stop == len(msg) - 1 or msg[stop + 1] == '\n'
			if prestart and poststop:
				msg = msg[:start] + '.' + msg[start:]
			start = -1
			stop = -1
		i += 1
	return msg


def base(line):
	return base64.b64encode(line.encode()).decode()


def random_boundary(length=10):
	return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))
	

def read_msg(path):
	with open(path, encoding='utf-8') as file:
		return file.read()

	
def read_file(path):
	with open(path, 'rb') as file:
		return base64.b64encode(file.read()).decode()
	
	
if __name__ == '__main__':
	mail = Mail()
	mail.parse_config('config.cnf')
	mail.send()
