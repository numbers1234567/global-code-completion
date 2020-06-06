import tkinter as tk
import keyboard
import multiprocessing as mp
from Autocompletion import *

window_keys = ["right shift", "up", "down"]

def setup_hotkeys(sending_pipe):
    keyboard.add_hotkey("command+[", sending_pipe.send, args=("selection L",))
    keyboard.add_hotkey("command+]", sending_pipe.send, args=("selection R",))
    keyboard.add_hotkey("right shift", sending_pipe.send, args=("autocomplete",))

class OptionsWindow:
    """
    Contains the autocompletion window and some methods for interacting with it
    """
    def __init__(self, in_pipe, update_rate, exit_code, UI_input):
        """
        in_pipe is the sending conn2 of a non-duplex pipe, and update_rate is like FPS, pass 60 for 60 updates per second
        """
        self.window = tk.Tk()
        #self.window.resizable(True)
        self.currently_displaying = []
        self.in_pipe = in_pipe
        self.update_rate = update_rate
        self.exit_code = exit_code
        self.last_typed = ""
        self.selected = 0
        self.UI_input = UI_input

    def text_complete(self, typed, to_type):
        keyboard.write(to_type[len(typed):])

    def update(self):
        """
        Beef of the class, gets input from in_pipe and displays them as labels. Also captures user input
        """
        if self.in_pipe.poll():
            # list option input
            new_updates = self.in_pipe.recv()
            while self.in_pipe.poll():
                new_updates = self.in_pipe.recv()

            if new_updates == "esc": # terminate
                self.window.destroy()
                return

            self.setup_display(new_updates[0])
            self.last_typed = new_updates[1]

            # update display
            for label in self.currently_displaying:
                label["bg"] = "white"

            if len(self.currently_displaying) > 0:
                self.currently_displaying[self.selected % len(self.currently_displaying)]["bg"] = "black"
        
        if self.UI_input.poll():
            # user input
            user_input = self.UI_input.recv()
            while self.UI_input.poll():
                user_input = self.UI_input.recv()
            
            if user_input == "selection L":
                self.selected -= 1
            elif user_input == "selection R":
                self.selected += 1
            elif user_input == "autocomplete":
                self.text_complete(self.last_typed, self.currently_displaying[self.selected % len(self.currently_displaying)]["text"])

            # update display
            for label in self.currently_displaying:
                label["bg"] = "white"

            if len(self.currently_displaying) > 0:
                self.currently_displaying[self.selected % len(self.currently_displaying)]["bg"] = "black"
            
        self.window.after(int(1000/self.update_rate), self.update)

    def start(self):
        """
        Start blocks the thread
        """
        self.update()
        self.window.mainloop() # Update shouldn't block, but this will
    
    def setup_display(self, labels):
        """
        Sets up the n labels for display and removes the last labels being displayed
        """
        #self.selected = 0
        to_display = [""] + labels
        for label in self.currently_displaying:
            label.destroy()
        
        self.currently_displaying = []
        for label in to_display:
            new_label = tk.Label(self.window)
            new_label["text"] = label
            self.currently_displaying.append(new_label)
            new_label.pack()

if __name__=="__main__":
    # Set up tracker
    q = mp.Queue()

    conn1, conn2 = mp.Pipe(False)
    input_out, input_in = mp.Pipe(False)

    setup_hotkeys(input_in)

    tracker = AutocompletionCalculator(q, 'esc', conn2, "libWordTree.dylib", "word_list.txt")

    window = OptionsWindow(conn1, 20, "esc", input_out)
    tracker.start()
    keyboard.start_recording(q)
    
    window.start()
