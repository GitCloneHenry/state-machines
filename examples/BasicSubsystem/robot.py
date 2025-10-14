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
        self.test_motor = TalonFX(2)

        # Create a motion magic controller
        self.motion_magic_voltage = MotionMagicVoltage(0).with_slot(0)
        
        # Create and apply simple motor configurations
        test_motor_config = TalonFXConfiguration()

        test_motor_config.slot0.k_p = 0.45
        test_motor_config.slot0.k_i = 0.001
        test_motor_config.slot0.k_d = 0.0

        motion_magic_config = test_motor_config.motion_magic

        motion_magic_config.motion_magic_cruise_velocity = 700
        motion_magic_config.motion_magic_acceleration = 1400
        motion_magic_config.motion_magic_jerk = 2800

        self.test_motor.configurator.apply(test_motor_config)

        # Used for timers
        self.start_time = None

    @state 
    def run_for_duration(self, duration=1.0):
        if self.start_time is None:
            self.start_time = wpilib.Timer.getFPGATimestamp()
        if wpilib.Timer.getFPGATimestamp() - self.start_time < duration:
            self.test_motor.set(0.5)
            return False
        self.start_time = None
        self.test_motor.stopMotor() 
        return True

    @state
    def run_to_position(self, position=100.0):
        self.test_motor.set_control(self.motion_magic_voltage.with_position(position))
        wpilib.SmartDashboard.putNumber("Error", abs(abs(position) - abs(self.test_motor.get_position().value_as_double)))
        return abs(abs(position) - abs(self.test_motor.get_position().value_as_double)) < 0.5

    @state 
    def manual_control(self, controller: wpilib.XboxController): 
        self.test_motor.set(controller.getLeftX())
        return False

    def periodic(self):
        super().periodic()
        wpilib.SmartDashboard.putNumber("Position", self.test_motor.get_position().value_as_double)

class Robot(wpilib.TimedRobot):
    def robotInit(self):
        self.subsystem = SubsystemExample()
        self.controller = wpilib.XboxController(0)
    
    def teleopInit(self):
        self.subsystem.queue_states(
            # ("run_for_duration", {"duration": 5.0}),
            # ("run_to_position", {"position": 0.0}),
            ("manual_control", (self.controller))
        )

    def teleopPeriodic(self):
        if self.controller.getAButtonPressed():
            self.subsystem.queue_state(
                ("run_to_position", {"position": 100.0}),
                0
            )
        if self.controller.getBButtonPressed():
            self.subsystem.queue_state(
                ("run_to_position", {"position": 0.0}),
                0
            )
        

if __name__ == "__main__":
    wpilib.run(Robot)