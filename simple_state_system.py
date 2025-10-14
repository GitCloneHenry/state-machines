import wpilib
import time
import threading

def state(func):
    func._is_state = True
    return func


class StateSystem:
    _override_warning_shown = set()

    def __init__(self):
        self._states = {}
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if callable(attr) and getattr(attr, "_is_state", False):
                self._states[attr_name] = attr

        if not self._states:
            wpilib.reportWarning(f"No states defined for {type(self).__name__}!")

        base_methods = {
            name: func
            for name, func in StateSystem.__dict__.items()
            if callable(func) and not name.startswith("__")
        }

        for name, base_func in base_methods.items():
            if name in ("__init__", "_run"):
                continue

            subclass_func = self.__class__.__dict__.get(name)
            if subclass_func is not None and subclass_func is not base_func:
                def make_wrapper(fname, base_f, subclass_f):
                    def wrapper(this, *args, **kwargs):
                        flag_name = f"_super_called_flag_{fname}"
                        setattr(this, flag_name, False)

                        result = subclass_f(this, *args, **kwargs)

                        if (
                            not getattr(this, flag_name)
                            and (type(this), fname)
                            not in StateSystem._override_warning_shown
                        ):
                            wpilib.reportWarning(
                                f"{type(this).__name__}.{fname}() overrides base but never calls super().{fname}()"
                            )
                            StateSystem._override_warning_shown.add(
                                (type(this), fname)
                            )

                        return result

                    return wrapper

                setattr(
                    self.__class__,
                    name,
                    make_wrapper(name, base_func, subclass_func),
                )

        self._current_state = None
        self._current_state_lock = threading.Lock()
        self._queue = []

        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        while True:
            if self._current_state:
                self.periodic()
            time.sleep(0.02)

    def periodic(self):
        self._mark_super_called("periodic")
        with self._current_state_lock:
            current = self._current_state
            queue = self._queue

        if current:
            name, args, kwargs = current
            try:
                done: bool = self._states[name](*args, **kwargs)
                if done and queue:
                    with self._current_state_lock:
                        queue.pop(0)
                        self._current_state = queue[0] if queue else None
            except Exception as e:
                wpilib.reportError(f"Error in state '{name}' of {type(self).__name__}: {e}")

    def queue_states(self, *states):
        with self._current_state_lock:
            for s in states:
                if isinstance(s, str):
                    name, args, kwargs = s, (), {}
                elif isinstance(s, tuple):
                    name = s[0]
                    if len(s) == 2 and not isinstance(s[1], dict):
                        args, kwargs = (s[1],), {}
                    elif len(s) == 2 and isinstance(s[1], dict):
                        args, kwargs = (), s[1]
                    elif len(s) == 3:
                        args, kwargs = s[1], s[2]
                    else:
                        args, kwargs = (), {}
                else:
                    wpilib.reportError(f"Invalid state format: {s}")
                    continue

                if name not in self._states:
                    wpilib.reportError(f"Unknown state '{name}' for {type(self).__name__}")
                    continue

                self._queue.append((name, args, kwargs))

            if not self._current_state and self._queue:
                self._current_state = self._queue[0]

    def clear_queue(self):
        with self._current_state_lock:
            self._queue.clear()
            self._current_state = None

    def _mark_super_called(self, method_name):
        setattr(self, f"_super_called_flag_{method_name}", True)
