import keyboard
import multiprocessing as mp
import queue
import ctypes

window_keys = ["right shift", "up", "down"]

class AutocompletionCalculator(mp.Process):
    """
    A process which takes input from a get_typed_strings call and returns of 5 recommended autocomplete words
    """
    def __init__(self, shared_queue, exit_code, send_pipe, tree_library_path, word_list_path, get_key_timeout=2):
        super().__init__(daemon=True)
        self.key_events = []
        self.in_queue = shared_queue
        self.send_pipe = send_pipe

        self.key_timeout = get_key_timeout
        self.tree_library_path = tree_library_path
        self.word_list_path = word_list_path
        self.exit_code = exit_code

    def run(self):
        library = ctypes.CDLL(self.tree_library_path)
        library.get_autocomplete.restype = ctypes.c_char_p
        cstring = ctypes.create_string_buffer(b"word_list.txt")
        library.set_tree(cstring)

        while True:
            # Figure out keys pressed
            try:
                key_pressed = self.in_queue.get(block=True, timeout=self.key_timeout) # block-timeout so the loop isn't unnecessarily busy
                if key_pressed == self.exit_code or key_pressed.name == self.exit_code: # Exit
                    self.send_pipe.send(self.exit_code)
                    return True

                # Check if up/down input or shift
                if key_pressed.name in window_keys and key_pressed.event_type != "up": # Have the graphical interface (main thread) respond to these
                    self.send_pipe.send(key_pressed.name)

                if len(key_pressed.name) == 1 or key_pressed.name == "space":
                    self.key_events.append(key_pressed)

            except queue.Empty:
                continue # Avoid creating a new typed string
            
            except:
                pass

            # Figure out and send string typed
            typed_string_gen = keyboard.get_typed_strings(self.key_events)
            typed = ""
            while True:
                try:
                    typed = next(typed_string_gen).split(" ")[-1]

                except StopIteration:
                    # Waits until a StopIteration exception before doing calculations
                    if typed != "":
                        # Calculate 5 best recommended autocompletes
                        autocompletes_bytes = library.get_autocomplete(ctypes.create_string_buffer(bytes(typed, 'utf-8')), 5)
                        autocompletes = autocompletes_bytes.decode("utf-8").split(" ")
                        self.send_pipe.send((autocompletes, typed)) # Make sure recv is constantly being checked
                    break

        self.send_pipe.send(self.exit_code)
        return True

if __name__=="__main__":
    # test caller process

    # Set up tracker
    q = mp.Queue()

    conn1, conn2 = mp.Pipe(False)

    tracker = AutocompletionCalculator(q, 'esc', conn2, "libWordTree.dylib", "word_list.txt")
    tracker.start()

    # Start recording
    keyboard.start_recording(q)
    print("Ready!")
    while True:
        x = conn1.recv()
        if x == "esc":
            break
        #print(x)