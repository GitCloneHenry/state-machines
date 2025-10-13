import wpilib
import time
import threading
import inspect

def state(func):
    func._is_state = True
    return func

class StateSystem:
    _override_warning_shown = set()

    def __init__(self):
        self._states = {} 

        # --- Collect @state methods ---
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if callable(attr) and getattr(attr, "_is_state", False):
                self._states[attr_name] = attr
        
        if not self._states:
            wpilib.reportWarning(f"No states defined for {type(self).__name__}!")

        # --- Detect overridden methods ---
        base_methods = {
            name: func
            for name, func in StateSystem.__dict__.items()
            if callable(func) and not name.startswith("__")
        }

        for name, base_func in base_methods.items():
            # Skip __init__, _run, and private helpers
            if name in ("__init__", "_run"):
                continue

            subclass_func = self.__class__.__dict__.get(name)
            if subclass_func is not None and subclass_func is not base_func:
                # Subclass has overridden a base method
                original = subclass_func

                def make_wrapper(fname, base_f):
                    def wrapper(this, *args, **kwargs):
                        # Reset flag
                        flag_name = f"_super_called_flag_{fname}"
                        setattr(this, flag_name, False)

                        result = original(this, *args, **kwargs)

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

                setattr(self.__class__, name, make_wrapper(name, base_func))

        # --- Thread setup ---
        self._current_state = None
        self._current_state_lock = threading.Lock()
        threading.Thread(target=self._run, daemon=True).start()
    
    def _run(self):
        while True:
            self.periodic()
            time.sleep(0.02)

    def set_state(self, name: str):
        if name not in self._states:
            wpilib.reportError(f"Unknown state '{name}' for {type(self).__name__}")
            return
        with self._current_state_lock:
            self._current_state = name

    def periodic(self):
        self._mark_super_called("periodic")
        with self._current_state_lock:
            state = self._current_state
        if state:
            try:
                self._states[state]()
            except Exception as e:
                wpilib.reportError(f"Error in state '{state}' of {type(self).__name__}: {e}")

    # --- Utility for marking super() calls ---
    def _mark_super_called(self, method_name):
        setattr(self, f"_super_called_flag_{method_name}", True)
