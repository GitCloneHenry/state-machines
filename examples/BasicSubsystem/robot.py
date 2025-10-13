import wpilib

from simple_state_system import *

from phoenix6.hardware import TalonFX
from phoenix6.configs import TalonFXConfiguration
from phoenix6.controls import MotionMagicVoltage

class SubsystemExample(StateSystem):
    def __init__(self):
        # Initialize the state machine
        super().__init__()

        # Create a motor
        self.test_motor = TalonFX(1)

        # Create a motion magic controller
        self.motion_magic_voltage = MotionMagicVoltage(0).with_slot(0)
        
        # Create and apply simple motor configurations
        test_motor_config = TalonFXConfiguration()

        test_motor_config.slot0.k_p = 0.1

        motion_magic_config = test_motor_config.motion_magic

        motion_magic_config.motion_magic_cruise_velocity = 700
        motion_magic_config.motion_magic_acceleration = 1400
        motion_magic_config.motion_magic_jerk = 2800

        self.test_motor.configurator.apply(test_motor_config)

    @state 
    def idle(self):
        self.test_motor.stopMotor()
        return True

    @state
    def run_to_position(self):
        self.test_motor.set_control(self.motion_magic_voltage.with_position(100))
        return abs(self.test_motor.get_closed_loop_error().value_as_double) < 0.1

class Robot(wpilib.TimedRobot):
    def robotInit(self):
        self.subsystem = SubsystemExample()
        self.controller = wpilib.XboxController(0)
    
    def teleopInit(self):
        self.subsystem.queue_states("run_to_position", "idle")

if __name__ == "__main__":
    wpilib.run(Robot)