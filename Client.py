from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.utils import get_color_from_hex
import socket
import threading
from datetime import datetime
import json

class ChatApp(App):
    def __init__(self, username, password, server_address, **kwargs):
        super(ChatApp, self).__init__(**kwargs)
        self.username = username
        self.password = password
        self.server_address = server_address
        self.client_socket = None
        self.is_running = True

    def build(self):
        self.layout = BoxLayout(orientation="vertical", padding=20, spacing=20)

        self.username_label = Label(text=self.username, size_hint_y=0.1, font_size="18sp")
        self.layout.add_widget(self.username_label)

        self.chat_scroll_view = ScrollView(size_hint_y=0.8, do_scroll_x=False)
        self.chat_history = BoxLayout(orientation="vertical", spacing=10, size_hint_y=None)
        self.chat_history.bind(minimum_height=self.chat_history.setter('height'))
        self.chat_scroll_view.add_widget(self.chat_history)
        self.layout.add_widget(self.chat_scroll_view)

        self.input_layout = BoxLayout(orientation="horizontal", size_hint_y=0.1, spacing=10)
        self.message_input = TextInput(multiline=False, hint_text="Type your message...", background_color=get_color_from_hex("#333333"), foreground_color=get_color_from_hex("#FFFFFF"))
        self.send_button = Button(text="Send", size_hint_x=None, width=100, background_color=get_color_from_hex("#0080FF"), color=get_color_from_hex("#FFFFFF"))
        self.send_button.bind(on_press=self.send_message)
        self.input_layout.add_widget(self.message_input)
        self.input_layout.add_widget(self.send_button)
        self.layout.add_widget(self.input_layout)

        try:
            self.connect_to_server()
            self.receive_messages_thread = threading.Thread(target=self.receive_messages)
            self.receive_messages_thread.start()
        except Exception as e:
            self.update_chat_history("Error", f"Failed to connect to the server: {str(e)}")

        return self.layout

    def connect_to_server(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect(self.server_address)
        self.client_socket.send(json.dumps({"username": self.username, "password": self.password}).encode("utf-8"))

    def receive_messages(self):
        while self.is_running:
            try:
                message = self.client_socket.recv(1024).decode("utf-8")
                if message.startswith("MESSAGEBROADCAST"):
                    data = json.loads(message.split(" ", 1)[1])
                    Clock.schedule_once(lambda dt: self.update_chat_history(data["username"], data["message"]), 0)
                elif message.startswith("SERVERMESSAGE"):
                    data = json.loads(message.split(" ", 1)[1])
                    Clock.schedule_once(lambda dt: self.update_chat_history("Server", data["message"]), 0)
            except Exception as e:
                if self.is_running:
                    self.update_chat_history("Error", f"An error occurred while receiving messages: {str(e)}")
                    break

    def send_message(self, instance):
        message = self.message_input.text
        if message:
            try:
                timestamp = datetime.now().strftime("%H:%M:%S")
                self.client_socket.send(message.encode("utf-8"))
                self.update_chat_history("Me", message)
                self.message_input.text = ""
            except Exception as e:
                self.update_chat_history("Error", f"An error occurred while sending message: {str(e)}")

    def update_chat_history(self, username, message):
        if username == "Server":
            message_label = Label(text=f"[color=#FFFFFF][b]{username}[/b]: {message}[/color]", markup=True, size_hint_y=None, height=40, halign="left")
        elif username == "Me":
            message_label = Label(text=f"[b][color=#0080FF]{username}[/color][/b] {datetime.now().strftime('%H:%M:%S')}: {message}", markup=True, size_hint_y=None, height=40, halign="right")
        else:
            message_label = Label(text=f"[color=#FFFFFF][b]{username}[/b]: {message}[/color]", markup=True, size_hint_y=None, height=40, halign="left")
        message_label.bind(texture_size=message_label.setter('size'))
        self.chat_history.add_widget(message_label)
        self.chat_scroll_view.scroll_to(message_label, padding=10)

    def on_stop(self):
        self.is_running = False
        if self.client_socket:
            self.client_socket.close()
        if self.receive_messages_thread.is_alive():
            self.receive_messages_thread.join()

if __name__ == "__main__":
    username = input("Enter your username: ")
    password = input("Enter your password: ")
    server_address = ("localhost", 9049)
    ChatApp(username=username, password=password, server_address=server_address).run()